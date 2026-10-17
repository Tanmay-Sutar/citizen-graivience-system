"""Grievance routes: submit, detail, list, verify & assign, officer status updates."""
from flask import render_template, redirect, url_for, flash, request, abort, current_app, jsonify
from flask_login import login_required, current_user
from . import grievance_bp
from .forms import GrievanceSubmitForm, GrievanceVerifyForm, GrievanceStatusForm
from ..models import db, Grievance, GrievanceTimeline, Department, User, AuditLog
from ..utils import generate_unique_grievance_id, save_base64_image
from ..decorators import citizen_only, roles_required, officer_only, admin_only, co_officer_only
from ..classifier import run_predictions
from ..credit_system.service import apply_resolution_credits
from ..notifications.service import (notify_status_change, notify_assignment,
                                     notify_high_priority)
from datetime import datetime, timedelta

# Future Enhancement (AI image/evidence verification):
# Use computer vision to verify that the captured photo matches the complaint text.
# For example, if complaint mentions "pothole", confirm the image contains a road
# damage pattern; if it mentions "water pipe leak", confirm water-related imagery.
# Add evidence_verified (bool) + evidence_confidence (float) columns to Grievance,
# run a pre-trained classifier (e.g. CLIP or fine-tuned MobileNet) on submit, and
# only escalate auto-approval when both textual rules and visual evidence align.


def attach_timeline(grievance_id, status_to, note, updated_by_id=None, status_from=None):
    tl = GrievanceTimeline(
        grievance_id=grievance_id,
        status_from=status_from,
        status_to=status_to,
        update_note=note,
        updated_by_id=updated_by_id
    )
    db.session.add(tl)


def write_audit(grievance_id, action_type, performed_by_id, field_name=None, old=None, new=None):
    db.session.add(AuditLog(
        grievance_id=grievance_id, action_type=action_type, field_name=field_name,
        old_value=str(old) if old is not None else None,
        new_value=str(new) if new is not None else None,
        performed_by_id=performed_by_id
    ))


def suggest_assignment(final_category: str):
    """
    Auto assignment rule:
    1. Find Department matching final_category.
    2. In that department, find Officers with area matching citizen's area (by text substring).
       If match, pick the least-loaded officer (fewest open 'In Progress'/'Assigned' grievances).
    3. If no area match -> pick the least loaded officer in the dept overall.
    4. If no officers in dept at all -> return (dept_id, None, 'Unassigned').
    """
    dept = Department.query.filter_by(name=final_category).first()
    if not dept:
        return None, None, "Unassigned"

    officers = User.query.filter_by(role='officer', department_id=dept.id, is_active=True, approved_by_admin=True).all()
    if not officers:
        return dept.id, None, "No officers in department"

    def open_count(o):
        return Grievance.query.filter(
            Grievance.assigned_officer_id == o.id,
            Grievance.status.in_(['Submitted', 'Assigned', 'In Progress', 'Need More Information'])
        ).count()

    officers_sorted = sorted(officers, key=open_count)
    return dept.id, officers_sorted[0].id, None


@grievance_bp.route('/submit', methods=['GET', 'POST'])
@login_required
@citizen_only
def submit():
    form = GrievanceSubmitForm()
    if form.validate_on_submit():
        try:
            image_rel_path = save_base64_image(form.image_data.data)
        except Exception as exc:
            flash(f"Failed to save photo: {exc}", "danger")
            return render_template('grievance/submit.html', form=form)

        try:
            uid = generate_unique_grievance_id()
        except RuntimeError as exc:
            flash(str(exc), "danger")
            return render_template('grievance/submit.html', form=form)

        # ML-based category/priority suggestion (TF-IDF + Logistic Regression).
        # Falls back to keyword rules if trained models are not found.
        preds = run_predictions(
            complaint_text=form.complaint_text.data,
            citizen_category=form.citizen_category.data,
            citizen_priority=form.citizen_priority.data
        )

        sla_map = {"High": current_app.config["SLA_HOURS_HIGH"],
                   "Medium": current_app.config["SLA_HOURS_MEDIUM"],
                   "Low": current_app.config["SLA_HOURS_LOW"]}
        expected = datetime.utcnow() + timedelta(hours=sla_map.get(form.citizen_priority.data, 72))

        g = Grievance(
            grievance_id=uid,
            citizen_id=current_user.id,
            complaint_text=form.complaint_text.data.strip(),
            image_path=image_rel_path,
            citizen_category=form.citizen_category.data,
            citizen_priority=form.citizen_priority.data,
            ml_category=preds["category"],
            ml_category_confidence=preds["category_confidence"],
            ml_priority=preds["priority"],
            ml_priority_confidence=preds["priority_confidence"],
            expected_resolution_time=expected,
            status="Submitted"
        )
        db.session.add(g)
        db.session.flush()
        attach_timeline(
            g.id, "Submitted",
            f"Grievance submitted (citizen chose: {g.citizen_category}/{g.citizen_priority}. "
            f"ML suggestion: {preds['category']} ({preds['category_confidence']:.0%}) / "
            f"{preds['priority']} ({preds['priority_confidence']:.0%}).",
            updated_by_id=current_user.id, status_from=None)
        db.session.commit()

        flash(f"Grievance submitted successfully! Your Grievance ID is <strong>{uid}</strong>.", "success")
        return redirect(url_for('grievance.detail', grievance_id=uid))

    return render_template('grievance/submit.html', form=form)


@grievance_bp.route('/<grievance_id>')
@login_required
def detail(grievance_id):
    g = Grievance.query.filter_by(grievance_id=grievance_id).first_or_404()
    if current_user.role == 'citizen' and g.citizen_id != current_user.id:
        abort(403)
    if current_user.role == 'officer' and g.assigned_officer_id and g.assigned_officer_id != current_user.id:
        abort(403)
    if current_user.role == 'co_officer' and g.department_id and g.department_id != current_user.department_id:
        abort(403)
    return render_template('grievance/detail.html', g=g)


