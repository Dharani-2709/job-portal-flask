# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length
from wtforms.fields import DateField  #  Import DateField

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('seeker', 'Job Seeker'), ('employer', 'Employer')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class JobForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    salary = StringField('Salary', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    expiration_date = DateField('Expiration Date (optional)', format='%Y-%m-%d')  # ✅ New field
    submit = SubmitField('Post Job')
