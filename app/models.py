import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from flask_login import UserMixin
from app import db, login

import pytz
import calendar
import phonenumbers
from typing import Optional
from datetime import datetime, timedelta

def format_phone_number(phone_number_str):
    """
    Formats a phone number string in the US national format.

    Args:
        phone_number_str (str): The phone number string to be formatted.

    Returns:
        str: The formatted phone number.

    """
    phone_number = phonenumbers.parse(phone_number_str, 'US')

    formatted_number = phonenumbers.format_number(
        phone_number,
        phonenumbers.PhoneNumberFormat.NATIONAL
    )

    return formatted_number

class User(UserMixin, db.Model):
    """
    Represents a user in the application.

    Attributes:
        id (int): The unique identifier of the user.
        phone_number (str): The phone number of the user.
        verification_code (str): The verification code for the user.
        verification_code_timestamp (datetime): The timestamp when the verification code was generated.
        special_dates (list): The special dates associated with the user.
        recurring_dates (list): The recurring dates associated with the user.
        remind_7_days (bool): Flag indicating whether to remind the user 7 days before their dates.
        remind_3_days (bool): Flag indicating whether to remind the user 3 days before their dates.
        remind_1_day (bool): Flag indicating whether to remind the user 1 day before their dates.
        remind_on_day (bool): Flag indicating whether to remind the user on the day of their dates.
        password_hash (str): The hashed password of the user. (CURRENTLY UNUSED)

    Methods:
        display_phone_number(): Returns the formatted phone number of the user.
    """

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    verification_code = db.Column(db.String(6))
    verification_code_timestamp = db.Column(DateTime(timezone=True), server_default=func.now())

    special_dates = db.relationship('SpecialDate', backref='user', lazy=True)
    recurring_dates = db.relationship('RecurringDate', backref='user', lazy=True)
    
    remind_7_days = db.Column(db.Boolean, default=False)
    remind_3_days = db.Column(db.Boolean, default=True)  
    remind_1_day = db.Column(db.Boolean, default=False)
    remind_on_day = db.Column(db.Boolean, default=True)
    
    role = db.Column(db.String(80), default='user')

    
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    
    def display_phone_number(self):
        """
        Returns the formatted phone number of the user.

        Returns:
            str: The formatted phone number.
        """
        return format_phone_number(self.phone_number)
    
    def get_sorted_special_dates(self):
        """
        Returns the special dates associated with the user sorted by date.

        Returns:
            list: The sorted special dates.
        """
        return sorted(self.special_dates, key=lambda x: x.to_date())

    def get_sorted_recurring_dates(self):
        """
        Returns the recurring dates associated with the user sorted by date.

        Returns:
            list: The sorted recurring dates.
        """
        return sorted(self.recurring_dates, key=lambda x: x.to_date())
    
    def get_sorted_dates(self):
        """
        Returns all dates associated with the user sorted by date.

        Returns:
            list: The sorted dates.
        """
        return sorted(self.special_dates + self.recurring_dates, key=lambda x: x.to_date())
    

    def __repr__(self):
        return f"User('{self.phone_number}')"
    
    def is_admin(self):
        return self.role == 'admin'

class SpecialDate(db.Model):
    """
    Represents a special date associated with a user.

    Attributes:
        id (int): The unique identifier for the special date.
        user_phone_number (str): The phone number of the user associated with the special date.
        label (str): The label or description of the special date.
        date (datetime.date): The date of the special event.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_phone_number = db.Column(db.String, db.ForeignKey('user.phone_number'), nullable=False)
    label = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    #couldnt get this working
    # __table_args__ = (UniqueConstraint('user_phone_number', 'label', name='_user_label_uc'),)

    def __repr__(self):
        return f"SpecialDate('{self.user}', '{self.label}', '{self.date}')"
    
    def display_for_text(self):
        """
        Returns the formatted string for the special date.

        Returns:
            str: The formatted string for the special date.
        """
        return f"{self.label} - {self.date.strftime('%B %d')}"
    
    def to_date(self):
        return self.date
    
    def get_days_away(self):
        """
        Returns the number of days until the special date.

        Returns:
            int: The number of days until the special date.
        """
        today = datetime.now().date()
        return (self.to_date() - today).days
    
class RecurringDate(db.Model):
    """
    Represents a recurring date for a user.

    Attributes:
        id (int): The unique identifier for the recurring date.
        user_phone_number (str): The phone number of the user associated with the recurring date.
        label (str): The label or description of the recurring date.
        month (int): The month of the recurring date.
        day (int): The day of the recurring date.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_phone_number = db.Column(db.String, db.ForeignKey('user.phone_number'), nullable=False)
    label = db.Column(db.String(50), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    
    def get_month_word(self):
        """
        Returns the name of the month for the recurring date.

        Returns:
            str: The name of the month.
        """
        month_word = calendar.month_name[self.month]
        return month_word

    def __repr__(self):
        return f"RecurringDate('{self.user}', '{self.label}', '{self.date}')"
    
    def display_for_text(self):
        """
        Returns the formatted string for the recurring date.

        Returns:
            str: The formatted string for the recurring date.
        """
        return f"{self.label} - {self.get_month_word()} {self.day}"
    
    def to_date(self):
        today = datetime.now().date()
        return datetime(today.year, self.month, self.day).date()
    
    def get_days_away(self):
        """
        Returns the number of days until the special date.

        Returns:
            int: The number of days until the special date.
        """
        today = datetime.now().date()
        return (self.to_date() - today).days

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))