@grievance_bp.route('/my')
@login_required
@citizen_only
def my_grievances():
    gs = Grievance.query.filter_by(citizen_id=current_user.id).order_by(Grievance.created_at.desc()).all()
    return render_template('grievance/list_citizen.html', grievances=gs)


@grievance_bp.route('/<grievance_id>/verify', methods=['GET', 'POST'])
@login_required
@roles_required('officer', 'co_officer', 'main_authority')
def verify(grievance_id):
    g = Grievance.query.filter_by(grievance_id=grievance_id).first_or_404()

    if current_user.role == 'officer' and g.department_id and g.department_id != current_user.department_id:
        abort(403)
    if current_user.role == 'co_officer' and g.department_id and g.department_id != current_user.department_id:
        abort(403)

    form = GrievanceVerifyForm(obj=g)
    officers = User.query.filter_by(role='officer', is_active=True, approved_by_admin=True).all()
    form.assigned_officer_id.choices = [(0, 'Unassigned')] + [
        (o.id, f"{o.name} — {o.department.name if o.department else '—'} ({o.area or 'no area'})")
        for o in officers
    ]

    if request.method == 'GET':
        form.final_category.data = g.final_category if g.final_category != 'Pending Verification' else g.ml_category
        form.final_priority.data = g.final_priority if g.final_priority != 'Pending Verification' else g.ml_priority
        dept = Department.query.filter_by(name=form.final_category.data).first()
        if dept:
            form.department_id.data = dept.id

    if form.validate_on_submit():
        old_cat, old_pri, old_dept, old_off = g.final_category, g.final_priority, g.department_id, g.assigned_officer_id

        new_cat = form.final_category.data
        new_pri = form.final_priority.data

        dept_id = form.department_id.data if form.department_id.data != 0 else None
        officer_id = form.assigned_officer_id.data if form.assigned_officer_id.data != 0 else None

        if dept_id is None and new_cat in ['Water', 'Road', 'Electricity']:
            d = Department.query.filter_by(name=new_cat).first()
            if d:
                dept_id = d.id

        # Auto assignment if officer is not manually selected
        if officer_id is None and new_cat in ['Water', 'Road', 'Electricity']:
            d_id, o_id, reason = suggest_assignment(new_cat)
            if d_id and not dept_id:
                dept_id = d_id
            if o_id:
                officer_id = o_id

        g.final_category = new_cat
        g.final_priority = new_pri
        g.department_id = dept_id
        g.assigned_officer_id = officer_id

        old_status = g.status
        if officer_id is not None and old_status in ['Submitted']:
            g.status = 'Assigned'

        sla_map = {"High": current_app.config["SLA_HOURS_HIGH"],
                   "Medium": current_app.config["SLA_HOURS_MEDIUM"],
                   "Low": current_app.config["SLA_HOURS_LOW"]}
        if new_pri in sla_map and g.created_at:
            g.expected_resolution_time = g.created_at + timedelta(hours=sla_map[new_pri])

        if old_cat != g.final_category:
            write_audit(g.id, "category_correction", current_user.id, "final_category", old_cat, g.final_category)
        if old_pri != g.final_priority:
            write_audit(g.id, "priority_correction", current_user.id, "final_priority", old_pri, g.final_priority)
        if old_dept != g.department_id:
            write_audit(g.id, "department_change", current_user.id, "department_id", old_dept, g.department_id)
        if old_off != g.assigned_officer_id:
            write_audit(g.id, "officer_assignment", current_user.id, "assigned_officer_id", old_off, g.assigned_officer_id)

        note = form.note.data or "Verified & routed"
        if officer_id:
            off = db.session.get(User, officer_id)
            note += f" | Assigned to officer: {off.name if off else officer_id}"
        else:
            note += " | UNASSIGNED — no matching officer"
        attach_timeline(g.id, g.status, note, updated_by_id=current_user.id, status_from=old_status)
        db.session.commit()

        try:
            notify_assignment(g)
            if g.final_priority == "High":
                notify_high_priority(g)
        except Exception:
            pass

        flash("Grievance verified & assigned successfully.", "success")
        return redirect(url_for('grievance.detail', grievance_id=g.grievance_id))

    return render_template('grievance/verify.html', form=form, g=g)


@grievance_bp.route('/<grievance_id>/status', methods=['POST'])
@login_required
@roles_required('officer', 'co_officer')
def update_status(grievance_id):
    g = Grievance.query.filter_by(grievance_id=grievance_id).first_or_404()

    if current_user.role == 'officer' and g.assigned_officer_id != current_user.id:
        abort(403)
    if current_user.role == 'co_officer' and g.department_id != current_user.department_id:
        abort(403)

    form = GrievanceStatusForm(request.form)
    if form.validate():
        old_status = g.status
        new_status = form.status.data
        g.status = new_status

        if new_status == 'Resolved' and not g.resolved_at:
            g.resolved_at = datetime.utcnow()

        attach_timeline(g.id, new_status, form.update_note.data,
                        updated_by_id=current_user.id, status_from=old_status)
        db.session.commit()

        try:
            if new_status == 'Resolved':
                awarded = apply_resolution_credits(g, current_app.config)
            notify_status_change(g, old_status, new_status, current_user)
        except Exception:
            pass

        flash("Status updated.", "success")
    else:
        for fld, errs in form.errors.items():
            for err in errs:
                flash(f"{fld}: {err}", "danger")
    return redirect(url_for('grievance.detail', grievance_id=g.grievance_id))
