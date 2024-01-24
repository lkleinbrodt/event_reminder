from flask import flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlalchemy as sa
from config import Config
from sqlalchemy.exc import IntegrityError

from app import app, db, text_bot, admin
from app.models import User, SpecialDate, RecurringDate
from app.forms import LoginForm, VerificationForm, SpecialDateForm, RecurringDateForm, SettingsForm
# from app.telegram_bot import RateLimitError
from app.twilio_bot import RateLimitError

from datetime import datetime, timezone, timedelta
from random import randint
from urllib.parse import urlsplit


limiter = Limiter(app = app, key_func=get_remote_address)


### PAGES

@app.before_request
def before_request():
    pass
        
@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home', methods=['POST', 'GET'])
@login_required
def home():
    special_date_form = SpecialDateForm()
    recurring_date_form = RecurringDateForm()
        
    return render_template('home.html', special_date_form = special_date_form, recurring_date_form = recurring_date_form)

@app.route('/login', methods=['POST', 'GET'])
@limiter.limit("5 per 5 seconds")  # Adjust the limit as needed
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm(request.form)
    if form.validate_on_submit():
        phone_number = form.phone_number.data
        
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        check_verification_attempts(request.remote_addr)
        
        user = User.query.filter_by(phone_number=phone_number).first()
        # user = db.session.scalar(
        #     sa.select(User).where(User.username == form.username.data)
        # )
        
        if not user:
            # Create a new user with the provided phone number
            user = User(phone_number=phone_number)
            db.session.add(user)
            db.session.commit()
        
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_code_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc)
        db.session.commit()
        
        ip_address = request.remote_addr
        try:
            text_bot.send_message(
                to_number = str(user.phone_number), #TODO: improve this
                message_body = f"Your code is: {verification_code}",
                from_ip = ip_address
            )

        except RateLimitError:
            flash("Rate limit exceeded. Please try again later.", 'error')
            return redirect(url_for('login'))
        
        return render_template('verify.html', phone_number=phone_number, form=VerificationForm())
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'message')
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        form = SettingsForm(
            remind_7_days = current_user.remind_7_days,
            remind_3_days = current_user.remind_3_days,
            remind_1_day = current_user.remind_1_day,
            remind_on_day = current_user.remind_on_day,
        )
    elif request.method == 'POST':
        form = SettingsForm(request.form)
    
    print('current value for remind_7_days', current_user.remind_7_days)
    print('current value for remind_3_days', current_user.remind_3_days)
    print('current value for remind_1_day', current_user.remind_1_day)
    print('current value for remind_on_day', current_user.remind_on_day)
    
    if request.method == 'POST' and form.validate_on_submit():
        # Update user settings in the database
        user = User.query.filter_by(id=current_user.id).first()

        print('form value for remind_7_days', form.remind_7_days.data)
        print('form value for remind_3_days', form.remind_3_days.data)
        print('form value for remind_1_day', form.remind_1_day.data)
        print('form value for remind_on_day', form.remind_on_day.data)

        user.remind_7_days = form.remind_7_days.data
        user.remind_3_days = form.remind_3_days.data
        user.remind_1_day = form.remind_1_day.data
        user.remind_on_day = form.remind_on_day.data

        try:
            db.session.commit()
            flash('Settings successfully updated.', 'success')
            print('new user value')
            user = User.query.filter_by(id=current_user.id).first()
            print('new value for remind_7_days', user.remind_7_days)
            print('new value for remind_3_days', user.remind_3_days)
            print('new value for remind_1_day', user.remind_1_day)
            print('new value for remind_on_day', user.remind_on_day)
            redirect(url_for('settings'))
        except IntegrityError:
            db.session.rollback()
            flash('Error saving settings. Please try again.', 'error')
            return redirect(url_for('settings'))

    return render_template('settings.html', settings_form=form)

@app.route('/verify', methods=['POST'])
def verify():
    form = VerificationForm(request.form)
    
    # Get the current IP address
    #TODO: improve this it exists in two places
    ip_address = request.remote_addr
    ip_session_key = f'{ip_address}_verification_attempts'
    attempts = session.get(ip_session_key, {'count': 0, 'timestamp': None})
    
    check_verification_attempts(ip_address)
    
    
    if form.validate_on_submit():
        entered_code = form.verification_code.data
        user = User.query.filter_by(phone_number=form.phone_number.data).first()
        
        if user and user.verification_code == entered_code:
            
            expiration_time = (user.verification_code_timestamp + timedelta(minutes=5)).replace(tzinfo=timezone.utc)
            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            
            if current_time <= expiration_time:
                
                # Successful verification
                login_user(user, True)
                
                session[ip_session_key] = {'count': 0, 'timestamp': None}
                
                next_page = request.args.get('next')
                if not next_page or urlsplit(next_page).netloc != '':
                    next_page = url_for('home')
            
                return redirect(next_page)
            else:
                flash('Verification code expired. Please try again.', 'error')
                return redirect(url_for('login'))
        
        else:
            attempts['count'] += 1
            attempts['timestamp'] = datetime.utcnow().replace(tzinfo=timezone.utc)
            
            if attempts['count'] >= 3:
                # Block further attempts for 24 hours
                block_until = attempts['timestamp'] + timedelta(hours=24)
                remaining_time = block_until - datetime.utcnow()
                flash(f'Too many failed attempts. Try again after {str(remaining_time)}.', 'error')
                return redirect(url_for('login'))

            # Update the session for this IP
            session[ip_session_key] = attempts
            flash(f'Invalid verification code (you have {3-attempts["count"]} attempts remaining)', 'error')
            
    
    return render_template('verify.html', form=form, phone_number=form.phone_number.data)


