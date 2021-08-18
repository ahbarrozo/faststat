import wtforms as wtf
from db_models import db, User

class ComputeForm(wtf.Form):
    filename = wtf.StringField(
        label='File', default=None,
        validators=[wtf.validators.InputRequired()])

# Standard Forms
class RegisterForm(wtf.Form):
    username = wtf.StringField(label='Username', validators=[wtf.validators.DataRequired()])
    password = wtf.PasswordField(label='Password',
                                 validators=[wtf.validators.DataRequired(),
                                             wtf.validators.EqualTo('confirm', message='Passwords must match')])
    confirm = wtf.PasswordField(label='Confirm Password', validators=[wtf.validators.DataRequired()])
    email = wtf.StringField(label='Email')
    notify = wtf.BooleanField(label='Email notifications')

    def validate(self):
        if not wtf.Form.validate(self):
            return False

        if self.notify.data and not self.email.data:
            self.notify.errors.append('Cannot send notifications without a valid email address')
            return False

        if db.session.query(User).filter_by(username=self.username.data).count() > 0:
            self.username.errors.append('User already exists')
            return False

        return True

class LoginForm(wtf.Form):
    username = wtf.StringField(label='Username', validators=[wtf.validators.DataRequired()])
    password = wtf.PasswordField(label='Password', validators=[wtf.validators.DataRequired()])

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
    filename = wtf.FileField(validators=[wtf.validators.InputRequired()])

