#!/usr/bin/env python3
"""
实时监控Web界面

使用Flask和Socket.IO提供实时监控界面，显示系统和进程的监控数据。
"""

import os
import json
import threading
import time
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

class MonitorWebApp:
    def __init__(self, port=5000):
        """
        初始化Web应用
        
        Args:
            port: Web服务器端口号
        """
        self.port = port
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.monitor_data = None
        self.thread = None
        self.thread_stop_event = threading.Event()
        
        # 确保模板目录存在
        os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
        
        # 设置路由
        self._setup_routes()
        
    def _setup_routes(self):
        """
        设置Flask路由
        """
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/data')
        def get_data():
            if self.monitor_data:
                return jsonify(self.monitor_data)
            return jsonify({})
        
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected')
            if not self.thread or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._background_thread)
                self.thread.daemon = True
                self.thread.start()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')
    
    def _background_thread(self):
        """
        后台线程，用于向客户端发送实时数据
        """
        while not self.thread_stop_event.is_set():
            if self.monitor_data:
                self.socketio.emit('update_data', json.dumps(self.monitor_data))
            time.sleep(1)
    
    def update_data(self, data):
        """
        更新监控数据
        
        Args:
            data: 新的监控数据
        """
        self.monitor_data = data
    
    def start(self):
        """
        启动Web服务器
        """
        print(f"Starting web server on port {self.port}")
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
    
    def stop(self):
        """
        停止Web服务器
        """
        self.thread_stop_event.set()
        print("Web server stopped")


def create_web_app(port=5000):
    """
    创建并返回一个MonitorWebApp实例
    
    Args:
        port: Web服务器端口号
    
    Returns:
        MonitorWebApp实例
    """
    return MonitorWebApp(port=port)
