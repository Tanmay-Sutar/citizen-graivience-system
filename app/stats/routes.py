from flask import Blueprint, render_template, request
from flask_login import login_required
from . import stats_bp
from ..models import Grievance, User, Department
from collections import Counter
from datetime import datetime, timedelta


@stats_bp.route('/')
@login_required
def index():
    gs = Grievance.query.all()
    total = len(gs)
    pending = sum(1 for g in gs if g.status not in ['Resolved', 'Rejected'])
    in_progress = sum(1 for g in gs if g.status == 'In Progress')
    resolved = sum(1 for g in gs if g.status == 'Resolved')

    priority_counts = Counter(g.final_priority for g in gs)
    category_counts = Counter(g.final_category for g in gs if g.final_category != 'Pending Verification')
    dept_counts = Counter(g.department.name for g in gs if g.department)
    status_counts = Counter(g.status for g in gs)

    officers = User.query.filter_by(role='officer').all()
    officer_stats = []
    for o in officers:
        og = [g for g in gs if g.assigned_officer_id == o.id]
        officer_stats.append({
            "name": o.name, "dept": o.department.name if o.department else "—",
            "total": len(og), "resolved": sum(1 for g in og if g.status == 'Resolved'),
            "pending": sum(1 for g in og if g.status not in ['Resolved', 'Rejected']),
            "credits": o.total_credits, "level": o.performance_level
        })

    return render_template('stats/index.html',
                           total=total, pending=pending, in_progress=in_progress, resolved=resolved,
                           priority_counts=priority_counts, category_counts=category_counts,
                           dept_counts=dept_counts, status_counts=status_counts,
                           officer_stats=officer_stats)
