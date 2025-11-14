"""
WebSocket connection manager for real-time communication
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional
import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        async with self._lock:
            self.connections[client_id] = websocket
            self.client_info[client_id] = {
                "connected_at": asyncio.get_event_loop().time(),
                "last_ping": asyncio.get_event_loop().time(),
                "subscriptions": set()
            }
            
        logger.info("WebSocket connection established", client_id=client_id)
        
        # Send welcome message
        await self.send_message(client_id, {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "message": "Welcome to HelloVM AI Funland"
        })
        
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.connections:
            del self.connections[client_id]
            del self.client_info[client_id]
            logger.info("WebSocket connection closed", client_id=client_id)
            
    async def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        async with self._lock:
            for client_id in list(self.connections.keys()):
                await self.disconnect_client(client_id)
                
    async def disconnect_client(self, client_id: str):
        """Gracefully disconnect a specific client"""
        if client_id in self.connections:
            try:
                await self.send_message(client_id, {
                    "type": "connection",
                    "status": "disconnecting",
                    "message": "Server is shutting down"
                })
                await self.connections[client_id].close()
            except Exception as e:
                logger.warning("Error disconnecting client", client_id=client_id, error=str(e))
            finally:
                self.disconnect(client_id)
                
    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client"""
        if client_id not in self.connections:
            logger.warning("Client not connected", client_id=client_id)
            return False
            
        try:
            await self.connections[client_id].send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error("Failed to send message", client_id=client_id, error=str(e))
            self.disconnect(client_id)
            return False
            
    async def broadcast_message(self, message: dict, exclude_client: Optional[str] = None):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        
        async with self._lock:
            for client_id, websocket in self.connections.items():
                if client_id == exclude_client:
                    continue
                    
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error("Failed to broadcast message", client_id=client_id, error=str(e))
                    disconnected_clients.append(client_id)
                    
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
                
    async def broadcast_to_subscribers(self, channel: str, message: dict):
        """Broadcast to clients subscribed to a specific channel"""
        disconnected_clients = []
        
        async with self._lock:
            for client_id, info in self.client_info.items():
                if channel in info["subscriptions"]:
                    try:
                        await self.connections[client_id].send_text(json.dumps(message))
                    except Exception as e:
                        logger.error("Failed to send to subscriber", client_id=client_id, channel=channel, error=str(e))
                        disconnected_clients.append(client_id)
                        
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
                
    async def handle_message(self, client_id: str, data: str):
        """Handle incoming WebSocket message"""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "ping":
                await self.handle_ping(client_id)
            elif message_type == "subscribe":
                await self.handle_subscribe(client_id, message.get("channel"))
            elif message_type == "unsubscribe":
                await self.handle_unsubscribe(client_id, message.get("channel"))
            elif message_type == "chat":
                await self.handle_chat_message(client_id, message)
            elif message_type == "hardware":
                await self.handle_hardware_message(client_id, message)
            else:
                logger.warning("Unknown message type", client_id=client_id, type=message_type)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received", client_id=client_id, data=data)
        except Exception as e:
            logger.error("Error handling message", client_id=client_id, error=str(e))
            
    async def handle_ping(self, client_id: str):
        """Handle ping message"""
        if client_id in self.client_info:
            self.client_info[client_id]["last_ping"] = asyncio.get_event_loop().time()
            
        await self.send_message(client_id, {
            "type": "pong",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    async def handle_subscribe(self, client_id: str, channel: str):
        """Handle channel subscription"""
        if client_id not in self.client_info:
            return
            
        self.client_info[client_id]["subscriptions"].add(channel)
        
        await self.send_message(client_id, {
            "type": "subscription",
            "status": "subscribed",
            "channel": channel
        })
        
        logger.info("Client subscribed to channel", client_id=client_id, channel=channel)
        
    async def handle_unsubscribe(self, client_id: str, channel: str):
        """Handle channel unsubscription"""
        if client_id not in self.client_info:
            return
            
        self.client_info[client_id]["subscriptions"].discard(channel)
        
        await self.send_message(client_id, {
            "type": "subscription",
            "status": "unsubscribed",
            "channel": channel
        })
        
        logger.info("Client unsubscribed from channel", client_id=client_id, channel=channel)
        
    async def handle_chat_message(self, client_id: str, message: dict):
        """Handle chat message (placeholder for chat service integration)"""
        # This would be integrated with the ChatService
        logger.info("Chat message received", client_id=client_id, message=message)
        
        # Echo back for now (would be replaced with actual chat processing)
        await self.send_message(client_id, {
            "type": "chat_response",
            "original_message": message,
            "response": "This is a placeholder response from the chat service"
        })
        
    async def handle_hardware_message(self, client_id: str, message: dict):
        """Handle hardware-related message"""
        action = message.get("action")
        
        if action == "get_status":
            # This would be integrated with HardwareService
            await self.send_message(client_id, {
                "type": "hardware_status",
                "status": "placeholder_hardware_status"
            })
        elif action == "select_device":
            device_id = message.get("device_id")
            logger.info("Hardware device selection requested", client_id=client_id, device_id=device_id)
            
            await self.send_message(client_id, {
                "type": "hardware_selection",
                "device_id": device_id,
                "status": "selected"
            })
            
    async def start_health_check(self):
        """Start periodic health checks for all connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._check_client_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error", error=str(e))
                
    async def _check_client_health(self):
        """Check health of all connected clients"""
        current_time = asyncio.get_event_loop().time()
        disconnected_clients = []
        
        for client_id, info in self.client_info.items():
            last_ping = info.get("last_ping", 0)
            
            # If no ping for more than 2 minutes, consider disconnected
            if current_time - last_ping > 120:
                disconnected_clients.append(client_id)
                
        # Disconnect inactive clients
        for client_id in disconnected_clients:
            logger.info("Disconnecting inactive client", client_id=client_id)
            await self.disconnect_client(client_id)
            
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "clients": {
                client_id: {
                    "connected_at": info["connected_at"],
                    "last_ping": info["last_ping"],
                    "subscriptions": list(info["subscriptions"])
                }
                for client_id, info in self.client_info.items()
            }
        }