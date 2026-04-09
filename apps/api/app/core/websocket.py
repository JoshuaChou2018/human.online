"""
WebSocket 连接管理器
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 用户 ID -> WebSocket 连接列表
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # 对话 ID -> 用户 ID 集合
        self.conversation_connections: Dict[str, Set[str]] = {}
        # 编织会话: avatar_id -> 用户 ID 集合
        self.weaving_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """建立新连接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    def join_conversation(self, conversation_id: str, user_id: str):
        """加入对话"""
        if conversation_id not in self.conversation_connections:
            self.conversation_connections[conversation_id] = set()
        
        self.conversation_connections[conversation_id].add(user_id)
    
    def leave_conversation(self, conversation_id: str, user_id: str):
        """离开对话"""
        if conversation_id in self.conversation_connections:
            self.conversation_connections[conversation_id].discard(user_id)
            
            if not self.conversation_connections[conversation_id]:
                del self.conversation_connections[conversation_id]
    
    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给指定用户"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: dict, exclude_user: str = None):
        """广播消息给对话中的所有用户"""
        if conversation_id not in self.conversation_connections:
            return
        
        for user_id in self.conversation_connections[conversation_id]:
            if user_id != exclude_user:
                await self.send_to_user(user_id, message)
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected_users = []
        
        for user_id, connections in self.active_connections.items():
            disconnected = []
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                connections.remove(conn)
            
            if not connections:
                disconnected_users.append(user_id)
        
        # 清理断开的用户
        for user_id in disconnected_users:
            del self.active_connections[user_id]
    
    def join_weaving(self, avatar_id: str, user_id: str):
        """加入编织会话监听"""
        if avatar_id not in self.weaving_connections:
            self.weaving_connections[avatar_id] = set()
        self.weaving_connections[avatar_id].add(user_id)
    
    def leave_weaving(self, avatar_id: str, user_id: str):
        """离开编织会话监听"""
        if avatar_id in self.weaving_connections:
            self.weaving_connections[avatar_id].discard(user_id)
            if not self.weaving_connections[avatar_id]:
                del self.weaving_connections[avatar_id]
    
    async def broadcast_to_avatar_weaving(self, avatar_id: str, message: dict):
        """推送编织进度给订阅的用户"""
        if avatar_id not in self.weaving_connections:
            return
        
        message["type"] = "weaving_progress"
        message["avatar_id"] = avatar_id
        
        for user_id in self.weaving_connections[avatar_id]:
            await self.send_to_user(user_id, message)


# 全局连接管理器实例
manager = ConnectionManager()
