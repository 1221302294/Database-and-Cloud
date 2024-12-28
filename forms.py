from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Regexp

class EmployeeForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=3, max=100),
        Regexp(r'^[a-zA-Z ]+$', message="Name must contain only letters and spaces")
    ])
    position = StringField('Position', validators=[
        DataRequired(),
        Length(min=2, max=100),
        Regexp(r'^[a-zA-Z ]+$', message="Position must contain only letters and spaces")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=50, message="Password must be between 6 and 50 characters")
    ])
