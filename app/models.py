from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ============================================================
# USER MODEL (Handles all 4 roles: citizen, officer, co_officer, main_authority)
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(15), unique=True, nullable=False, index=True)
    dob = db.Column(db.Date, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False)

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    area = db.Column(db.String(150), nullable=True)

    is_active = db.Column(db.Boolean, default=False)
    approved_by_admin = db.Column(db.Boolean, default=False)

    total_credits = db.Column(db.Integer, default=0)
    performance_level = db.Column(db.String(20), default='Bronze')

    terms_accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = db.relationship('Department', back_populates='members')
    grievances_submitted = db.relationship('Grievance', foreign_keys='Grievance.citizen_id', back_populates='citizen')
    grievances_assigned = db.relationship('Grievance', foreign_keys='Grievance.assigned_officer_id', back_populates='assigned_officer')
    credit_transactions = db.relationship('CreditTransaction', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'main_authority'

    @property
    def is_officer(self):
        return self.role in ['officer', 'co_officer', 'main_authority']


# ============================================================
# DEPARTMENT MODEL (Water / Road / Electricity)
# ============================================================
class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('User', back_populates='department')
    grievances = db.relationship('Grievance', back_populates='department')
    co_officers = db.relationship('User', foreign_keys='User.department_id',
                                  primaryjoin="and_(User.department_id==Department.id, User.role=='co_officer')",
                                  viewonly=True)


# ============================================================
# GRIEVANCE MODEL (Core entity)
# ============================================================
class Grievance(db.Model):
    __tablename__ = 'grievances'

    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.String(30), unique=True, nullable=False, index=True)

    citizen_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    complaint_text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)

    citizen_category = db.Column(db.String(50), nullable=False)
    citizen_priority = db.Column(db.String(20), nullable=False)

    ml_category = db.Column(db.String(50), nullable=True)
    ml_category_confidence = db.Column(db.Float, nullable=True)
    ml_priority = db.Column(db.String(20), nullable=True)
    ml_priority_confidence = db.Column(db.Float, nullable=True)

    final_category = db.Column(db.String(50), default='Pending Verification')
    final_priority = db.Column(db.String(20), default='Pending Verification')

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    status = db.Column(db.String(50), default='Submitted')
    expected_resolution_time = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citizen = db.relationship('User', foreign_keys=[citizen_id], back_populates='grievances_submitted')
    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], back_populates='grievances_assigned')
    department = db.relationship('Department', back_populates='grievances')
    timeline = db.relationship('GrievanceTimeline', back_populates='grievance', cascade='all, delete-orphan', order_by='GrievanceTimeline.created_at')
    chats = db.relationship('ChatMessage', back_populates='grievance', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', back_populates='grievance', cascade='all, delete-orphan')


# ============================================================
# GRIEVANCE TIMELINE (Status history and work updates)
# ============================================================
class GrievanceTimeline(db.Model):
    __tablename__ = 'grievance_timeline'

    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False)
    status_from = db.Column(db.String(50), nullable=True)
    status_to = db.Column(db.String(50), nullable=True)
    update_note = db.Column(db.Text, nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    grievance = db.relationship('Grievance', back_populates='timeline')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])


# ============================================================
# CREDIT TRANSACTION (Audit trail for performance points)
# ============================================================
class CreditTransaction(db.Model):
    __tablename__ = 'credit_transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=True)
    reason = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='credit_transactions')
    grievance = db.relationship('Grievance')


# ============================================================
# CHAT MESSAGE (Officer collaboration platform)
# ============================================================
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(30), default='text')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department')
    grievance = db.relationship('Grievance', back_populates='chats')
    sender = db.relationship('User', foreign_keys=[sender_id])


# ============================================================
# NOTIFICATION LOG (SMS / Email history)
# ============================================================
class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    recipient_type = db.Column(db.String(30), nullable=False)
    recipient_id = db.Column(db.Integer, nullable=True)
    recipient_email = db.Column(db.String(150), nullable=True)
    recipient_mobile = db.Column(db.String(20), nullable=True)
    channel = db.Column(db.String(10), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=True)
    status = db.Column(db.String(20), default='sent')
    mock_mode = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# AUDIT LOG (Tracks category/priority corrections)
# ============================================================
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(50), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    grievance = db.relationship('Grievance', back_populates='audit_logs')
    performed_by = db.relationship('User', foreign_keys=[performed_by_id])
