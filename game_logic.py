import numpy as np

PLAYER_PIECE = 1
AI_PIECE = 2

class Board:
    def __init__(self):
        self.board = np.zeros((6, 7), int)  # 6 rows and 7 columns

    def is_valid_location(self, col):
        return self.board[0][col] == 0

    def get_next_open_row(self, col):
        for row in range(5, -1, -1):  # Start from the bottom row
            if self.board[row][col] == 0:
                return row
        return -1

    def drop_piece(self, row, col, piece):
        self.board[row][col] = piece

    def winning_move(self, piece):
        # Check for winning conditions (horizontal, vertical, diagonal)
        for r in range(6):
            for c in range(7):
                if c + 3 < 7 and all(self.board[r][c + i] == piece for i in range(4)):  # Horizontal
                    return True
                if r + 3 < 6 and all(self.board[r + i][c] == piece for i in range(4)):  # Vertical
                    return True
                if r + 3 < 6 and c + 3 < 7 and all(self.board[r + i][c + i] == piece for i in range(4)):  # Diagonal \
                    return True
                if r - 3 >= 0 and c + 3 < 7 and all(self.board[r - i][c + i] == piece for i in range(4)):  # Diagonal /
                    return True
        return False

    def is_full(self):
        return np.all(self.board != 0)

    def to_list(self):
        return self.board.tolist()
