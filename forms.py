import wtforms as wtf
from math import pi

def check_T(form, field):
    """Form validation: failure if T > 30 periods"""
    w = form.w.data
    T = field.data
    period = 2*pi / w
    if T > 30 * period:
        num_periods = int(round(T/period))
        raise validators.ValidationError("Cannot plot as much as {} periods!".format(num_periods))

class ComputeForm(wtf.Form):
    filename = wtf.StringField(
        label='File', default=None,
        validators=[wtf.validators.InputRequired()])

from db_models import db, User
import flask_wtf

#Standard Forms
class register_form(wtf.Form):
    username = wtf.TextField(
       label = 'Username', validators=[wtf.validators.Required()])
    password = wtf.PasswordField(
       label = 'Password', validators=[
           wtf.validators.Required(),
           wtf.validators.EqualTo(
               'confirm', message='Passwords must match')])
    confirm  = wtf.PasswordField(
       label = 'Confirm Password',validators=[wtf.validators.Required()])
    email = wtf.StringField(label='Email')
    notify = wtf.BooleanField(label='Email notifications')

    def validate(self):
        if not wtf.Form.validate(self):
            return False

        if self.notify.data and not self.email.data:
            self.notify.errors.append('Cannot send notifications without a valid email address')
            return False

        if db.session.query(User).filter_by(username=self.username.data).count() > 0:
            self.username.append('User already exists')
            return False

        return True

class login_form(wtf.Form):
    username = wtf.TextField(
       label = 'Username', validators=[wtf.validators.Required()])
    password = wtf.PasswordField(
       label = 'Password', validators=[wtf.validators.Required()])

    def validate(self):
        if not wtf.Form.validate(self):
            return False

        user = self.get_user()

        if user is None:
            self.username.errors.append('Unknown username')
            return False

        if not user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        return True

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class StatForm(wtf.Form):
    filename   = wtf.FileField(validators=
                               [wtf.validators.InputRequired()])

