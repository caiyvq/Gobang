# c:\Code\project\gobang\game_logic.py

from . import config

class Game:
    """
    管理游戏状态和逻辑，例如落子和检查胜利者。
    """
    def __init__(self):
        self.board = [[0] * config.BOARD_SIZE for _ in range(config.BOARD_SIZE)]
        self.current_player = config.PLAYER_BLACK
        self.game_over = False
        self.winner = None

    def is_valid_move(self, row, col):
        """检查一步棋是否有效（在边界内且落在空位上）。"""
        return 0 <= row < config.BOARD_SIZE and 0 <= col < config.BOARD_SIZE and self.board[row][col] == 0

    def place_piece(self, row, col):
        """在棋盘上落子。"""
        if self.is_valid_move(row, col):
            self.board[row][col] = self.current_player
            return True
        return False

    def switch_player(self):
        """切换当前玩家。"""
        self.current_player = config.PLAYER_WHITE if self.current_player == config.PLAYER_BLACK else config.PLAYER_BLACK

    def check_win(self, row, col):
        """
        检查最后一步棋是否导致胜利。
        它会检查水平、垂直以及两条对角线方向。
        """
        player = self.board[row][col]
        if player == 0:
            return False

        # 需要检查的方向：水平、垂直、主对角线、副对角线
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # 检查正方向
            for i in range(1, 5):
                r, c = row + i * dr, col + i * dc
                if 0 <= r < config.BOARD_SIZE and 0 <= c < config.BOARD_SIZE and self.board[r][c] == player:
                    count += 1
                else:
                    break
            # 检查反方向
            for i in range(1, 5):
                r, c = row - i * dr, col - i * dc
                if 0 <= r < config.BOARD_SIZE and 0 <= c < config.BOARD_SIZE and self.board[r][c] == player:
                    count += 1
                else:
                    break
            
            if count >= 5:
                self.game_over = True
                self.winner = player
                return True
        return False

    def run_move(self, row, col):
        """
        执行单步操作：落子，检查胜利，然后切换玩家。
        """
        if self.is_valid_move(row, col):
            self.place_piece(row, col)
            if self.check_win(row, col):
                # 游戏结束，胜利者在 check_win 中设置
                pass
            else:
                self.switch_player()