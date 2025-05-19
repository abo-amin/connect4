from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from models import Game
from dashboard import dashboard_bp

@dashboard_bp.route('/menu')
@login_required
def menu():
    return render_template('dashboard/menu.html')

@dashboard_bp.route('/')
@login_required
def index():
    return redirect(url_for('dashboard.menu'))

@dashboard_bp.route('/stats')
@login_required
def dashboard():
    recent_games = current_user.get_recent_games(10)
    
    last_game = Game.query.filter_by(user_id=current_user.id).order_by(Game.end_time.desc()).first()
    
    mode_stats = {
        'ai_vs_human': Game.query.filter_by(user_id=current_user.id, game_mode='ai_vs_human').count(),
        'human_vs_human': Game.query.filter_by(user_id=current_user.id, game_mode='human_vs_human').count(),
        'ai_vs_ai': Game.query.filter_by(user_id=current_user.id, game_mode='ai_vs_ai').count()
    }
    
    return render_template(
        'dashboard/dashboard.html', 
        recent_games=recent_games, 
        last_game=last_game,
        mode_stats=mode_stats
    )
