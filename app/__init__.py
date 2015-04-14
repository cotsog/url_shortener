import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import BASE_DIR, BASE_URL, URLS_PER_PAGE
from .base_62 import saturate, dehydrate

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

openid = OpenID(app, os.path.join(BASE_DIR, 'tmp'))


from app import views, models