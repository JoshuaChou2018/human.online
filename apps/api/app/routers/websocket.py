"""
WebSocket 路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import json

from app.core.config import settings
from app.core.websocket import manager
from app.core.database import AsyncSessionLocal
from app.services.chat import generate_streaming_response
from app.models.conversation import Conversation

router = APIRouter()


async def get_user_id_from_token(token: str) -> str:
    """从 JWT token 获取用户 ID"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError()
        return user_id
    except JWTError:
        return None


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket 聊天端点"""
    
    # 等待连接并验证
    await websocket.accept()
    
    # 接收认证消息
    try:
        auth_message = await websocket.receive_json()
        token = auth_message.get("token")
        
        if not token:
            await websocket.send_json({"type": "error", "message": "Authentication required"})
            await websocket.close()
            return
        
        user_id = await get_user_id_from_token(token)
        
        if not user_id:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close()
            return
        
        # 注册连接
        await manager.connect(websocket, user_id)
        manager.join_conversation(conversation_id, user_id)
        
        await websocket.send_json({"type": "connected", "message": "Connected successfully"})
        
        # 处理消息
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "message":
                    # 处理聊天消息
                    content = data.get("content", "")
                    avatar_id = data.get("avatar_id")
                    
                    # 广播用户消息
                    await manager.broadcast_to_conversation(
                        conversation_id,
                        {
                            "type": "message",
                            "sender_id": user_id,
                            "content": content,
                            "is_user": True
                        }
                    )
                    
                    # 生成 AI 响应
                    if avatar_id:
                        # 获取 avatar 信息
                        async with AsyncSessionLocal() as db:
                            from sqlalchemy import select
                            from app.models.avatar import Avatar
                            
                            result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
                            avatar = result.scalar_one_or_none()
                            
                            if avatar:
                                # 发送 typing 状态
                                await manager.broadcast_to_conversation(
                                    conversation_id,
                                    {
                                        "type": "typing",
                                        "avatar_id": avatar_id,
                                        "avatar_name": avatar.name
                                    }
                                )
                                
                                # 生成流式响应
                                messages = [{"role": "user", "content": content}]
                                
                                full_response = ""
                                async for chunk in generate_streaming_response(avatar, messages):
                                    full_response += chunk
                                    await manager.broadcast_to_conversation(
                                        conversation_id,
                                        {
                                            "type": "stream",
                                            "avatar_id": avatar_id,
                                            "chunk": chunk,
                                            "is_end": False
                                        }
                                    )
                                
                                # 发送完成消息
                                await manager.broadcast_to_conversation(
                                    conversation_id,
                                    {
                                        "type": "stream",
                                        "avatar_id": avatar_id,
                                        "content": full_response,
                                        "is_end": True
                                    }
                                )
                
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif message_type == "leave":
                    manager.leave_conversation(conversation_id, user_id)
                    break
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        # 清理连接
        manager.disconnect(websocket, user_id)
        manager.leave_conversation(conversation_id, user_id)


@router.websocket("/ws/simulation/{simulation_id}")
async def websocket_simulation(websocket: WebSocket, simulation_id: str):
    """WebSocket 模拟进度端点"""
    
    await websocket.accept()
    
    try:
        # 接收认证
        auth_message = await websocket.receive_json()
        token = auth_message.get("token")
        
        user_id = await get_user_id_from_token(token)
        
        if not user_id:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close()
            return
        
        await manager.connect(websocket, user_id)
        
        # 监听模拟进度
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif data.get("type") == "subscribe":
                    # 订阅特定模拟的更新
                    await websocket.send_json({
                        "type": "subscribed",
                        "simulation_id": simulation_id
                    })
            
            except WebSocketDisconnect:
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Simulation WebSocket error: {e}")
    
    finally:
        if user_id:
            manager.disconnect(websocket, user_id)


async def safe_send_json(websocket: WebSocket, data: dict):
    """安全发送 JSON 消息，处理连接已关闭的情况"""
    try:
        await websocket.send_json(data)
    except RuntimeError as e:
        # 连接已关闭，忽略
        if "close message" in str(e) or "disconnect" in str(e).lower():
            pass
        else:
            raise
    except Exception:
        # 其他发送错误，忽略
        pass


@router.websocket("/ws/weaving/{avatar_id}")
async def websocket_weaving(websocket: WebSocket, avatar_id: str):
    """WebSocket 编织进度监听端点"""
    
    await websocket.accept()
    
    user_id = None
    connection_active = True
    
    try:
        # 接收认证
        auth_message = await websocket.receive_json()
        token = auth_message.get("token")
        
        user_id = await get_user_id_from_token(token)
        
        if not user_id:
            await safe_send_json(websocket, {"type": "error", "message": "Invalid token"})
            await websocket.close()
            return
        
        # 验证用户是否有权访问这个 avatar
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.models.avatar import Avatar
            
            result = await db.execute(
                select(Avatar).where(
                    Avatar.id == avatar_id,
                    Avatar.user_id == user_id
                )
            )
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                await safe_send_json(websocket, {"type": "error", "message": "Avatar not found or access denied"})
                await websocket.close()
                return
        
        # 注册连接
        if user_id not in manager.active_connections:
            manager.active_connections[user_id] = []
        manager.active_connections[user_id].append(websocket)
        manager.join_weaving(avatar_id, user_id)
        
        await safe_send_json(websocket, {
            "type": "connected",
            "message": "Weaving progress WebSocket connected",
            "avatar_id": avatar_id
        })
        
        # 发送当前进度
        async with AsyncSessionLocal() as db:
            from app.models.weaving_progress import WeavingProgress
            
            result = await db.execute(
                select(WeavingProgress).where(WeavingProgress.avatar_id == avatar_id)
            )
            progress = result.scalar_one_or_none()
            
            if progress:
                await safe_send_json(websocket, {
                    "type": "weaving_progress",
                    **progress.to_dict()
                })
        
        # 监听客户端消息
        while connection_active:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await safe_send_json(websocket, {"type": "pong"})
                
                elif msg_type == "request_progress":
                    # 客户端请求最新进度
                    async with AsyncSessionLocal() as db:
                        from app.models.weaving_progress import WeavingProgress
                        
                        result = await db.execute(
                            select(WeavingProgress).where(WeavingProgress.avatar_id == avatar_id)
                        )
                        progress = result.scalar_one_or_none()
                        
                        if progress:
                            await safe_send_json(websocket, {
                                "type": "weaving_progress",
                                **progress.to_dict()
                            })
                
                elif msg_type == "close":
                    break
            
            except WebSocketDisconnect:
                connection_active = False
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Weaving error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        connection_active = False
        if user_id:
            manager.leave_weaving(avatar_id, user_id)
            manager.disconnect(websocket, user_id)
