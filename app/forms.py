from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import User
import phonenumbers
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length
import calendar

class LoginForm(FlaskForm):
    phone_number = StringField('Phone', validators=[DataRequired()])

    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
    def validate_phone_number(form, field):
        stripped_number = ''.join(filter(str.isdigit, field.data))
        if len(stripped_number) != 11:
            raise ValidationError('Please enter a 10 digit phone number. (Only U.S. numbers are supported)')
        try:
            input_number = phonenumbers.parse(stripped_number)
            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Invalid phone number.')
        except:
            input_number = phonenumbers.parse("+1" + stripped_number)
            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Invalid phone number.')
            
    def validate_phone_number2(self, phone):
        stripped_number = ''.join(filter(str.isdigit, phone.data))
        try:
            p = phonenumbers.parse(stripped_number)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Invalid phone number')

class VerificationForm(FlaskForm):
    phone_number = StringField('Phone', validators=[DataRequired()])
    verification_code = StringField('Verification Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify')
    
    def validate_phone_number(form, field):
        if len(field.data) > 16:
            raise ValidationError('Invalid phone number.')
        try:
            input_number = phonenumbers.parse(field.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')
        except:
            input_number = phonenumbers.parse("+1"+field.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')

class SpecialDateForm(FlaskForm):
    date_input = DateField('Select Date', validators=[DataRequired()], format='%Y-%m-%d', id='dateInputSpecial')
    label_input = StringField('Event Label', validators=[DataRequired()], id='labelInputSpecial', render_kw={"placeholder": "Enter Event Label"})
    save_event_button = SubmitField('Save Event', render_kw={"class": "btn btn-primary btn-block"})
    
class RecurringDateForm(FlaskForm):
    month_choices = [
        ('', 'Select Month'),
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ]

    month_input = SelectField('Month', choices=month_choices, validators=[DataRequired()], id='monthInputRecurring')
    day_input = IntegerField('Day', validators=[DataRequired()], id='dayInputRecurring', render_kw={"placeholder": "Enter Day", "min": 1, "max": 31})
    label_input = StringField('Event Label', validators=[DataRequired()], id='labelInputRecurring', render_kw={"placeholder": "Enter Event Label"})
    save_event_button = SubmitField('Save Event', render_kw={"class": "btn btn-primary btn-block"})
        
    def validate_month_and_day(form, field):
        month = form.month_input.data
        day = str(form.day_input.data)
        
        def is_valid_date(month, day):
            try:
                # Check if the day is valid for the given month
                # use 2020 cause it's a leap year
                return calendar.monthrange(2020, int(month))[1] >= int(day)
            except ValueError:
                # Handle invalid month input (e.g., non-integer)
                return False

        try:
            if not is_valid_date(month, day):
                raise ValidationError('Invalid date.')
        except ValueError:
            raise ValidationError('Invalid date.')

    
class SettingsForm(FlaskForm):
    remind_7_days = BooleanField('Remind me 7 days before event')
    remind_3_days = BooleanField('Remind me 3 days before event')
    remind_1_day = BooleanField('Remind me 1 day before event')
    remind_on_day = BooleanField('Remind me on the day of the event')
    submit = SubmitField('Save Settings')