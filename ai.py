from game_logic import Board, PLAYER_PIECE, AI_PIECE
import random

class AIPlayer:
    def __init__(self, depth):
        self.depth = depth  # عمق البحث في الخوارزمية

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        valid_locations = [col for col in range(7) if board.is_valid_location(col)]
        
        # إذا كانت اللعبة انتهت أو وصلنا لعمق البحث المحدد
        if depth == 0 or not valid_locations:
            return None, self.evaluate(board)

        if maximizing_player:
            max_eval = -float('inf')
            best_col = random.choice(valid_locations)
            for col in valid_locations:
                row = board.get_next_open_row(col)
                board.drop_piece(row, col, AI_PIECE)
                evaluation = self.minimax(board, depth - 1, alpha, beta, False)[1]
                board.board[row][col] = 0
                if evaluation > max_eval:
                    max_eval = evaluation
                    best_col = col
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            return best_col, max_eval
        else:
            min_eval = float('inf')
            best_col = random.choice(valid_locations)
            for col in valid_locations:
                row = board.get_next_open_row(col)
                board.drop_piece(row, col, PLAYER_PIECE)
                evaluation = self.minimax(board, depth - 1, alpha, beta, True)[1]
                board.board[row][col] = 0
                if evaluation < min_eval:
                    min_eval = evaluation
                    best_col = col
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            return best_col, min_eval

    def evaluate(self, board):
        # تقييم اللوحة على أساس عدّ القطع المتصلة
        score = 0
        # تحليل الصفوف
        for r in range(6):
            for c in range(7):
                if c + 3 < 7:
                    # تحقق من الخطوط الأفقية
                    score += self.evaluate_line(board, r, c, 0, 1)
                if r + 3 < 6:
                    # تحقق من الخطوط العمودية
                    score += self.evaluate_line(board, r, c, 1, 0)
                if r + 3 < 6 and c + 3 < 7:
                    # تحقق من الخطوط القطرية
                    score += self.evaluate_line(board, r, c, 1, 1)
                if r - 3 >= 0 and c + 3 < 7:
                    # تحقق من الخطوط القطرية العكسية
                    score += self.evaluate_line(board, r, c, -1, 1)

        return score

    def evaluate_line(self, board, row, col, row_step, col_step):
        # تقييم سطر معين (أفقي، عمودي، قطري)
        score = 0
        player_count = 0
        ai_count = 0
        for i in range(4):
            r = row + i * row_step
            c = col + i * col_step
            if r >= 0 and r < 6 and c >= 0 and c < 7:
                if board.board[r][c] == AI_PIECE:
                    ai_count += 1
                elif board.board[r][c] == PLAYER_PIECE:
                    player_count += 1

        if ai_count == 4:
            score += 100
        elif player_count == 4:
            score -= 100
        elif ai_count == 3 and player_count == 0:
            score += 10
        elif player_count == 3 and ai_count == 0:
            score -= 10
        elif ai_count == 2 and player_count == 0:
            score += 1
        elif player_count == 2 and ai_count == 0:
            score -= 1

        return score
