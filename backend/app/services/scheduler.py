"""Background task scheduler for notifications and maintenance."""
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config.database import SessionLocal
from app.services.notification_service import NotificationService


class TaskScheduler:
    """Manages scheduled background tasks."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self._is_running = False

    def start(self):
        """Start the scheduler."""
        if self._is_running:
            return

        # Schedule daily notification generation (6 AM)
        self.scheduler.add_job(
            self._generate_notifications,
            CronTrigger(hour=6, minute=0),
            id="generate_notifications",
            replace_existing=True,
        )

        # Schedule notification processing every 5 minutes
        self.scheduler.add_job(
            self._process_notifications,
            CronTrigger(minute="*/5"),
            id="process_notifications",
            replace_existing=True,
        )

        # Schedule status updates hourly
        self.scheduler.add_job(
            self._update_requirement_statuses,
            CronTrigger(minute=0),
            id="update_statuses",
            replace_existing=True,
        )

        # Schedule CRM compliance sync hourly (at :30)
        self.scheduler.add_job(
            self._sync_crm_compliance,
            CronTrigger(minute=30),
            id="sync_crm_compliance",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        print(f"[{datetime.now()}] Task scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            print(f"[{datetime.now()}] Task scheduler stopped")

    def run_now(self, task_name: str):
        """Run a scheduled task immediately."""
        tasks = {
            "generate_notifications": self._generate_notifications,
            "process_notifications": self._process_notifications,
            "update_statuses": self._update_requirement_statuses,
            "sync_crm_compliance": self._sync_crm_compliance,
        }
        task = tasks.get(task_name)
        if task:
            task()
        else:
            raise ValueError(f"Unknown task: {task_name}")

    def _generate_notifications(self):
        """Generate expiration and overdue notifications."""
        print(f"[{datetime.now()}] Generating notifications...")

        db = SessionLocal()
        try:
            service = NotificationService(db)

            # Generate expiration notifications
            expiring_count = service.generate_expiration_notifications()
            print(f"  Created {expiring_count} expiration notifications")

            # Generate overdue notifications
            overdue_count = service.generate_overdue_notifications()
            print(f"  Created {overdue_count} overdue notifications")

        except Exception as e:
            print(f"  Error generating notifications: {e}")
        finally:
            db.close()

    def _process_notifications(self):
        """Process and send pending notifications."""
        db = SessionLocal()
        try:
            service = NotificationService(db)
            results = service.process_pending_notifications()

            if results["sent"] > 0 or results["failed"] > 0:
                print(
                    f"[{datetime.now()}] Processed notifications: "
                    f"{results['sent']} sent, {results['failed']} failed"
                )

        except Exception as e:
            print(f"[{datetime.now()}] Error processing notifications: {e}")
        finally:
            db.close()

    def _update_requirement_statuses(self):
        """Update requirement statuses based on due dates."""
        from datetime import date, timedelta
        from app.models.requirement import Requirement, RequirementStatus

        db = SessionLocal()
        try:
            today = date.today()
            soon_threshold = today + timedelta(days=30)

            # Update to due_soon
            due_soon = db.query(Requirement).filter(
                Requirement.due_date <= soon_threshold,
                Requirement.due_date > today,
                Requirement.status == RequirementStatus.CURRENT.value,
            ).all()

            for req in due_soon:
                req.status = RequirementStatus.DUE_SOON.value

            # Update to expired
            expired = db.query(Requirement).filter(
                Requirement.due_date < today,
                Requirement.status.in_([
                    RequirementStatus.CURRENT.value,
                    RequirementStatus.DUE_SOON.value,
                    RequirementStatus.PENDING.value,
                ]),
            ).all()

            for req in expired:
                req.status = RequirementStatus.EXPIRED.value

            db.commit()

            if due_soon or expired:
                print(
                    f"[{datetime.now()}] Status updates: "
                    f"{len(due_soon)} due soon, {len(expired)} expired"
                )

        except Exception as e:
            print(f"[{datetime.now()}] Error updating statuses: {e}")
            db.rollback()
        finally:
            db.close()

    def _sync_crm_compliance(self):
        """Push compliance status updates to CRM for all accounts with sync enabled."""
        from app.models.account import Account
        from app.models.entity import Entity
        from app.models.crm_sync import CRMSyncLog, SyncDirection, SyncOperation, SyncStatus
        from app.services.crm import get_crm_service
        import time

        db = SessionLocal()
        try:
            # Get accounts with CRM sync enabled
            accounts = db.query(Account).filter(Account.is_active == True).all()

            total_synced = 0
            total_failed = 0

            for account in accounts:
                crm_service = get_crm_service(account)

                # Skip if CRM not configured
                if not crm_service.is_configured():
                    continue

                # Get entities with external_id (already synced to CRM)
                entities = db.query(Entity).filter(
                    Entity.account_id == account.id,
                    Entity.external_id.isnot(None),
                ).all()

                for entity in entities:
                    start_time = time.time()
                    result = crm_service.push_entity_compliance(entity)
                    duration_ms = int((time.time() - start_time) * 1000)

                    if result.get("success"):
                        total_synced += 1
                    else:
                        total_failed += 1

                    # Log the sync
                    log = CRMSyncLog(
                        account_id=account.id,
                        entity_id=entity.id,
                        direction=SyncDirection.PUSH.value,
                        operation=SyncOperation.COMPLIANCE_PUSH.value,
                        provider=crm_service.provider,
                        request_data=crm_service._calculate_compliance_status(entity),
                        response_data=result,
                        status=SyncStatus.SUCCESS.value if result.get("success") else SyncStatus.FAILED.value,
                        error_message=result.get("error") if not result.get("success") else None,
                        external_id=entity.external_id,
                        duration_ms=duration_ms,
                    )
                    db.add(log)

                # Update last sync timestamp
                if entities:
                    crm_config = account.settings.get("crm", {})
                    crm_config["last_sync_at"] = datetime.now().isoformat()
                    crm_config["last_sync_status"] = "success" if total_failed == 0 else "partial"
                    account.settings["crm"] = crm_config

            db.commit()

            if total_synced > 0 or total_failed > 0:
                print(
                    f"[{datetime.now()}] CRM compliance sync: "
                    f"{total_synced} synced, {total_failed} failed"
                )

        except Exception as e:
            print(f"[{datetime.now()}] Error in CRM compliance sync: {e}")
            db.rollback()
        finally:
            db.close()


# Global scheduler instance
_scheduler: TaskScheduler = None


def get_scheduler() -> TaskScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
