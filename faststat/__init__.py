import os
from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Folder to temporarily store data frames as HTML for display. 
# Those are deleted at the end of each session.
UPLOAD_FOLDER = 'uploads/'
UPLOAD_PATH = os.path.join('faststat/templates/', UPLOAD_FOLDER)

if not os.path.isdir(UPLOAD_PATH):
    os.mkdir(UPLOAD_PATH)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///faststat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_PATH 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000   # limit uploads to 16 MB

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from faststat import controller
