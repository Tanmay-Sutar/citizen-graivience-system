from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SelectField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from ..models import User


def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class CitizenRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    mobile = StringField('Mobile Number (10 digits)', validators=[DataRequired(), Length(min=10, max=15)])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    terms = BooleanField('I accept the Terms & Conditions', validators=[DataRequired()])
    submit = SubmitField('Register as Citizen')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email is already registered.')

    def validate_mobile(self, field):
        digits = ''.join(c for c in field.data if c.isdigit())
        if len(digits) < 10:
            raise ValidationError('Mobile number must be at least 10 digits.')
        if User.query.filter_by(mobile=digits).first():
            raise ValidationError('Mobile number is already registered.')

    def validate_dob(self, field, min_age=18):
        age = calculate_age(field.data)
        if age < min_age:
            raise ValidationError(f'You must be at least {min_age} years old to register.')


class OfficerRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    mobile = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    department = SelectField('Department', choices=[('', 'Select Department'), ('Water', 'Water'), ('Road', 'Road'), ('Electricity', 'Electricity')], validators=[DataRequired()])
    area = StringField('Area / Location', validators=[DataRequired(), Length(min=2, max=150)])
    role = SelectField('Role', choices=[('officer', 'Officer'), ('co_officer', 'Co-Officer')], validators=[DataRequired()])
    submit = SubmitField('Submit Registration Request')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email is already registered.')

    def validate_mobile(self, field):
        digits = ''.join(c for c in field.data if c.isdigit())
        if len(digits) < 10:
            raise ValidationError('Mobile number must be at least 10 digits.')
        if User.query.filter_by(mobile=digits).first():
            raise ValidationError('Mobile number is already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Login As', choices=[('citizen', 'Citizen'), ('officer', 'Officer'), ('co_officer', 'Co-Officer'), ('main_authority', 'Main Authority')], validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')
