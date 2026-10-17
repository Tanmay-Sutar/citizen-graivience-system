from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from . import chat_bp
from ..models import db, ChatMessage, Department, User, Grievance
from ..decorators import officer_only


@chat_bp.route('/department')
@login_required
@officer_only
def department_chat():
    if current_user.role == 'officer':
        dept_id = current_user.department_id
    elif current_user.role == 'co_officer':
        dept_id = current_user.department_id
    else:
        dept_id = request.args.get('department_id', type=int)
    messages = ChatMessage.query.filter_by(department_id=dept_id).order_by(ChatMessage.created_at).all()
    departments = Department.query.all()
    return render_template('chat/department.html', messages=messages,
                           department_id=dept_id, departments=departments)


@chat_bp.route('/department/send', methods=['POST'])
@login_required
@officer_only
def send_department():
    dept_id = request.form.get('department_id', type=int)
    message = request.form.get('message', '').strip()
    if not message:
        return redirect(url_for('chat.department_chat', department_id=dept_id))
    msg = ChatMessage(department_id=dept_id, sender_id=current_user.id,
                      message=message, message_type='text')
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('chat.department_chat', department_id=dept_id))


@chat_bp.route('/grievance/<grievance_id>')
@login_required
@officer_only
def grievance_thread(grievance_id):
    g = Grievance.query.filter_by(grievance_id=grievance_id).first_or_404()
    if current_user.role == 'officer' and g.assigned_officer_id and g.assigned_officer_id != current_user.id:
        abort(403)
    if current_user.role == 'co_officer' and g.department_id and g.department_id != current_user.department_id:
        abort(403)
    messages = ChatMessage.query.filter_by(grievance_id=g.id).order_by(ChatMessage.created_at).all()
    return render_template('chat/grievance.html', g=g, messages=messages)


@chat_bp.route('/grievance/<grievance_id>/send', methods=['POST'])
@login_required
@officer_only
def send_grievance(grievance_id):
    g = Grievance.query.filter_by(grievance_id=grievance_id).first_or_404()
    message = request.form.get('message', '').strip()
    if not message:
        return redirect(url_for('chat.grievance_thread', grievance_id=grievance_id))
    msg = ChatMessage(grievance_id=g.id, department_id=g.department_id,
                      sender_id=current_user.id, message=message, message_type='text')
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('chat.grievance_thread', grievance_id=grievance_id))
