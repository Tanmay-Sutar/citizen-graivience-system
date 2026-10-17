"""Grievance & verification forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from ..models import Department, User


class GrievanceSubmitForm(FlaskForm):
    """Back-end validation; image comes as base64 in a hidden field (no file upload allowed)."""
    image_data = HiddenField("Camera Photo", validators=[DataRequired(message="Please capture a photo using the camera.")])
    complaint_text = TextAreaField("Describe Your Complaint", validators=[
        DataRequired(message="Please describe your complaint."),
        Length(min=10, max=2000, message="Description must be between 10 and 2000 characters.")
    ])
    citizen_category = SelectField("Category",
                                   choices=[("", "Select Category"),
                                            ("Water", "Water"),
                                            ("Road", "Road"),
                                            ("Electricity", "Electricity")],
                                   validators=[DataRequired(message="Please select a category.")])
    citizen_priority = SelectField("Suggested Priority",
                                   choices=[("", "Select Priority"),
                                            ("High", "High"),
                                            ("Medium", "Medium"),
                                            ("Low", "Low")],
                                   validators=[DataRequired(message="Please suggest a priority.")])
    submit = SubmitField("Submit Grievance")


class GrievanceVerifyForm(FlaskForm):
    """Officer/Authority verification: accept ML or manually set final."""
    final_category = SelectField("Final Category",
                                 choices=[("Pending Verification", "Pending Verification"),
                                          ("Water", "Water"),
                                          ("Road", "Road"),
                                          ("Electricity", "Electricity")],
                                 validators=[DataRequired()])
    final_priority = SelectField("Final Priority",
                                 choices=[("Pending Verification", "Pending Verification"),
                                          ("High", "High"),
                                          ("Medium", "Medium"),
                                          ("Low", "Low")],
                                 validators=[DataRequired()])
    department_id = SelectField("Department", coerce=int, validators=[DataRequired()])
    assigned_officer_id = SelectField("Assigned Officer", coerce=int)
    note = TextAreaField("Verification / Routing Note (optional)",
                         validators=[Length(max=1000)])
    submit = SubmitField("Verify & Assign")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = Department.query.order_by(Department.name).all()
        self.department_id.choices = [(0, "Unassigned")] + [(d.id, d.name) for d in departments]
        self.assigned_officer_id.choices = [(0, "Unassigned")]


class GrievanceStatusForm(FlaskForm):
    """Officer status / progress updates."""
    status = SelectField("Update Status",
                         choices=[("Submitted", "Submitted"),
                                  ("Assigned", "Assigned"),
                                  ("In Progress", "In Progress"),
                                  ("Need More Information", "Need More Information"),
                                  ("Resolved", "Resolved"),
                                  ("Rejected", "Rejected")],
                         validators=[DataRequired()])
    update_note = TextAreaField("Work Update / Note",
                                validators=[DataRequired(message="Please provide an update note."),
                                            Length(min=3, max=1000)])
    submit = SubmitField("Update Grievance")