### ENDPOINTS

@app.route('/add-special-date', methods=['POST', 'GET'])
@login_required
def add_special_date():
    form = SpecialDateForm(request.form)
    if form.validate_on_submit():
        label = form.label_input.data
        date = form.date_input.data
        
        # Check for duplicate label
        existing_special_date = SpecialDate.query.filter_by(user_phone_number=current_user.phone_number, label=label).first()
        if existing_special_date:
            flash('You already have an event with that label', 'error')
            return redirect(url_for('home'))
        
        # Save the special date to the database
        special_date = SpecialDate(user_phone_number=current_user.phone_number, label=label, date=date)
        db.session.add(special_date)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Error saving event. Please try again.', 'error')
            return redirect(url_for('home'))
        
        return redirect(url_for('home'))
    return redirect(url_for('home'))

@app.route('/add-recurring-date', methods=['POST'])
@login_required
def add_recurring_date():
    form = RecurringDateForm(request.form)
    if form.validate_on_submit():
        label = form.label_input.data
        month = int(form.month_input.data)
        day = int(form.day_input.data)

        # Check for duplicate label
        existing_recurring_date = RecurringDate.query.filter_by(user_phone_number=current_user.phone_number, label=label).first()
        if existing_recurring_date:
            flash('You already have an event with that label', 'error')
            return redirect(url_for('home'))
        
        # Save the recurring date to the database
        recurring_date = RecurringDate(user_phone_number=current_user.phone_number, label=label, month=month, day=day)
        db.session.add(recurring_date)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Error saving event. Please try again.', 'error')
            return redirect(url_for('home'))
        
        return redirect(url_for('home'))
    
    return redirect(url_for('home'))

@app.route('/delete-recurring-date/<label>', methods=['POST'])
@login_required
def delete_recurring_date(label):
    if not label:
        flash('Invalid request. Please provide a valid label.', 'error')
        return redirect(url_for('home'))
    
    recurring_date = RecurringDate.query.filter_by(user_phone_number=current_user.phone_number, label=label).first()
    
    if not recurring_date:
        flash('Recurring date not found.', 'error')
        return redirect(url_for('home'))
    
    db.session.delete(recurring_date)
    try:
        db.session.commit()
        flash('Date deleted successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error deleting recurring date. Please try again.', 'error')

    return redirect(url_for('home'))

@app.route('/delete-special-date/<label>', methods=['POST'])
@login_required
def delete_special_date(label):
    if not label:
        flash('Invalid request. Please provide a valid label.', 'error')
        return redirect(url_for('home'))
    
    special_date = SpecialDate.query.filter_by(user_phone_number=current_user.phone_number, label=label).first()
    
    if not special_date:
        flash('Special date not found.', 'error')
        return redirect(url_for('home'))
    
    db.session.delete(special_date)
    try:
        db.session.commit()
        flash('Date deleted successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error deleting special date. Please try again.', 'error')

    return redirect(url_for('home'))

@app.route('/login-as-test')
def login_as_test():
    if Config.ENV != 'dev':
        return redirect(url_for('index'))
    
    test_phone_number = '123456789'
    user = User.query.filter_by(phone_number=test_phone_number).first()
    
    if user:
        db.session.delete(user)
        db.session.commit()
        
    user = User(phone_number=test_phone_number)
    db.session.add(user)
    db.session.commit()
    
    
    login_user(user, True)
    
    return redirect(url_for('home'))


def check_verification_attempts(ip_address):
    # Check if there is an existing session for the IP
    ip_session_key = f'{ip_address}_verification_attempts'
    attempts = session.get(ip_session_key, {'count': 0, 'timestamp': None})
    
    if attempts['count'] >= 3:
        # Check if the block has expired
        block_until = (attempts['timestamp'] + timedelta(hours=24)).replace(tzinfo=timezone.utc)
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        if current_time >= block_until:
            # Reset attempts after block expires
            attempts = {'count': 0, 'timestamp': None}
            session[ip_session_key] = attempts
        else:
            remaining_time = block_until - current_time
            flash(f'Too many failed attempts. Try again after {str(remaining_time)}.', 'error')
            #TODO: better way of stopping user from trying too many times
            return redirect(url_for('login'))
        
def generate_verification_code():
    return str(randint(100000, 999999))


@login_required
@app.route('/admin')
def admin():
    if current_user.is_admin():
        return admin.index()