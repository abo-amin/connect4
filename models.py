from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import string
import json
from enum import Enum

db = SQLAlchemy()

# Enum for friendship status
class FriendshipStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    BLOCKED = 'blocked'

# Enum for message status
class MessageStatus(Enum):
    UNREAD = 'unread'
    READ = 'read'
    DELETED = 'deleted'
    
# Enum for notification types
class NotificationType(Enum):
    FRIEND_REQUEST = 'friend_request'
    GAME_INVITE = 'game_invite'
    MESSAGE = 'message'
    SYSTEM = 'system'

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_mode = db.Column(db.String(20), nullable=False)  # ai_vs_human, human_vs_human, ai_vs_ai
    difficulty = db.Column(db.String(100), nullable=True)  # easy, medium, hard or opponent:username:id
    result = db.Column(db.String(10), nullable=False)  # win, loss, draw
    moves = db.Column(db.Integer, default=0)  # number of moves in the game
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    board_state = db.Column(db.Text, nullable=True)  # final board state as JSON
    opponent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # For human vs human games
    
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
        
        # If this is a human vs human game, check if the opponent info is stored in difficulty
        if self.game_mode == 'human_vs_human' and self.difficulty and self.difficulty.startswith('opponent:'):
            # Return N/A since we'll use opponent_name property instead
            return "N/A"
        
        return self.difficulty.capitalize()
        
    @property
    def opponent_name(self):
        """Extract opponent name for human vs human games"""
        if self.game_mode == 'human_vs_human' and self.difficulty and self.difficulty.startswith('opponent:'):
            # Format is 'opponent:username:id' or 'opponent:username:unknown'
            parts = self.difficulty.split(':')
            if len(parts) >= 2:
                return parts[1]  # Return the username part
        return None

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    
    # User preferences
    theme = db.Column(db.String(20), default='default')  # For custom themes
    show_animations = db.Column(db.Boolean, default=True)  # For animations toggle
    play_sounds = db.Column(db.Boolean, default=True)  # For sound toggle
    
    # Game statistics
    total_games = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    total_game_time = db.Column(db.Integer, default=0)  # in seconds
    
    # Relationships
    games = db.relationship('Game', foreign_keys='Game.user_id', backref='user', lazy=True)
    sent_friendships = db.relationship('Friendship', 
                                      foreign_keys='Friendship.sender_id',
                                      backref='sender', 
                                      lazy='dynamic')
    received_friendships = db.relationship('Friendship', 
                                         foreign_keys='Friendship.receiver_id',
                                         backref='receiver', 
                                         lazy='dynamic')
    sent_messages = db.relationship('Message',
                                   foreign_keys='Message.sender_id',
                                   backref='sender',
                                   lazy='dynamic')
    received_messages = db.relationship('Message',
                                      foreign_keys='Message.receiver_id',
                                      backref='receiver',
                                      lazy='dynamic')
    notifications = db.relationship('Notification',
                                  backref='user',
                                  lazy='dynamic',
                                  order_by='desc(Notification.created_at)')
    
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
    
    def get_friends(self):
        """Get all accepted friends for this user"""
        sent = Friendship.query.filter_by(
            sender_id=self.id, status=FriendshipStatus.ACCEPTED.value
        ).all()
        received = Friendship.query.filter_by(
            receiver_id=self.id, status=FriendshipStatus.ACCEPTED.value
        ).all()
        
        friends = []
        for friendship in sent:
            friends.append(friendship.receiver)
        for friendship in received:
            friends.append(friendship.sender)
            
        return friends
    
    def get_friend_requests(self):
        """Get pending friend requests received by this user"""
        return Friendship.query.filter_by(
            receiver_id=self.id, status=FriendshipStatus.PENDING.value
        ).all()
    
    def has_unread_notifications(self):
        """Check if user has any unread notifications"""
        return Notification.query.filter_by(user_id=self.id, is_read=False).count() > 0
    
    def has_unread_messages(self):
        """Check if user has any unread messages"""
        return Message.query.filter_by(receiver_id=self.id, status=MessageStatus.UNREAD.value).count() > 0
    
    def is_friend_with(self, user_id):
        """Check if a user is friends with another user"""
        return Friendship.query.filter(
            ((Friendship.sender_id == self.id) & (Friendship.receiver_id == user_id)) |
            ((Friendship.sender_id == user_id) & (Friendship.receiver_id == self.id)),
            Friendship.status == FriendshipStatus.ACCEPTED.value
        ).first() is not None


class Friendship(db.Model):
    __tablename__ = 'friendships'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default=FriendshipStatus.PENDING.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Friendship {self.id}: {self.sender_id} -> {self.receiver_id} [{self.status}]>'


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default=MessageStatus.UNREAD.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender_id} -> {self.receiver_id}'
    
    def mark_as_read(self):
        self.status = MessageStatus.READ.value
        self.read_at = datetime.utcnow()


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # friend_request, game_invite, message, system
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    data = db.Column(db.Text, nullable=True)  # Optional JSON data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.type} for {self.user_id}>'
    
    def mark_as_read(self):
        self.is_read = True
