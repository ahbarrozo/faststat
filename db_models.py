from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import app

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique = True)
    pwhash = db.Column(db.String())
    email = db.Column(db.String(120), nullable = True)
    notify = db.Column(db.Boolean())

    def __repr__(self):
        return '<User %r>' % (self.username)


    def check_password(self, pw):
        return check_password_hash(self.pwhash, pw)


    def set_password(self, pw):
        self.pwhash = generate_password_hash(pw)

    # Variables that must be declared to use flask_login library    
    is_authenticated = True
    is_anonymous = False
    is_active = True


    def get_id(self):
        return self.id


class Compute(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    filename = db.Column(db.String())
    result = db.Column(db.String())
    plot = db.Column(db.String())
    comments = db.Column(db.String(), nullable = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref = db.backref('Compute', lazy = 'dynamic'))

