import os
from flask_login import UserMixin
from faststat import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    """SQLAlchemy model for users. Contains id, username, password hash, email and
    email notification."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(60))
    email = db.Column(db.String(120), nullable=False)
    notify = db.Column(db.Boolean())

    def __repr__(self):
        return f"<User '{self.username}', '{self.email}'>"


class Compute(db.Model):
    """SQLAlchemy model for storing results of previous calculations. Includes id to order
    calculations, name of file used (filename), the results, plot (for Two-way ANOVA case),
    comments to be added to calculation, user_id and user."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String())
    result = db.Column(db.String())
    plot = db.Column(db.String())
    comments = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('Compute', lazy='dynamic'))

    def __repr__(self):
        return f"<Compute '{self.result}', '{self.plot}'>"

if not os.path.isfile(os.path.join(os.path.dirname(__file__), 'faststat.db')):
    db.create_all()
