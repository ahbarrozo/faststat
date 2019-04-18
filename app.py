import os
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

# Email settings
import base64
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USERNAME = 'barrozo.ah@gmail.com',
    MAIL_PASSWORD = '7heLepper4ffinity',
    MAIL_DEFAULT_SENDER = 'Alexandre Barrozo <barrozo.ah@gmail.com>')

filename = None
statData = None
statFunc = None
statParm = [{}, {}]
dataset1 = None
dataset2 = None
parmNames = None