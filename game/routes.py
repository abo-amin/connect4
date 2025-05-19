from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
import json
import numpy as np

from game import game_bp
from models import db, Game
from game_logic import Board, PLAYER_PIECE, AI_PIECE
from ai import AIPlayer

# Define difficulty levels
DIFFICULTY_LEVELS = {
    'easy': 2,
    'medium': 4,
    'hard': 6
}

@game_bp.route('/')
@login_required
def game():
    return render_template('game/index.html')

@game_bp.route('/start', methods=['POST'])
@login_required
def start():
    data = request.get_json()
    session['mode'] = data['mode']
    
    # For human vs human, store opponent username instead of difficulty
    if data['mode'] == 'human_vs_human':
        session['opponent'] = data.get('opponent')
        session['difficulty'] = None
    else:
        session['difficulty'] = data.get('difficulty')
    
    session['game_start_time'] = datetime.utcnow().isoformat()
    session['move_count'] = 0
    
    return jsonify(success=True)

@game_bp.route('/move', methods=['POST'])
@login_required
def handle_move():
    data = request.get_json()
    board_obj = Board()
    board_obj.board = np.array(data.get('board', []))

    col = data.get('col')
    current_player = data.get('current_player', PLAYER_PIECE)
    mode = session.get('mode', 'ai_vs_human')
    difficulty = session.get('difficulty', 'medium')
    depth = DIFFICULTY_LEVELS.get(difficulty, 4)
    ai_player = AIPlayer(depth=depth)
    
    if 'move_count' in session:
        session['move_count'] = session.get('move_count', 0) + 1

    status = ''
    game_ended = False
    result = None

    if col is None and ((mode == 'ai_vs_human' and current_player == AI_PIECE) or mode == 'ai_vs_ai'):
        col, _ = ai_player.minimax(board_obj, depth, -np.inf, np.inf, True)

    if col is not None and board_obj.is_valid_location(col):
        row = board_obj.get_next_open_row(col)
        board_obj.drop_piece(row, col, current_player)

        if board_obj.winning_move(current_player):
            status = f'Player {current_player} wins!'
            game_ended = True
            if (current_player == PLAYER_PIECE and mode != 'ai_vs_ai') or \
               (mode == 'ai_vs_human' and current_player == AI_PIECE):
                result = 'win' if current_player == PLAYER_PIECE else 'loss'
            else:
                result = 'draw'
        elif board_obj.is_full():
            status = 'Draw!'
            game_ended = True
            result = 'draw'
        else:
            current_player = PLAYER_PIECE if current_player == AI_PIECE else AI_PIECE
            
    if game_ended and 'game_start_time' in session:
        save_game_results(board_obj, mode, difficulty, result, session.get('move_count', 0))
        session.pop('game_start_time', None)
        session.pop('move_count', None)

    response = {
        'board': board_obj.to_list(),
        'status': status,
        'next_player': current_player
    }
    return jsonify(response)

def save_game_results(board_obj, mode, difficulty, result, moves):
    if not current_user.is_authenticated:
        return
        
    try:
        start_time = datetime.fromisoformat(session.get('game_start_time'))
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # For human vs human games, store opponent username in the difficulty field
        if mode == 'human_vs_human':
            opponent_username = session.get('opponent')
            
            # Try to find the opponent user in the database
            from models import User
            opponent = User.query.filter_by(username=opponent_username).first()
            
            # Additional opponent info can be stored in the difficulty field
            if opponent:
                difficulty = f"opponent:{opponent.username}:{opponent.id}"
            else:
                difficulty = f"opponent:{opponent_username}:unknown"
        
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
        from flask import current_app
        current_app.logger.error(f"Error saving game: {e}")
        db.session.rollback()
