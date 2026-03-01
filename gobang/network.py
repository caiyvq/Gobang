# c:\Code\project\gobang\network.py

import socket
import json
import threading
import queue
from . import config
import time

class Network:
    """
    管理在线多人模式的网络通信。
    这个类可以作为服务器或客户端。
    """
    def __init__(self):
        self.client_socket = None
        self.server_socket = None
        self.connection = None
        self.accept_thread = None
        self.connection_queue = queue.Queue(maxsize=1)

        # 用于UDP广播的新增属性
        self.broadcast_socket = None
        self.broadcast_thread = None
        self.is_broadcasting = False

        # 用于UDP监听的新增属性
        self.listener_socket = None
        self.listener_thread = None
        self.is_listening = False
        self.discovered_hosts = set()
        self.hosts_lock = threading.Lock()

    def _listen_for_broadcasts(self):
        """
        在后台线程中运行，监听来自主机的UDP广播。
        """
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.listener_socket.bind(('', config.BROADCAST_PORT))
        except OSError as e:
            print(f"Error binding to broadcast port: {e}. Another app might be using it.")
            return

        print(f"Started listening for hosts on port {config.BROADCAST_PORT}")
        while self.is_listening:
            try:
                data, addr = self.listener_socket.recvfrom(1024)
                if data.decode('utf-8') == config.BROADCAST_SIGNAL:
                    host_ip = addr[0]
                    with self.hosts_lock:
                        if host_ip not in self.discovered_hosts:
                            print(f"Discovered host: {host_ip}")
                            self.discovered_hosts.add(host_ip)
            except OSError:
                # 当套接字被关闭时，会发生OSError
                break
            except Exception as e:
                if self.is_listening:
                    print(f"Error listening for broadcasts: {e}")
        
        self.listener_socket.close()
        self.listener_socket = None
        print("Stopped listening for hosts.")

    def start_listening_for_hosts(self):
        """启动客户端对主机广播的监听。"""
        if not self.is_listening:
            self.is_listening = True
            self.discovered_hosts.clear()
            self.listener_thread = threading.Thread(target=self._listen_for_broadcasts)
            self.listener_thread.daemon = True
            self.listener_thread.start()

    def stop_listening_for_hosts(self):
        """停止客户端对主机广播的监听。"""
        if self.is_listening:
            self.is_listening = False
            # 通过关闭套接字来解除recvfrom的阻塞
            if self.listener_socket:
                self.listener_socket.close()
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=1)
            self.listener_thread = None

    def get_discovered_hosts(self):
        """获取当前发现的主机列表。"""
        with self.hosts_lock:
            return list(self.discovered_hosts)

    def _broadcast_presence(self):
        """
        在后台线程中运行，定期发送UDP广播宣告主机存在。
        """
        # 创建一个新的UDP套接字用于广播
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 设置套接字选项以允许广播
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        broadcast_address = ('<broadcast>', config.BROADCAST_PORT)
        message = config.BROADCAST_SIGNAL.encode('utf-8')

        print(f"Starting to broadcast presence at {broadcast_address}")
        while self.is_broadcasting:
            try:
                self.broadcast_socket.sendto(message, broadcast_address)
                time.sleep(1) # 每秒广播一次
            except Exception as e:
                print(f"Error broadcasting presence: {e}")
                break
        
        if self.broadcast_socket:
            self.broadcast_socket.close()
            self.broadcast_socket = None
        print("Stopped broadcasting presence.")

    def start_broadcasting(self):
        """启动主机状态的UDP广播。"""
        if not self.is_broadcasting:
            self.is_broadcasting = True
            self.broadcast_thread = threading.Thread(target=self._broadcast_presence)
            self.broadcast_thread.daemon = True
            self.broadcast_thread.start()

    def stop_broadcasting(self):
        """停止主机状态的UDP广播。"""
        if self.is_broadcasting:
            self.is_broadcasting = False
            if self.broadcast_socket:
                # 尝试通过关闭套接字来优雅地中断sendto
                self.broadcast_socket.close()
            if self.broadcast_thread and self.broadcast_thread.is_alive():
                self.broadcast_thread.join(timeout=1.5) # 给予足够时间让线程退出
            self.broadcast_thread = None

    def _accept_connections(self):
        """
        在后台线程中运行，阻塞等待客户端连接。
        一旦连接成功，将连接对象放入队列。
        """
        try:
            conn, addr = self.server_socket.accept()
            self.connection = conn
            self.connection_queue.put(conn)
            print(f"Connection from {addr}")
        except OSError:
            # 当主线程关闭套接字时，accept()会引发OSError，这是正常行为
            print("Server socket closed, accepting thread is stopping.")
        except Exception as e:
            print(f"Error accepting connections: {e}")
            self.connection_queue.put(None)

    def start_server(self):
        """
        启动服务器以监听客户端连接。
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', config.PORT))
        self.server_socket.listen(1)
        print(f"Server started, listening on port {config.PORT}")

    def start_accepting(self):
        """启动一个后台线程来接受连接。"""
        if self.server_socket and not self.accept_thread:
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()

    def check_for_connection(self):
        """非阻塞地检查是否有新的连接。"""
        try:
            connection = self.connection_queue.get_nowait()
            return connection
        except queue.Empty:
            return None

    def connect_to_server(self, host):
        """
        作为客户端连接到服务器。
        """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, config.PORT))
        self.connection = self.client_socket
        print(f"Connected to server at {host}")

    def send_move(self, move):
        """
        将走棋数据（一个元组）编码并发送到对方。
        """
        if self.connection:
            try:
                self.connection.sendall(json.dumps(move).encode())
            except (ConnectionResetError, BrokenPipeError):
                print("Failed to send move, connection lost.")
                self.connection = None

    def receive_move(self):
        """
        接收走棋数据并解码。
        这是一个阻塞操作。
        """
        if self.connection:
            try:
                data = self.connection.recv(1024)
                if not data:
                    print("Connection closed by opponent.")
                    self.connection = None
                    return None
                return json.loads(data.decode())
            except (ConnectionResetError, json.JSONDecodeError, OSError):
                print("Failed to receive move, connection lost.")
                self.connection = None
                return None
        return None

    def close(self):
        """
        关闭所有活动的网络连接和套接字。
        """
        # 停止广播和监听
        self.stop_broadcasting()
        self.stop_listening_for_hosts()

        if self.connection:
            self.connection.close()
            self.connection = None
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        # 等待接受线程结束
        if self.accept_thread and self.accept_thread.is_alive():
            self.accept_thread.join(timeout=1)
        self.accept_thread = None