"""APScheduler setup: periodically scans for overdue grievances and fires notifications."""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger(__name__)
scheduler = BackgroundScheduler(daemon=True)


def check_overdue_job(app):
    """Find grievances past expected_resolution_time that are still open and notify."""
    with app.app_context():
        from .models import db, Grievance
        from .notifications.service import notify_overdue
        now = datetime.utcnow()
        overdue = Grievance.query.filter(
            Grievance.expected_resolution_time.isnot(None),
            Grievance.expected_resolution_time < now,
            Grievance.status.notin_(['Resolved', 'Rejected'])
        ).all()
        for g in overdue:
            try:
                notify_overdue(g)
            except Exception as exc:
                log.error("Notification failed for %s: %s", g.grievance_id, exc)


def start_scheduler(app):
    if scheduler.running:
        return
    scheduler.add_job(
        check_overdue_job,
        trigger=IntervalTrigger(minutes=15),
        args=[app],
        id='overdue_check',
        replace_existing=True,
        misfire_grace_time=60
    )
    scheduler.start()
    log.info("APScheduler started: overdue grievance check every 15 minutes.")
