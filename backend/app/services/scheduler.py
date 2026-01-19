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

            # Update to expiring_soon
            expiring_soon = db.query(Requirement).filter(
                Requirement.due_date <= soon_threshold,
                Requirement.due_date > today,
                Requirement.status == RequirementStatus.COMPLIANT.value,
            ).all()

            for req in expiring_soon:
                req.status = RequirementStatus.EXPIRING_SOON.value

            # Update to expired
            expired = db.query(Requirement).filter(
                Requirement.due_date < today,
                Requirement.status.in_([
                    RequirementStatus.COMPLIANT.value,
                    RequirementStatus.EXPIRING_SOON.value,
                    RequirementStatus.PENDING.value,
                ]),
            ).all()

            for req in expired:
                req.status = RequirementStatus.EXPIRED.value

            db.commit()

            if expiring_soon or expired:
                print(
                    f"[{datetime.now()}] Status updates: "
                    f"{len(expiring_soon)} expiring soon, {len(expired)} expired"
                )

        except Exception as e:
            print(f"[{datetime.now()}] Error updating statuses: {e}")
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
