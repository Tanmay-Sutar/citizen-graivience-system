from datetime import date
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from .forms import CitizenRegistrationForm, OfficerRegistrationForm, LoginForm
from ..models import db, User, Department
from ..decorators import roles_required


@auth_bp.route('/register/citizen', methods=['GET', 'POST'])
def register_citizen():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = CitizenRegistrationForm()
    min_age = current_app.config['MIN_AGE']

    if form.validate_on_submit():
        age = date.today().year - form.dob.data.year - ((date.today().month, date.today().day) < (form.dob.data.month, form.dob.data.day))
        if age < min_age:
            flash(f'You must be at least {min_age} years old to register.', 'danger')
            return render_template('auth/register_citizen.html', form=form, min_age=min_age)

        mobile_digits = ''.join(c for c in form.mobile.data if c.isdigit())
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            mobile=mobile_digits,
            dob=form.dob.data,
            role='citizen',
            is_active=True,
            approved_by_admin=True,
            terms_accepted=form.terms.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_citizen.html', form=form, min_age=min_age)


@auth_bp.route('/register/officer', methods=['GET', 'POST'])
def register_officer():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = OfficerRegistrationForm()
    departments = Department.query.all()
    form.department.choices = [('', 'Select Department')] + [(d.name, d.name) for d in departments]

    if form.validate_on_submit():
        dept = Department.query.filter_by(name=form.department.data).first()
        mobile_digits = ''.join(c for c in form.mobile.data if c.isdigit())

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            mobile=mobile_digits,
            role=form.role.data,
            department_id=dept.id if dept else None,
            area=form.area.data.strip(),
            is_active=False,
            approved_by_admin=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Registration submitted! Awaiting approval from Main Authority.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_officer.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None:
            flash('Invalid email or password.', 'danger')
        elif not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
        elif user.role != form.role.data:
            flash(f'Account is registered as {user.role}. Please select correct role.', 'warning')
        elif not user.is_active:
            flash('Your account is not active yet. Please contact Main Authority.', 'warning')
        elif form.role.data in ['officer', 'co_officer'] and not user.approved_by_admin:
            flash('Your registration is pending approval. Please wait for Main Authority approval.', 'warning')
        else:
            login_user(user, remember=form.remember.data)
            flash(f'Welcome, {user.name}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.home'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
