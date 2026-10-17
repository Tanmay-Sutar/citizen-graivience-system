from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import main_bp


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('index.html')


@main_bp.route('/home')
@login_required
def home():
    if current_user.role == 'citizen':
        return redirect(url_for('dashboard.citizen'))
    elif current_user.role == 'officer':
        return redirect(url_for('dashboard.officer'))
    elif current_user.role == 'co_officer':
        return redirect(url_for('dashboard.co_officer'))
    elif current_user.role == 'main_authority':
        return redirect(url_for('dashboard.admin'))
    return redirect(url_for('main.index'))
