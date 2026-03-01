# c:\Code\project\gobang\main.py

import pygame
import sys
from . import config
import threading
import queue
import socket
from .game_logic import Game
from .ui import UI
from .network import Network

def local_game_loop(screen, ui):
    """本地双人对战的游戏循环。"""
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # 1 代表鼠标左键
                x, y = event.pos
                if not game.game_over:
                    row, col = ui.pixel_to_grid(x, y)
                    game.run_move(row, col)
                else:
                    if ui.get_return_button_click((x, y)):
                        return

        ui.draw_board()
        ui.draw_pieces(game.board)

        if not game.game_over:
            turn_text = "Black's Turn" if game.current_player == config.PLAYER_BLACK else "White's Turn"
            ui.draw_turn_indicator(turn_text)
        elif game.winner:
            winner_text = "Black Wins!" if game.winner == config.PLAYER_BLACK else "White Wins!"
            ui.show_message(winner_text)
            ui.draw_return_button()

        pygame.display.flip()

def network_receive_worker(net, move_queue):
    """
    工作线程函数，用于阻塞等待网络中的走棋信息。
    将接收到的走棋放入队列，供主线程处理。
    """
    while True:
        move = net.receive_move()
        move_queue.put(move)
        if move is None:  # 表示连接已关闭
            break

def get_local_ip():
    """获取本机的局域网IP地址。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 连接到一个公共DNS服务器以找到出口IP，但实际上不发送任何数据
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1' # 如果无法获取，则回退到本地地址
    finally:
        s.close()
    return ip

def online_game_loop(screen, ui, is_host):
    """具有非阻塞UI的在线多人游戏循环。"""
    game = Game()
    net = Network()
    
    try:
        if is_host:
            host_ip = get_local_ip()
            net.start_server()
            net.start_accepting()
            net.start_broadcasting() # 开始广播主机状态
            
            # 非阻塞的等待循环
            waiting_for_connection = True
            while waiting_for_connection:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        net.close()
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if ui.get_cancel_button_click(event.pos):
                            net.close()
                            return # 返回主菜单

                # 检查是否有客户端连接
                connection = net.check_for_connection()
                if connection:
                    waiting_for_connection = False
                    my_turn = True
                elif connection is None and not net.connection_queue.empty(): # 明确的失败信号
                    raise ConnectionAbortedError("Failed to accept connection.")

                ui.draw_host_info(host_ip)
                pygame.display.flip()
                pygame.time.wait(100) # 短暂等待以降低CPU使用率
            
            if not net.connection: # 如果循环结束但没有连接（例如，取消了）
                return

        else:
            # 客户端：搜索并加入游戏
            net.start_listening_for_hosts()
            host_ip_to_join = None
            searching_for_host = True
            while searching_for_host:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        net.close()
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # 检查是否点击了返回按钮
                        if ui.get_cancel_button_click(event.pos):
                            searching_for_host = False
                            net.stop_listening_for_hosts()
                            return # 返回主菜单
                        
                        # 检查是否点击了某个主机
                        chosen_ip = ui.get_host_choice(event.pos)
                        if chosen_ip:
                            host_ip_to_join = chosen_ip
                            searching_for_host = False

                # 绘制主机列表
                discovered_hosts = net.get_discovered_hosts()
                ui.draw_host_list(discovered_hosts)
                pygame.display.flip()
                pygame.time.wait(100)

            net.stop_listening_for_hosts()

            if not host_ip_to_join:
                return # 如果没有选择主机就返回了

            ui.draw_board()
            ui.show_message(f"Connecting to {host_ip_to_join}...")
            pygame.display.flip()
            net.connect_to_server(host_ip_to_join)
            my_turn = False
    except Exception as e:
        print(f"Network connection failed: {e}")
        # 在屏幕上显示错误信息
        ui.draw_board()
        ui.show_message(f"Failed: {e}")
        pygame.display.flip()
        pygame.time.wait(3000)
        net.close() # 确保在失败时关闭网络资源
        return

    move_queue = queue.Queue()
    receiver_thread = threading.Thread(target=network_receive_worker, args=(net, move_queue))
    receiver_thread.daemon = True
    receiver_thread.start()

    temp_message = None
    temp_message_time = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # 1 代表鼠标左键
                x, y = event.pos
                if my_turn and not game.game_over:
                    row, col = ui.pixel_to_grid(x, y)
                    if game.is_valid_move(row, col):
                        game.run_move(row, col)
                        net.send_move((row, col))
                        my_turn = False
                elif not my_turn and not game.game_over:
                    row, col = ui.pixel_to_grid(x, y)
                    if 0 <= row < config.BOARD_SIZE and 0 <= col < config.BOARD_SIZE:
                        temp_message = "Not your turn"
                        temp_message_time = pygame.time.get_ticks()
                elif game.game_over:
                    if ui.get_return_button_click((x, y)):
                        running = False

        try:
            move = move_queue.get_nowait()
            if move:
                game.run_move(move[0], move[1])
                my_turn = True
            else:
                if not game.game_over:
                    print("Opponent has disconnected. Game over.")
                    game.game_over = True
        except queue.Empty:
            pass

        ui.draw_board()
        ui.draw_pieces(game.board)

        if not game.game_over:
            display_text = ""
            if temp_message and pygame.time.get_ticks() - temp_message_time < 1500:
                display_text = temp_message
            else:
                temp_message = None
                display_text = "Your Turn" if my_turn else "Opponent's Turn"
            ui.draw_turn_indicator(display_text)
        elif game.winner:
            winner_text = "You Win!" if my_turn != (game.winner == config.PLAYER_BLACK) else "You Lose!"
            ui.show_message(winner_text)
            ui.draw_return_button()
        elif game.game_over:
            ui.show_message("Opponent disconnected")
            ui.draw_return_button()

        pygame.display.flip()

    net.close()

def main_menu(screen, ui):
    """显示主菜单并处理用户选择。"""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # 1 代表鼠标左键
                choice = ui.get_menu_choice(event.pos)
                if choice == "local":
                    local_game_loop(screen, ui)
                elif choice == "create":
                    online_game_loop(screen, ui, is_host=True)
                elif choice == "join":
                    online_game_loop(screen, ui, is_host=False)

        ui.draw_menu()
        pygame.display.flip()

def main():
    """程序的主入口点。"""
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Gobang")

    # 设置窗口图标
    # try:
    #     icon_image = pygame.image.load("gobang/icon.png")
    #     pygame.display.set_icon(icon_image)
    # except pygame.error as e:
    #     print(f"Icon not found, using default icon. Error: {e}")

    ui = UI(screen)
    
    main_menu(screen, ui)

if __name__ == '__main__':
    main()