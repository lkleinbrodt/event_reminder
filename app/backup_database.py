from datetime import datetime
from app.s3 import S3
from pytz import timezone
from app import app
from config import Config

def save_db_to_s3():
    app.logger.info('TRYING TO BACKUP DB TO S3')
    s3 = S3()
    today = datetime.now(timezone('America/Los_Angeles')).date()
    try:
        if Config.ENV == 'dev':
            s3.upload_file('app.db', f'app_dev_{today}.db')
        else:
            s3.upload_file('app.db', f'app_{today}.db')
    except:
        app.logger.exception('Failed to upload app.db to S3')
    return True

if __name__ == '__main__':
    with app.app_context():
        save_db_to_s3()
    print('done')