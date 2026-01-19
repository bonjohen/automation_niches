"""Notification service - schedules and sends notifications."""
from datetime import datetime, date, timedelta
from typing import Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.config.settings import get_settings
from app.config.yaml_loader import get_niche_loader
from app.models.notification import Notification, NotificationStatus, NotificationType, NotificationChannel
from app.models.requirement import Requirement, RequirementType, RequirementStatus
from app.models.entity import Entity
from app.models.user import User
from app.models.account import Account
from app.services.email_service import get_email_service

settings = get_settings()


class NotificationService:
    """Service for creating and sending notifications."""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = get_email_service()
        self.loader = get_niche_loader()

    def generate_expiration_notifications(self) -> int:
        """
        Generate notifications for expiring requirements.

        This should be called daily by a scheduler (cron job or Celery beat).

        Returns the number of notifications created.
        """
        today = date.today()
        notifications_created = 0

        # Get all active accounts
        accounts = self.db.query(Account).filter(Account.is_active == True).all()

        for account in accounts:
            # Get requirement types with notification rules
            req_types = self.db.query(RequirementType).filter(
                RequirementType.niche_id == account.niche_id
            ).all()

            for req_type in req_types:
                days_before = req_type.notification_rules.get("days_before", [])

                for days in days_before:
                    target_date = today + timedelta(days=days)

                    # Find requirements expiring on target date
                    requirements = self.db.query(Requirement).filter(
                        Requirement.account_id == account.id,
                        Requirement.requirement_type_id == req_type.id,
                        Requirement.due_date == target_date,
                        Requirement.status.in_([
                            RequirementStatus.COMPLIANT.value,
                            RequirementStatus.PENDING.value,
                            RequirementStatus.EXPIRING_SOON.value,
                        ]),
                    ).all()

                    for requirement in requirements:
                        created = self._create_expiration_notification(
                            requirement, req_type, days, account
                        )
                        if created:
                            notifications_created += 1

        self.db.commit()
        return notifications_created

    def generate_overdue_notifications(self) -> int:
        """Generate notifications for overdue requirements."""
        today = date.today()
        notifications_created = 0

        # Find all overdue requirements
        overdue_requirements = self.db.query(Requirement).filter(
            Requirement.due_date < today,
            Requirement.status.notin_([
                RequirementStatus.COMPLIANT.value,
                RequirementStatus.WAIVED.value,
            ]),
        ).all()

        for requirement in overdue_requirements:
            # Update status to expired
            if requirement.status != RequirementStatus.EXPIRED.value:
                requirement.status = RequirementStatus.EXPIRED.value

            # Check if we should send overdue notification
            days_overdue = (today - requirement.due_date).days

            # Send on day 1, 3, 7, and weekly thereafter
            if days_overdue in [1, 3, 7] or (days_overdue > 7 and days_overdue % 7 == 0):
                created = self._create_overdue_notification(requirement, days_overdue)
                if created:
                    notifications_created += 1

        self.db.commit()
        return notifications_created

    def process_pending_notifications(self) -> dict:
        """
        Process and send pending notifications.

        Returns dict with counts of sent, failed notifications.
        """
        now = datetime.utcnow()
        results = {"sent": 0, "failed": 0}

        # Get notifications that are ready to send
        pending = self.db.query(Notification).filter(
            Notification.status == NotificationStatus.PENDING.value,
            Notification.scheduled_at <= now,
        ).limit(100).all()  # Process in batches

        for notification in pending:
            success = self._send_notification(notification)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

        self.db.commit()
        return results

    def _create_expiration_notification(
        self,
        requirement: Requirement,
        req_type: RequirementType,
        days_until_expiration: int,
        account: Account,
    ) -> bool:
        """Create an expiration notification. Returns True if created."""
        # Get entity for context
        entity = self.db.query(Entity).filter(Entity.id == requirement.entity_id).first()
        if not entity:
            return False

        # Get users to notify (for now, notify all users in account)
        users = self.db.query(User).filter(
            User.account_id == account.id,
            User.is_active == True,
        ).all()

        if not users:
            return False

        # Check if notification already exists for this requirement/day
        existing = self.db.query(Notification).filter(
            Notification.requirement_id == requirement.id,
            Notification.notification_type == NotificationType.EXPIRING.value,
            Notification.context_data["days_before"].astext == str(days_until_expiration),
        ).first()

        if existing:
            return False

        # Get notification template
        template = self._get_notification_template(
            account.niche_id,
            NotificationType.EXPIRING.value,
            days_until_expiration,
        )

        # Create notification for each user
        for user in users:
            context = self._build_context(requirement, entity, user, account, days_until_expiration)

            notification = Notification(
                account_id=account.id,
                requirement_id=requirement.id,
                recipient_id=user.id,
                notification_type=NotificationType.EXPIRING.value,
                channel=NotificationChannel.EMAIL.value,
                subject=template["subject"] if template else f"COI Expiring in {days_until_expiration} days - {entity.name}",
                body=template["body"] if template else self._default_expiration_body(context),
                scheduled_at=datetime.utcnow(),  # Send immediately
                status=NotificationStatus.PENDING.value,
                context_data={
                    "days_before": days_until_expiration,
                    **context,
                },
            )
            self.db.add(notification)

        return True

    def _create_overdue_notification(
        self, requirement: Requirement, days_overdue: int
    ) -> bool:
        """Create an overdue notification."""
        entity = self.db.query(Entity).filter(Entity.id == requirement.entity_id).first()
        if not entity:
            return False

        account = self.db.query(Account).filter(Account.id == requirement.account_id).first()
        if not account:
            return False

        users = self.db.query(User).filter(
            User.account_id == account.id,
            User.is_active == True,
        ).all()

        for user in users:
            context = self._build_context(requirement, entity, user, account, -days_overdue)

            notification = Notification(
                account_id=account.id,
                requirement_id=requirement.id,
                recipient_id=user.id,
                notification_type=NotificationType.OVERDUE.value,
                channel=NotificationChannel.EMAIL.value,
                subject=f"EXPIRED: COI for {entity.name} is {days_overdue} days overdue",
                body=self._default_overdue_body(context, days_overdue),
                scheduled_at=datetime.utcnow(),
                status=NotificationStatus.PENDING.value,
                context_data={
                    "days_overdue": days_overdue,
                    **context,
                },
            )
            self.db.add(notification)

        return True

    def _send_notification(self, notification: Notification) -> bool:
        """Send a notification via its channel."""
        notification.delivery_attempts += 1

        if notification.channel == NotificationChannel.EMAIL.value:
            # Get recipient email
            user = self.db.query(User).filter(User.id == notification.recipient_id).first()
            if not user:
                notification.status = NotificationStatus.FAILED.value
                notification.last_error = "Recipient user not found"
                return False

            # Render templates with context
            from jinja2 import Template
            try:
                context = notification.context_data or {}
                subject = Template(notification.subject).render(**context)
                body = Template(notification.body).render(**context)
            except Exception as e:
                subject = notification.subject
                body = notification.body

            # Send email
            from app.services.email_service import EmailMessage
            message = EmailMessage(
                to_email=user.email,
                subject=subject,
                html_body=body,
            )
            result = self.email_service.send(message)

            if result.get("success"):
                notification.status = NotificationStatus.SENT.value
                notification.sent_at = datetime.utcnow()
                notification.external_id = result.get("external_id")
                return True
            else:
                notification.last_error = result.get("error", "Unknown error")
                if notification.delivery_attempts >= 3:
                    notification.status = NotificationStatus.FAILED.value
                return False

        # Unsupported channel
        notification.status = NotificationStatus.FAILED.value
        notification.last_error = f"Unsupported channel: {notification.channel}"
        return False

    def _get_notification_template(
        self, niche_id: str, notification_type: str, days: int
    ) -> Optional[dict]:
        """Get notification template from YAML config."""
        config = self.loader.get_config(niche_id)
        if not config:
            return None

        # Find matching template
        for template in config.notification_templates:
            if template.notification_type == notification_type:
                # Check if template matches the days parameter
                if "30" in template.code and days == 30:
                    return {"subject": template.subject, "body": template.body}
                elif "7" in template.code and days == 7:
                    return {"subject": template.subject, "body": template.body}
                elif notification_type == "expiring" and template.notification_type == "expiring":
                    return {"subject": template.subject, "body": template.body}

        return None

    def _build_context(
        self,
        requirement: Requirement,
        entity: Entity,
        user: User,
        account: Account,
        days: int,
    ) -> dict:
        """Build template context for notifications."""
        return {
            "user": {
                "first_name": user.first_name or user.email.split("@")[0],
                "email": user.email,
            },
            "entity": {
                "name": entity.name,
                "email": entity.email,
                "phone": entity.phone,
            },
            "requirement": {
                "id": str(requirement.id),
                "name": requirement.name,
                "due_date": requirement.due_date.isoformat() if requirement.due_date else None,
                "status": requirement.status,
            },
            "account": {
                "name": account.name,
            },
            "days_until_due": days if days > 0 else 0,
            "days_overdue": abs(days) if days < 0 else 0,
            "app_url": "http://localhost:3000",  # TODO: Configure from settings
        }

    def _default_expiration_body(self, context: dict) -> str:
        """Default email body for expiration notifications."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hello {context['user']['first_name']},</p>

            <p>The Certificate of Insurance for <strong>{context['entity']['name']}</strong>
            is expiring on <strong>{context['requirement']['due_date']}</strong>.</p>

            <p>Please request an updated COI from the vendor to maintain compliance.</p>

            <p><a href="{context['app_url']}/requirements/{context['requirement']['id']}"
                  style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View Requirement
            </a></p>

            <p>Thank you,<br>
            {context['account']['name']} Compliance Team</p>
        </body>
        </html>
        """

    def _default_overdue_body(self, context: dict, days_overdue: int) -> str:
        """Default email body for overdue notifications."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hello {context['user']['first_name']},</p>

            <p><strong style="color: #dc3545;">ALERT:</strong> The Certificate of Insurance for
            <strong>{context['entity']['name']}</strong> has been <strong>EXPIRED</strong>
            for {days_overdue} days.</p>

            <p>This vendor is currently operating without valid insurance coverage on file.
            Please take immediate action.</p>

            <p><a href="{context['app_url']}/requirements/{context['requirement']['id']}"
                  style="background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Resolve Now
            </a></p>

            <p>Thank you,<br>
            {context['account']['name']} Compliance Team</p>
        </body>
        </html>
        """


def get_notification_service(db: Session) -> NotificationService:
    """Get a notification service instance."""
    return NotificationService(db)
