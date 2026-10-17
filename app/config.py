import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'instance', 'citizen_grievance.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MIN_AGE = int(os.environ.get('MIN_AGE', 18))

    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.path.join(basedir, os.environ.get('UPLOAD_FOLDER', 'app/static/uploads'))
    ALLOWED_IMAGE_EXTENSIONS = set(os.environ.get('ALLOWED_IMAGE_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))

    SLA_HOURS_HIGH = int(os.environ.get('SLA_HOURS_HIGH', 24))
    SLA_HOURS_MEDIUM = int(os.environ.get('SLA_HOURS_MEDIUM', 72))
    SLA_HOURS_LOW = int(os.environ.get('SLA_HOURS_LOW', 168))

    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', '')

    SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'mock')
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

    CREDIT_RESOLVED = int(os.environ.get('CREDIT_RESOLVED', 10))
    CREDIT_RESOLVED_ON_TIME = int(os.environ.get('CREDIT_RESOLVED_ON_TIME', 5))
    CREDIT_HIGH_PRIORITY = int(os.environ.get('CREDIT_HIGH_PRIORITY', 10))
    CREDIT_TIMELY_UPDATE = int(os.environ.get('CREDIT_TIMELY_UPDATE', 2))

    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True
