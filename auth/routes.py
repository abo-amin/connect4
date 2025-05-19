from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from auth import auth_bp
from models import db, User
from forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.menu'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.menu'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.menu'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Username or email already exists.', 'danger')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.menu'))
        
    form = ForgotPasswordForm()
    from flask import current_app
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                msg = Message('Reset Your Connect 4 Password',
                            sender='noreply@connect4app.com',
                            recipients=[user.email])
                msg.body = f'Click the following link to reset your password: {reset_url}'
                from flask import current_app
                mail = current_app.extensions['mail']
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Error sending email: {e}")
                flash('Error sending email. Please try again later.', 'danger')
                return render_template('auth/forgot_password.html', form=form)
            
            flash(f'A password reset link has been generated: {reset_url}', 'info')
            
        flash('If the email exists in our system, a password reset link has been sent.', 'info')
        
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.menu'))
        
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or (user.token_expiry and user.token_expiry < datetime.utcnow()):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.token_expiry = None
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form, token=token)


@auth_bp.route('/check_user_exists', methods=['POST'])
def check_user_exists():
    """Check if a user exists in the database."""
    data = request.get_json()
    username = data.get('username', '')
    
    user = User.query.filter_by(username=username).first()
    
    return jsonify({
        'exists': user is not None
    })
