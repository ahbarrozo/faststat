import os
from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Folder to temporarily store data frames as HTML for display. 
# Those are deleted at the end of each session.
UPLOAD_DIR = 'uploads/'

if not os.path.isdir(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///faststat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('faststat/templates/',UPLOAD_DIR)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000   # limit uploads to 16 MB

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Email settings
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='barrozo.ah@gmail.com',
    MAIL_PASSWORD='',
    MAIL_DEFAULT_SENDER='Alexandre Barrozo <barrozo.ah@gmail.com>')

filename = None
data_frame = None

from faststat import controller
