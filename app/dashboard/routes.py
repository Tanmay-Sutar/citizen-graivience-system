from flask import render_template, request
from flask_login import login_required, current_user
from . import dashboard_bp
from ..models import db, Grievance, User, Department, CreditTransaction
from ..decorators import citizen_only, officer_only, co_officer_only, admin_only
from ..credit_system.service import officer_stats


@dashboard_bp.route('/citizen')
@login_required
@citizen_only
def citizen():
    gs = Grievance.query.filter_by(citizen_id=current_user.id).order_by(Grievance.created_at.desc()).all()
    stats = {
        "total": len(gs),
        "pending": sum(1 for g in gs if g.status not in ['Resolved', 'Rejected']),
        "resolved": sum(1 for g in gs if g.status == 'Resolved'),
    }
    return render_template('dashboard/citizen.html', user=current_user, grievances=gs, stats=stats)


@dashboard_bp.route('/officer')
@login_required
@officer_only
def officer():
    if current_user.role == 'officer':
        gs = Grievance.query.filter_by(assigned_officer_id=current_user.id).order_by(Grievance.created_at.desc()).all()
        pending_verify = []
    else:
        gs = Grievance.query.filter_by(department_id=current_user.department_id).order_by(Grievance.created_at.desc()).all()
        pending_verify = [g for g in gs if g.final_category == 'Pending Verification']

    s = officer_stats(current_user.id)
    txns = CreditTransaction.query.filter_by(user_id=current_user.id).order_by(CreditTransaction.created_at.desc()).limit(10).all()
    return render_template('dashboard/officer.html', user=current_user, grievances=gs,
                           stats=s, txns=txns, pending_verify=pending_verify)


@dashboard_bp.route('/co-officer')
@login_required
@co_officer_only
def co_officer():
    dept_id = current_user.department_id
    gs = Grievance.query.filter_by(department_id=dept_id).order_by(Grievance.created_at.desc()).all() if dept_id else []
    officers = User.query.filter_by(role='officer', department_id=dept_id).all() if dept_id else []
    pending = [g for g in gs if g.status not in ['Resolved', 'Rejected']]
    in_progress = [g for g in gs if g.status == 'In Progress']
    resolved = [g for g in gs if g.status == 'Resolved']
    pending_verify = [g for g in gs if g.final_category == 'Pending Verification']
    return render_template('dashboard/co_officer.html', user=current_user, grievances=gs,
                           officers=officers, pending=pending, in_progress=in_progress,
                           resolved=resolved, pending_verify=pending_verify)


@dashboard_bp.route('/admin')
@login_required
@admin_only
def admin():
    gs = Grievance.query.order_by(Grievance.created_at.desc()).all()
    users = User.query.all()
    pending_approvals = User.query.filter_by(approved_by_admin=False).all()
    stats = {
        "total": len(gs),
        "pending": sum(1 for g in gs if g.status not in ['Resolved', 'Rejected']),
        "in_progress": sum(1 for g in gs if g.status == 'In Progress'),
        "resolved": sum(1 for g in gs if g.status == 'Resolved'),
        "unassigned": sum(1 for g in gs if not g.assigned_officer_id),
        "high": sum(1 for g in gs if g.final_priority == 'High'),
        "pending_verify": sum(1 for g in gs if g.final_category == 'Pending Verification'),
        "pending_approvals": len(pending_approvals),
        "total_users": len(users),
    }
    return render_template('dashboard/admin.html', user=current_user, grievances=gs[:30],
                           stats=stats, pending_approvals=pending_approvals)
