from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime
from game_logic import Board, PLAYER_PIECE, AI_PIECE
from ai import AIPlayer
from models import db, User, Game
from forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
import os
import json
import numpy as np
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connect4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask extensions
db.init_app(app)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Set up mail (for password reset)
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Configure with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'  # Configure with your email
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Configure with your password
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Map difficulty levels to search depths
DIFFICULTY_LEVELS = {
    'easy': 2,
    'medium': 4,
    'hard': 6
}

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('menu'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Username or email already exists.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            # Send email
            reset_url = url_for('reset_password', token=token, _external=True)
            # Uncomment to enable email sending
            # try:
            #     msg = Message('Reset Your Connect 4 Password',
            #                 sender='noreply@connect4app.com',
            #                 recipients=[user.email])
            #     msg.body = f'Click the following link to reset your password: {reset_url}'
            #     mail.send(msg)
            # except Exception as e:
            #     app.logger.error(f"Error sending email: {e}")
            #     flash('Error sending email. Please try again later.', 'danger')
            #     return render_template('forgot_password.html', form=form)
            
            # For development, just show the link
            flash(f'A password reset link has been generated: {reset_url}', 'info')
            
        # Always show the same message for security
        flash('If the email exists in our system, a password reset link has been sent.', 'info')
        
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
        
    user = User.query.filter_by(reset_token=token).first()
    
    # Check if token is valid
    if not user or (user.token_expiry and user.token_expiry < datetime.utcnow()):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.token_expiry = None
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', form=form, token=token)

@app.route('/start', methods=['POST'])
@login_required
def start():
    data = request.get_json()
    session['mode'] = data['mode']
    session['difficulty'] = data['difficulty']
    
    # Record the start of a new game
    session['game_start_time'] = datetime.utcnow().isoformat()
    session['move_count'] = 0
    
    return jsonify(success=True)

@app.route('/game')
@login_required
def game():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
@login_required
def handle_move():
    data = request.get_json()
    board_obj = Board()
    board_obj.board = np.array(data.get('board', []))

    # Input values
    col = data.get('col')  # None or integer
    current_player = data.get('current_player', PLAYER_PIECE)
    mode = session.get('mode', 'ai_vs_human')
    difficulty = session.get('difficulty', 'medium')
    depth = DIFFICULTY_LEVELS.get(difficulty, 4)
    ai_player = AIPlayer(depth=depth)
    
    # Increment move counter
    if 'move_count' in session:
        session['move_count'] = session.get('move_count', 0) + 1

    status = ''
    game_ended = False
    result = None

    # If it's an AI move (col is None) and mode allows AI for this player
    if col is None and ((mode == 'ai_vs_human' and current_player == AI_PIECE) or mode == 'ai_vs_ai'):
        # AI picks a move
        col, _ = ai_player.minimax(board_obj, depth, -np.inf, np.inf, True)

    # Perform move if valid
    if col is not None and board_obj.is_valid_location(col):
        row = board_obj.get_next_open_row(col)
        board_obj.drop_piece(row, col, current_player)

        # Check win or draw
        if board_obj.winning_move(current_player):
            status = f'Player {current_player} wins!'
            game_ended = True
            # Determine win/loss based on who moved last
            if (current_player == PLAYER_PIECE and mode != 'ai_vs_ai') or \
               (mode == 'ai_vs_human' and current_player == AI_PIECE):
                result = 'win' if current_player == PLAYER_PIECE else 'loss'
            else:
                result = 'draw'  # For AI vs AI, we'll consider it a draw for the user's record
        elif board_obj.is_full():
            status = 'Draw!'
            game_ended = True
            result = 'draw'
        else:
            # Switch player
            current_player = PLAYER_PIECE if current_player == AI_PIECE else AI_PIECE
            
    # Save game if it ended
    if game_ended and 'game_start_time' in session:
        save_game_results(board_obj, mode, difficulty, result, session.get('move_count', 0))
        # Clear game session data
        session.pop('game_start_time', None)
        session.pop('move_count', None)

    # Return updated board and status
    response = {
        'board': board_obj.to_list(),
        'status': status,
        'next_player': current_player
    }
    return jsonify(response)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get the user's most recent games
    recent_games = current_user.get_recent_games(10)
    
    # Get the last game played
    last_game = Game.query.filter_by(user_id=current_user.id).order_by(Game.end_time.desc()).first()
    
    # Get game mode statistics
    mode_stats = {
        'ai_vs_human': Game.query.filter_by(user_id=current_user.id, game_mode='ai_vs_human').count(),
        'human_vs_human': Game.query.filter_by(user_id=current_user.id, game_mode='human_vs_human').count(),
        'ai_vs_ai': Game.query.filter_by(user_id=current_user.id, game_mode='ai_vs_ai').count()
    }
    
    return render_template(
        'dashboard.html', 
        recent_games=recent_games, 
        last_game=last_game,
        mode_stats=mode_stats
    )

# Function to save game results
def save_game_results(board_obj, mode, difficulty, result, moves):
    if not current_user.is_authenticated:
        return
        
    try:
        # Calculate game duration
        start_time = datetime.fromisoformat(session.get('game_start_time'))
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Create a new game record
        game = Game(
            user_id=current_user.id,
            game_mode=mode,
            difficulty=difficulty,
            result=result,
            moves=moves,
            start_time=start_time,
            end_time=end_time,
            duration=int(duration),
            board_state=json.dumps(board_obj.to_list())
        )
        db.session.add(game)
        
        # Update user statistics
        current_user.total_games += 1
        if result == 'win':
            current_user.wins += 1
        elif result == 'loss':
            current_user.losses += 1
        elif result == 'draw':
            current_user.draws += 1
            
        current_user.total_game_time += int(duration)
        
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error saving game: {e}")
        db.session.rollback()

# Initialize database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)