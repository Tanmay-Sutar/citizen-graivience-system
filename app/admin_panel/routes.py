from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import admin_bp
from ..models import db, User, Department, Grievance, NotificationLog, CreditTransaction
from ..decorators import admin_only
from ..credit_system.service import officer_stats
from sqlalchemy import func


@admin_bp.route('/')
@login_required
@admin_only
def index():
    users = User.query.all()
    departments = Department.query.all()
    grievances = Grievance.query.order_by(Grievance.created_at.desc()).all()
    pending_approvals = User.query.filter_by(approved_by_admin=False).all()

    stats = {
        "total_users": len(users),
        "total_grievances": len(grievances),
        "pending": len([g for g in grievances if g.status not in ['Resolved', 'Rejected']]),
        "resolved": len([g for g in grievances if g.status == 'Resolved']),
        "unassigned": len([g for g in grievances if not g.assigned_officer_id]),
        "pending_approvals": len(pending_approvals),
    }
    return render_template('admin_panel/index.html', stats=stats, users=users,
                           departments=departments, grievances=grievances,
                           pending_approvals=pending_approvals)


@admin_bp.route('/approve/<int:user_id>')
@login_required
@admin_only
def approve_officer(user_id):
    user = db.session.get(User, user_id)
    if user and user.role in ['officer', 'co_officer']:
        user.approved_by_admin = True
        user.is_active = True
        db.session.commit()
        flash(f"Approved: {user.name} ({user.role}).", "success")
    return redirect(url_for('admin_panel.index'))


@admin_bp.route('/reject/<int:user_id>')
@login_required
@admin_only
def reject_officer(user_id):
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f"Rejected and removed: {user.name}.", "warning")
    return redirect(url_for('admin_panel.index'))


@admin_bp.route('/users')
@login_required
@admin_only
def users():
    users_list = User.query.order_by(User.role, User.created_at).all()
    return render_template('admin_panel/users.html', users=users_list)


@admin_bp.route('/performance')
@login_required
@admin_only
def performance():
    officers = User.query.filter_by(role='officer').all()
    co_officers = User.query.filter_by(role='co_officer').all()
    perfs = []
    for o in officers:
        s = officer_stats(o.id)
        perfs.append({"user": o, **s})
    co_perfs = []
    for c in co_officers:
        s = officer_stats(c.id)
        co_perfs.append({"user": c, **s})
    return render_template('admin_panel/performance.html', perfs=perfs, co_perfs=co_perfs)


@admin_bp.route('/notifications')
@login_required
@admin_only
def notifications():
    logs = NotificationLog.query.order_by(NotificationLog.created_at.desc()).limit(100).all()
    return render_template('admin_panel/notifications.html', logs=logs)
