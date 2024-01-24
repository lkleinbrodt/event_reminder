import os
from dotenv import load_dotenv
load_dotenv()
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    ENV = os.environ.get('ENV', 'dev').lower()
    assert ENV in ['dev', 'prod', 'test']
    if SECRET_KEY is None:
        raise ValueError("No SECRET_KEY set for Flask application")
    
    if ENV == 'prod':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(ROOT_DIR, 'app.db')
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(ROOT_DIR, 'dev_app.db')

    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
    TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
    TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
    TWILIO_NUMBER = os.environ['TWILIO_NUMBER']
    
    MAIL_SERVER = None
    
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    S3_BUCKET = os.environ.get('S3_BUCKET')