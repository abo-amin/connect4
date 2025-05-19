from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64, message="Username must be between 3 and 64 characters")
    ])
    email = EmailField('Email', validators=[
        DataRequired(), 
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(), 
        Email(message="Please enter a valid email address")
    ])
    submit = SubmitField('Reset Password')
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password_confirm = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Reset Password')
