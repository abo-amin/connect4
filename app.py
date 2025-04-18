from flask import Flask, render_template, request, jsonify, session
from game_logic import Board, PLAYER_PIECE, AI_PIECE
from ai import AIPlayer
import numpy as np

app = Flask(__name__)
app.secret_key = 'secret_key'

# Map difficulty levels to search depths
DIFFICULTY_LEVELS = {
    'easy': 2,
    'medium': 4,
    'hard': 6
}

@app.route('/')
def menu():
    return render_template('menu.html')

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json()
    session['mode'] = data['mode']
    session['difficulty'] = data['difficulty']
    return jsonify(success=True)

@app.route('/game')
def game():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
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

    status = ''

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
        elif board_obj.is_full():
            status = 'Draw!'
        else:
            # Switch player
            current_player = PLAYER_PIECE if current_player == AI_PIECE else AI_PIECE

    # Return updated board and status
    response = {
        'board': board_obj.to_list(),
        'status': status,
        'next_player': current_player
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)