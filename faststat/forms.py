import wtforms as wtf
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError, InputRequired
from faststat.db_models import db, User

class ComputeForm(wtf.Form):
    filename = wtf.StringField(
        label='File', default=None,
        validators=[wtf.validators.InputRequired()])

# Standard Forms
class RegisterForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    notify = BooleanField(label='Email notifications')
    submit = SubmitField(label='Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email has already been used. Please choose a different one')

class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    remember = BooleanField(label='Remember me')
    submit = SubmitField(label='Login')

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class StatForm(FlaskForm):
    filename = FileField(label='Spreadsheet', validators=[InputRequired()], 
                         render_kw={"onchange": "form.submit()"})
