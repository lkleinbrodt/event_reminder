from datetime import datetime
from app.s3 import S3
from pytz import timezone

def save_db_to_s3():
    s3 = S3()
    today = datetime.now(timezone('America/Los_Angeles')).date()
    s3.upload_file('app.db', f'app_{today}.db')
    # try:
    # except:
    #     app.logger.exception('Failed to upload app.db to S3')
    return True

if __name__ == '__main__':
    save_db_to_s3()