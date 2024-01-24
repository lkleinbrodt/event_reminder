from datetime import datetime, timedelta
from config import Config
from app.twilio_bot import TwilioTextBot
from app.models import User, SpecialDate, RecurringDate
from app import app

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
    
    special_dates = SpecialDate.query.filter_by(user_phone_number=user.phone_number).all()
    recurring_dates = RecurringDate.query.filter_by(user_phone_number=user.phone_number).all()
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
        app.logger('Sending daily text to {user.phone_number}')
        text_bot.send_message(user.phone_number, message)
    

def daily_text():
    # I'm creating a new text bot here, rather than using the one owned by created in init
    # because I dont want these texts to count for the rate limit / be stopped by it

    text_bot = TwilioTextBot(
        account_sid=Config.TWILIO_ACCOUNT_SID, 
        auth_token=Config.TWILIO_AUTH_TOKEN,
        phone_number = Config.TWILIO_NUMBER
    )

    # Loop over every user in the database
    users = User.query.all()
    for user in users:
        try:
            text_one_user(text_bot, user)
        except Exception as e:
            app.logger.exception(f'Error sending daily text to {user.phone_number} - {e}')
        
    app.logger.info('Sent daily texts')
    return True