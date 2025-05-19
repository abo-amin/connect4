from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from models import db, User

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'qwnbsvhooiewrjfmarhio2163bviohadsbn'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connect4.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.example.com'  
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@example.com' 
    app.config['MAIL_PASSWORD'] = 'your-email-password'
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from auth import auth_bp
    from dashboard import dashboard_bp
    from game import game_bp
    from social import social_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(game_bp)  # No prefix for game routes to maintain compatibility
    app.register_blueprint(social_bp)  # Social features blueprint
    
    # Register a route for the root URL
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.menu'))
        return redirect(url_for('auth.login'))
    
    return app
