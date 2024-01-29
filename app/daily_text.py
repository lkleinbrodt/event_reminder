from datetime import datetime, timedelta
import os
import psycopg2
from app.twilio_bot import TwilioTextBot
from app.models import User, SpecialDate, RecurringDate
from dotenv import load_dotenv
import logging
load_dotenv()

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # You can adjust the log level as needed

# Create a console handler and set the formatter
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)

def connect_to_database():
    logger.debug('Connecting to database')
    connection = psycopg2.connect(
        host=os.environ.get('DATABASE_HOST'),
        database=os.environ.get('DATABASE_DATABASE'),
        user=os.environ.get('DATABASE_USER'),
        password=os.environ.get('DATABASE_PASSWORD'),
    )
    return connection

def close_connection(connection):
    connection.close()

def text_one_user(text_bot: TwilioTextBot, user: User):
    reminder_lags = []
    if user.remind_7_days:
        reminder_lags.append(7)
    if user.remind_3_days:
        reminder_lags.append(3)
    if user.remind_1_day:
        reminder_lags.append(1)
    if user.remind_on_day:
        reminder_lags.append(0)
    
    # Use the database connection
    connection = connect_to_database()
    cursor = connection.cursor()

    try:
        special_dates_query = """
            SELECT * FROM special_date
            WHERE user_phone_number = %s
        """
        recurring_dates_query = """
            SELECT * FROM recurring_date
            WHERE user_phone_number = %s
        """
        with connection.cursor() as cursor:
            # Execute the query
            cursor.execute(special_dates_query, (user.phone_number,))
            columns = [desc[0] for desc in cursor.description]
            special_dates = [dict(zip(columns, row)) for row in cursor.fetchall()]
            special_dates = [SpecialDate(**date) for date in special_dates]
            
            cursor.execute(recurring_dates_query, (user.phone_number,))
            columns = [desc[0] for desc in cursor.description]
            recurring_dates = [dict(zip(columns, row)) for row in cursor.fetchall()]
            recurring_dates = [RecurringDate(**date) for date in recurring_dates]

        special_date_reminders = []
        recurring_date_reminders = []

        today = datetime.now().date()
        for lag in reminder_lags:
            for date in special_dates:
                if date.to_date() == (today + timedelta(days=lag)):
                    special_date_reminders.append(date)
                    
            for date in recurring_dates:
                if date.to_date() == (today + timedelta(days=lag)):
                    recurring_date_reminders.append(date)
        
        date_reminders = special_date_reminders + recurring_date_reminders
        
        if len(date_reminders) > 0:
            message = "The following important dates are coming up soon:"
            for date in date_reminders:
                message += f"\n{date.display_for_text()}"
            logger.info(f'Sending daily text to {user.phone_number}')
            text_bot.send_message(user.phone_number, message)

    except Exception as e:
        logger.exception(f'Error querying database for user {user.phone_number} - {e}')
        raise e

    finally:
        # Close the database connection
        close_connection(connection)

def daily_text():
    # a much more efficient way would be to iterate through the dates, 
    # and compile a dict of users
    # that requires more thinking, cause you have to also check for reminder preferences
    # I'm creating a new text bot here, rather than using the one owned by created in init
    # because I dont want these texts to count for the rate limit / be stopped by it

    text_bot = TwilioTextBot(
        account_sid=os.environ.get('TWILIO_ACCOUNT_SID'),
        auth_token=os.environ.get('TWILIO_AUTH_TOKEN'),
        phone_number=os.environ.get('TWILIO_NUMBER')
    )
    
    if os.environ.get('ENV') == 'prod':
        # Use the database connection
        connection = connect_to_database()

        try:
            #have to use "" around user because it's a reserved word in postgres
            # #TODO: fix this
            users_query = """
                SELECT * FROM "user" 
            """
            with connection.cursor() as cursor:
                cursor.execute(users_query)
                columns = [desc[0] for desc in cursor.description]
                users = [dict(zip(columns, row)) for row in cursor.fetchall()]
                users = [User(**date) for date in users]
            

            for user in users:
                try:
                    text_one_user(text_bot, user)  # Assuming there's a constructor for User
                except Exception as e:
                    logger.exception(f'Error sending daily text to {user} - {e}')
                    raise e

        except Exception as e:
            logger.exception(f'Error querying database for users - {e}')
            raise e

        finally:
            # Close the database connection
            close_connection(connection)
        
    else:
        # Use the database connection
        connection = connect_to_database()
        

        try:
            #have to use "" around user because it's a reserved word in postgres
            # #TODO: fix this
            users_query = """
                SELECT * FROM "user"
                WHERE phone_number = '14153064760'
            """
            with connection.cursor() as cursor:
                cursor.execute(users_query)
                columns = [desc[0] for desc in cursor.description]
                users = [dict(zip(columns, row)) for row in cursor.fetchall()]
                users = [User(**date) for date in users]
        

            if users:
                user = users[0]
                try:
                    text_one_user(text_bot, user)  # Assuming there's a constructor for User
                    logger.info(f'Sent daily text to {user.phone_number}')
                except Exception as e:
                    logger.exception(f'Error sending daily text to {user} - {e}')
                    raise e

        except Exception as e:
            logger.exception(f'Error querying database for user - {e}')
            raise e

        finally:
            # Close the database connection
            close_connection(connection)
        
    logger.info('Sent daily texts')
    return True

if __name__ == '__main__':
    logger.info('Starting daily text')
    daily_text()
