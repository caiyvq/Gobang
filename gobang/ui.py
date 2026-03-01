# c:\Code\project\gobang\ui.py

import pygame
from . import config

class UI:
    """
    处理所有图形界面的绘制和用户输入处理。
    """
    def __init__(self, screen):
        self.screen = screen
        
        # 尝试加载支持中文的字体，如果找不到则回退到默认字体
        try:
            self.turn_font = pygame.font.Font("simhei", config.TURN_INFO_FONT_SIZE)
        except FileNotFoundError:
            self.turn_font = pygame.font.Font(None, config.TURN_INFO_FONT_SIZE)
            
        self.end_game_font = pygame.font.Font(None, config.FONT_SIZE)
        self.menu_font = pygame.font.Font(None, config.MENU_FONT_SIZE)
        self.input_font = pygame.font.Font(None, 32)
        
        # 主菜单按钮区域
        self.local_button_rect = pygame.Rect((config.SCREEN_WIDTH - config.BUTTON_WIDTH) // 2, config.LOCAL_GAME_BUTTON_Y, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        self.create_button_rect = pygame.Rect((config.SCREEN_WIDTH - config.BUTTON_WIDTH) // 2, config.CREATE_GAME_BUTTON_Y, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        self.join_button_rect = pygame.Rect((config.SCREEN_WIDTH - config.BUTTON_WIDTH) // 2, config.JOIN_GAME_BUTTON_Y, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        
        # 返回主菜单按钮区域
        self.return_button_rect = pygame.Rect((config.SCREEN_WIDTH - config.RETURN_BUTTON_WIDTH) // 2, config.RETURN_BUTTON_Y, config.RETURN_BUTTON_WIDTH, config.RETURN_BUTTON_HEIGHT)

        # 取消等待按钮
        self.cancel_button_rect = pygame.Rect((config.SCREEN_WIDTH - config.RETURN_BUTTON_WIDTH) // 2, config.RETURN_BUTTON_Y, config.RETURN_BUTTON_WIDTH, config.RETURN_BUTTON_HEIGHT)

        # IP输入框
        self.input_box_rect = pygame.Rect((config.SCREEN_WIDTH - 300) // 2, config.SCREEN_HEIGHT // 2, 300, 40)
        self.input_text = ''
        self.input_active = False

        # 房间列表相关UI元素
        self.host_list_buttons = []
        self.host_list_font = pygame.font.Font(None, config.MENU_FONT_SIZE)
        self.host_list_title_font = pygame.font.Font(None, 40)

    def draw_host_list(self, hosts):
        """绘制一个可点击的主机IP列表。"""
        self.screen.fill(config.BOARD_COLOR)
        self.host_list_buttons.clear()

        # 绘制标题
        title_text = "Searching for LAN games..." if not hosts else "Click an IP to join:"
        title_surf = self.host_list_title_font.render(title_text, True, config.FONT_COLOR)
        title_rect = title_surf.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4))
        self.screen.blit(title_surf, title_rect)

        if not hosts:
            no_hosts_text = "No games found yet."
            no_hosts_surf = self.host_list_font.render(no_hosts_text, True, config.FONT_COLOR)
            no_hosts_rect = no_hosts_surf.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2))
            self.screen.blit(no_hosts_surf, no_hosts_rect)
        else:
            # 绘制主机列表按钮
            for i, host_ip in enumerate(hosts):
                button_y = config.SCREEN_HEIGHT // 2 + i * (config.BUTTON_HEIGHT + 10)
                button_rect = pygame.Rect((config.SCREEN_WIDTH - config.BUTTON_WIDTH) // 2, button_y, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
                self._draw_button(button_rect, host_ip)
                self.host_list_buttons.append((button_rect, host_ip))
        
        # 始终绘制返回按钮
        self._draw_button(self.cancel_button_rect, "Back to Menu")

    def get_host_choice(self, pos):
        """检查是否有主机IP按钮被点击。"""
        for rect, host_ip in self.host_list_buttons:
            if rect.collidepoint(pos):
                return host_ip
        return None

    def draw_board(self):
        """绘制游戏棋盘网格。"""
        self.screen.fill(config.BOARD_COLOR)
        for i in range(config.BOARD_SIZE):
            pygame.draw.line(self.screen, config.BLACK, (config.START_X, config.START_Y + i * config.GRID_SIZE), (config.START_X + (config.BOARD_SIZE - 1) * config.GRID_SIZE, config.START_Y + i * config.GRID_SIZE), 1)
            pygame.draw.line(self.screen, config.BLACK, (config.START_X + i * config.GRID_SIZE, config.START_Y), (config.START_X + i * config.GRID_SIZE, config.START_Y + (config.BOARD_SIZE - 1) * config.GRID_SIZE), 1)

    def draw_pieces(self, board):
        """根据棋盘状态绘制所有棋子。"""
        for row in range(config.BOARD_SIZE):
            for col in range(config.BOARD_SIZE):
                player = board[row][col]
                if player != 0:
                    center = (config.START_X + col * config.GRID_SIZE, config.START_Y + row * config.GRID_SIZE)
                    color = config.BLACK if player == config.PLAYER_BLACK else config.WHITE
                    pygame.draw.circle(self.screen, color, center, config.PIECE_RADIUS)

    def pixel_to_grid(self, pixel_x, pixel_y):
        """将屏幕像素坐标转换为棋盘网格坐标。"""
        row = round((pixel_y - config.START_Y) / config.GRID_SIZE)
        col = round((pixel_x - config.START_X) / config.GRID_SIZE)
        return row, col

    def show_message(self, text):
        """在屏幕中央显示游戏结束信息。"""
        text_surface = self.end_game_font.render(text, True, config.FONT_COLOR)
        text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

    def draw_menu(self):
        """绘制主菜单界面和按钮。"""
        self.screen.fill(config.BOARD_COLOR)
        self._draw_button(self.local_button_rect, "Local Game")
        self._draw_button(self.create_button_rect, "Create Online Game")
        self._draw_button(self.join_button_rect, "Join Online Game")

    def _draw_button(self, rect, text):
        """用于绘制单个按钮的辅助函数。"""
        pygame.draw.rect(self.screen, config.BUTTON_COLOR, rect)
        text_surf = self.menu_font.render(text, True, config.BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def get_menu_choice(self, pos):
        """根据鼠标点击位置返回对应的游戏模式。"""
        if self.local_button_rect.collidepoint(pos):
            return "local"
        if self.create_button_rect.collidepoint(pos):
            return "create"
        if self.join_button_rect.collidepoint(pos):
            return "join"
        return None

    def draw_return_button(self):
        """在屏幕底部绘制“返回主菜单”按钮。"""
        self._draw_button(self.return_button_rect, "Return to Main Menu")

    def get_return_button_click(self, pos):
        """检查鼠标点击是否在“返回主菜单”按钮上。"""
        return self.return_button_rect.collidepoint(pos)

    def get_cancel_button_click(self, pos):
        """检查鼠标点击是否在“取消”按钮上。"""
        return self.cancel_button_rect.collidepoint(pos)

    def draw_turn_indicator(self, text):
        """在屏幕顶部中央绘制回合指示器。"""
        text_surface = self.turn_font.render(text, True, config.TURN_INFO_COLOR)
        text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.TURN_INFO_Y))
        self.screen.blit(text_surface, text_rect)

    def draw_host_info(self, ip_address):
        """在屏幕上显示主机IP地址。"""
        self.screen.fill(config.BOARD_COLOR)
        
        line1_text = "Waiting for player to join..."
        line2_text = f"Your IP is: {ip_address}"
        
        line1_surf = self.menu_font.render(line1_text, True, config.FONT_COLOR)
        line1_rect = line1_surf.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 30))
        
        line2_surf = self.menu_font.render(line2_text, True, config.FONT_COLOR)
        line2_rect = line2_surf.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 30))
        
        self.screen.blit(line1_surf, line1_rect)
        self.screen.blit(line2_surf, line2_rect)

        self._draw_button(self.cancel_button_rect, "Cancel")

    def draw_input_box(self):
        """绘制一个文本输入框，用于输入IP。"""
        prompt_text = "Enter Host IP and Press Enter"
        prompt_surface = self.menu_font.render(prompt_text, True, config.FONT_COLOR)
        prompt_rect = prompt_surface.get_rect(center=(config.SCREEN_WIDTH // 2, self.input_box_rect.y - 30))
        self.screen.blit(prompt_surface, prompt_rect)

        # 根据是否激活来改变输入框颜色
        color = config.FONT_COLOR if self.input_active else (100, 100, 100)
        pygame.draw.rect(self.screen, color, self.input_box_rect, 2)
        
        text_surface = self.input_font.render(self.input_text, True, config.FONT_COLOR)
        self.screen.blit(text_surface, (self.input_box_rect.x + 5, self.input_box_rect.y + 5))

    def handle_input_event(self, event):
        """处理文本输入框的事件，返回输入的文本或None。"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.input_box_rect.collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False
        
        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                entered_text = self.input_text
                # 重置输入框状态以便下次使用
                self.input_text = ''
                self.input_active = False
                return entered_text
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                # 仅接受数字和点
                if event.unicode.isdigit() or event.unicode == '.':
                    self.input_text += event.unicode
        return None