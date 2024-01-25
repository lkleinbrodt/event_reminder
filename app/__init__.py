from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from logging.handlers import SMTPHandler, RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from app.s3 import S3
from app.twilio_bot import TwilioTextBot

import logging
import os
from datetime import datetime
from config import Config


app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)
login = LoginManager(app)
login.login_view = 'login' #name of endpoint for the login view in routes.py, same as url_for()
admin = Admin(app, name = 'Admin Panel', template_mode='bootstrap3')

text_bot = TwilioTextBot(
    account_sid=Config.TWILIO_ACCOUNT_SID, 
    auth_token=Config.TWILIO_AUTH_TOKEN,
    phone_number = Config.TWILIO_NUMBER
)

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='birthdays Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # rotates logs, keeping last 10 files with a max size of 10kb
    file_handler = RotatingFileHandler('logs/birthdays.log', maxBytes=10240, backupCount=10)
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('birthdays startup')
    
        
from app import routes, models
from app.daily_text import daily_text

import atexit
from pytz import timezone

scheduler = BackgroundScheduler(timezone='America/Los_Angeles')
scheduler.start()
scheduler.add_job(daily_text, 'cron', hour=9, minute=0)

def save_db_to_s3():
    s3 = S3()
    today = datetime.now(timezone('America/Los_Angeles')).date()
    try:
        s3.upload_file('app.db', f'app_{today}.db')
    except:
        app.logger.exception('Failed to upload app.db to S3')
    return True

scheduler.add_job(save_db_to_s3, 'cron', hour=0, minute=10)

admin.add_view(ModelView(models.User, db.session))
admin.add_view(ModelView(models.SpecialDate, db.session))
admin.add_view(ModelView(models.RecurringDate, db.session))

atexit.register(lambda: scheduler.shutdown())

with app.app_context():
    db.create_all()