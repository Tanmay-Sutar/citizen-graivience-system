"""Notification service: sends Email (SMTP) and SMS (Twilio abstraction).
MOCK MODE: when credentials are not configured, logs to DB + console instead of real dispatch.
All messages persisted in NotificationLog."""
import smtplib
import logging
from email.message import EmailMessage
from datetime import datetime
from flask import current_app

from ..models import db, NotificationLog, User, Grievance

log = logging.getLogger(__name__)


def is_smtp_configured(cfg):
    return bool(cfg.get("SMTP_USERNAME") and cfg.get("SMTP_PASSWORD") and cfg.get("SMTP_SERVER"))


def is_sms_configured(cfg):
    return cfg.get("SMS_PROVIDER", "mock") != "mock" and bool(cfg.get("TWILIO_ACCOUNT_SID") and cfg.get("TWILIO_AUTH_TOKEN"))


def _log(recipient_type, recipient_id, recipient_email, recipient_mobile,
         channel, subject, message, grievance_id, status, mock_mode, error=None):
    entry = NotificationLog(
        recipient_type=recipient_type, recipient_id=recipient_id,
        recipient_email=recipient_email, recipient_mobile=recipient_mobile,
        channel=channel, subject=subject, message=message, grievance_id=grievance_id,
        status=status, mock_mode=mock_mode, error_message=error
    )
    db.session.add(entry)
    db.session.commit()
    mode = "MOCK " if mock_mode else ""
    print(f"[{mode}{channel.upper()}] To: {recipient_email or recipient_mobile} | Subject: {subject or '-'} | {message[:80]}")


def send_email(to_email, subject, message_body, grievance_id=None, recipient_id=None, recipient_type="user"):
    cfg = current_app.config
    mock = not is_smtp_configured(cfg)
    if not mock:
        try:
            msg = EmailMessage()
            msg.set_content(message_body)
            msg["Subject"] = subject
            msg["From"] = cfg["SMTP_FROM_EMAIL"] or cfg["SMTP_USERNAME"]
            msg["To"] = to_email
            with smtplib.SMTP(cfg["SMTP_SERVER"], cfg["SMTP_PORT"], timeout=15) as srv:
                srv.starttls()
                srv.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
                srv.send_message(msg)
            _log(recipient_type, recipient_id, to_email, None, "email", subject, message_body, grievance_id, "sent", False)
            return True
        except Exception as exc:
            _log(recipient_type, recipient_id, to_email, None, "email", subject, message_body, grievance_id, "failed", False, str(exc))
            return False
    else:
        _log(recipient_type, recipient_id, to_email, None, "email", subject, message_body, grievance_id, "sent", True)
        return True


def send_sms(to_mobile, message_body, grievance_id=None, recipient_id=None, recipient_type="user"):
    cfg = current_app.config
    mock = not is_sms_configured(cfg)
    if not mock:
        try:
            from twilio.rest import Client
            client = Client(cfg["TWILIO_ACCOUNT_SID"], cfg["TWILIO_AUTH_TOKEN"])
            client.messages.create(body=message_body[:1600], from_=cfg["TWILIO_PHONE_NUMBER"], to=to_mobile)
            _log(recipient_type, recipient_id, None, to_mobile, "sms", None, message_body, grievance_id, "sent", False)
            return True
        except Exception as exc:
            _log(recipient_type, recipient_id, None, to_mobile, "sms", None, message_body, grievance_id, "failed", False, str(exc))
            return False
    else:
        _log(recipient_type, recipient_id, None, to_mobile, "sms", None, message_body, grievance_id, "sent", True)
        return True


def notify_user(user: User, subject: str, message: str, grievance_id=None):
    if user.email:
        send_email(user.email, subject, message, grievance_id=grievance_id, recipient_id=user.id, recipient_type=user.role)
    if user.mobile:
        send_sms(user.mobile, f"[{subject}] {message[:500]}", grievance_id=grievance_id, recipient_id=user.id, recipient_type=user.role)


def notify_assignment(g: Grievance):
    """Notify assigned officer, co-officer (dept), and main authority."""
    if not g: return
    dept = g.department
    msg_off = f"New {g.final_category or g.ml_category} grievance {g.grievance_id} assigned to you. Priority: {g.final_priority}. {g.complaint_text[:80]}"
    sub_off = f"New grievance assigned: {g.grievance_id}"
    if g.assigned_officer:
        notify_user(g.assigned_officer, sub_off, msg_off, grievance_id=g.id)

    if dept:
        co_officers = User.query.filter_by(role="co_officer", department_id=dept.id).all()
        for co in co_officers:
            notify_user(co, f"Dept {dept.name}: Grievance {g.grievance_id}",
                        f"Grievance {g.grievance_id} assigned in your dept. Priority {g.final_priority}.",
                        grievance_id=g.id)

    admins = User.query.filter_by(role="main_authority").all()
    for a in admins:
        notify_user(a, f"System alert: {g.grievance_id}",
                    f"Grievance {g.grievance_id} ({g.final_category}/{g.final_priority}) assigned.",
                    grievance_id=g.id)


def notify_high_priority(g: Grievance):
    if g.final_priority != "High":
        return
    admins = User.query.filter_by(role="main_authority").all()
    for a in admins:
        notify_user(a, f"HIGH PRIORITY grievance: {g.grievance_id}",
                    f"High-priority grievance {g.grievance_id} requires attention. {g.complaint_text[:100]}",
                    grievance_id=g.id)


def notify_status_change(g: Grievance, old_status: str, new_status: str, updater: User):
    if not g.citizen_id: return
    citizen = db.session.get(User, g.citizen_id)
    if citizen:
        notify_user(citizen, f"Update: {g.grievance_id}",
                    f"Your grievance status changed: {old_status} -> {new_status}. Last note: check the portal.",
                    grievance_id=g.id)


def notify_overdue(g: Grievance):
    """Called by scheduler when SLA exceeded."""
    if g.assigned_officer:
        notify_user(g.assigned_officer, f"OVERDUE grievance: {g.grievance_id}",
                    f"Grievance {g.grievance_id} has exceeded expected resolution time. Please act.",
                    grievance_id=g.id)
    if g.department_id:
        co_officers = User.query.filter_by(role="co_officer", department_id=g.department_id).all()
        for co in co_officers:
            notify_user(co, f"Overdue in your dept: {g.grievance_id}",
                        f"Grievance {g.grievance_id} is overdue beyond SLA.", grievance_id=g.id)
    admins = User.query.filter_by(role="main_authority").all()
    for a in admins:
        notify_user(a, f"Escalation: Overdue {g.grievance_id}",
                    f"Overdue grievance: {g.grievance_id}. Please escalate.", grievance_id=g.id)
