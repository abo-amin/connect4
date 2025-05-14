from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import string
import json

db = SQLAlchemy()

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_mode = db.Column(db.String(20), nullable=False)  # ai_vs_human, human_vs_human, ai_vs_ai
    difficulty = db.Column(db.String(10), nullable=True)  # easy, medium, hard
    result = db.Column(db.String(10), nullable=False)  # win, loss, draw
    moves = db.Column(db.Integer, default=0)  # number of moves in the game
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    board_state = db.Column(db.Text, nullable=True)  # final board state as JSON
    
    def __repr__(self):
        return f'<Game {self.id}: {self.result}>'  
    
    def format_duration(self):
        """Format duration as MM:SS"""
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    @property
    def formatted_start_time(self):
        """Format start time for display"""
        return self.start_time.strftime("%Y-%m-%d %H:%M")
    
    @property
    def formatted_mode(self):
        """Format game mode for readable display"""
        mode_map = {
            'ai_vs_human': 'AI vs Human',
            'human_vs_human': 'Human vs Human',
            'ai_vs_ai': 'AI vs AI'
        }
        return mode_map.get(self.game_mode, self.game_mode)
    
    @property 
    def formatted_difficulty(self):
        """Format difficulty for display with capitalization"""
        if not self.difficulty:
            return "N/A"
        return self.difficulty.capitalize()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Game statistics
    total_games = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    total_game_time = db.Column(db.Integer, default=0)  # in seconds
    
    # Relationship with games
    games = db.relationship('Game', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def generate_reset_token(self):
        # Generate a secure random token
        alphabet = string.ascii_letters + string.digits
        self.reset_token = ''.join(secrets.choice(alphabet) for i in range(64))
        # Set expiry time (24 hours)
        from datetime import timedelta
        self.token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.reset_token
        
    def __repr__(self):
        return f'<User {self.username}>'
        
    @property
    def average_game_time(self):
        """Calculate average game time in seconds"""
        if self.total_games > 0:
            return round(self.total_game_time / self.total_games)
        return 0
        
    @property
    def win_rate(self):
        """Calculate win rate as a percentage"""
        if self.total_games > 0:
            return round((self.wins / self.total_games) * 100, 1)
        return 0.0
        
    def get_recent_games(self, limit=5):
        """Get the most recent games for this user"""
        return Game.query.filter_by(user_id=self.id).order_by(Game.end_time.desc()).limit(limit).all()
