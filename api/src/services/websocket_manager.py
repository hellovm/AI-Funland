"""
WebSocket manager for handling real-time connections and message routing
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime
import structlog
from fastapi import WebSocket, WebSocketDisconnect

from .chat import ChatService
from .hardware import HardwareService
from .model import ModelService
from .websocket_integration import ChatStreamManager, VueIntegrationHelper

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self, chat_service: ChatService, hardware_service: HardwareService, model_service: ModelService):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, Dict[str, Any]] = {}
        self.chat_stream_manager = ChatStreamManager(chat_service, hardware_service, model_service)
        self.vue_helper = VueIntegrationHelper()
        
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
            
        self.active_connections[client_id] = websocket
        self.client_info[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "user_agent": None,
            "ip_address": None
        }
        
        logger.info("WebSocket connection established", client_id=client_id)
        
        # Send welcome message
        await self.send_message(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return client_id
        
    async def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        if client_id in self.active_connections:
            # Cancel any active streams for this client
            await self._cancel_client_streams(client_id)
            
            # Remove connection
            del self.active_connections[client_id]
            del self.client_info[client_id]
            
            logger.info("WebSocket connection closed", client_id=client_id)
            
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id not in self.active_connections:
            logger.warning("Client not connected", client_id=client_id)
            return
            
        try:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))
            
            # Update client activity
            self.client_info[client_id]["last_activity"] = datetime.now().isoformat()
            
        except WebSocketDisconnect:
            logger.warning("WebSocket disconnected while sending message", client_id=client_id)
            await self.disconnect(client_id)
        except Exception as e:
            logger.error("Failed to send message", client_id=client_id, error=str(e))
            
    async def broadcast_message(self, message: Dict[str, Any], exclude_client: Optional[str] = None):
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            if client_id == exclude_client:
                continue
                
            try:
                await websocket.send_text(json.dumps(message))
                self.client_info[client_id]["last_activity"] = datetime.now().isoformat()
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error("Failed to broadcast message", client_id=client_id, error=str(e))
                disconnected_clients.append(client_id)
                
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
            
    async def handle_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            message_type = message_data.get("type")
            
            # Update client activity
            self.client_info[client_id]["last_activity"] = datetime.now().isoformat()
            
            logger.debug("Handling WebSocket message", 
                        client_id=client_id, 
                        message_type=message_type)
            
            # Route message based on type
            if message_type == "chat_message":
                await self._handle_chat_message(client_id, message_data)
            elif message_type == "cancel_stream":
                await self._handle_cancel_stream(client_id, message_data)
            elif message_type == "get_hardware_status":
                await self._handle_hardware_status_request(client_id)
            elif message_type == "get_models":
                await self._handle_models_request(client_id)
            elif message_type == "ping":
                await self._handle_ping(client_id)
            else:
                logger.warning("Unknown message type", 
                             client_id=client_id, 
                             message_type=message_type)
                             
        except Exception as e:
            logger.error("Failed to handle message", 
                        client_id=client_id, 
                        error=str(e))
            await self.send_message(client_id, {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
    async def _handle_chat_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle chat message request"""
        session_id = message_data.get("session_id")
        message = message_data.get("message")
        model_id = message_data.get("model_id")
        
        if not session_id or not message:
            await self.send_message(client_id, {
                "type": "error",
                "error": "Missing session_id or message",
                "timestamp": datetime.now().isoformat()
            })
            return
            
        # Start chat stream
        stream_id = await self.chat_stream_manager.start_chat_stream(
            client_id, session_id, message, model_id
        )
        
        # Send acknowledgment
        await self.send_message(client_id, {
            "type": "chat_stream_started",
            "stream_id": stream_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
    async def _handle_cancel_stream(self, client_id: str, message_data: Dict[str, Any]):
        """Handle stream cancellation request"""
        stream_id = message_data.get("stream_id")
        
        if not stream_id:
            await self.send_message(client_id, {
                "type": "error",
                "error": "Missing stream_id",
                "timestamp": datetime.now().isoformat()
            })
            return
            
        success = await self.chat_stream_manager.cancel_stream(stream_id)
        
        await self.send_message(client_id, {
            "type": "stream_cancelled",
            "stream_id": stream_id,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
    async def _handle_hardware_status_request(self, client_id: str):
        """Handle hardware status request"""
        try:
            from ..services.hardware import HardwareService
            hardware_service = HardwareService()
            status = hardware_service.get_status()
            
            await self.send_message(client_id, {
                "type": "hardware_status",
                "hardware": status.dict() if hasattr(status, 'dict') else status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to get hardware status", error=str(e))
            await self.send_message(client_id, {
                "type": "error",
                "error": f"Failed to get hardware status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            
    async def _handle_models_request(self, client_id: str):
        """Handle models list request"""
        try:
            from ..services.model import ModelService
            model_service = ModelService()
            models = model_service.get_models()
            
            await self.send_message(client_id, {
                "type": "models_list",
                "models": models,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to get models", error=str(e))
            await self.send_message(client_id, {
                "type": "error",
                "error": f"Failed to get models: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            
    async def _handle_ping(self, client_id: str):
        """Handle ping message"""
        await self.send_message(client_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
        
    async def _cancel_client_streams(self, client_id: str):
        """Cancel all active streams for a client"""
        active_streams = self.chat_stream_manager.get_active_streams()
        
        for stream_id, stream_info in active_streams.items():
            if stream_id.startswith(f"{client_id}_"):
                await self.chat_stream_manager.cancel_stream(stream_id)
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "clients": [
                {
                    "client_id": client_id,
                    "connected_at": info["connected_at"],
                    "last_activity": info["last_activity"],
                    "user_agent": info.get("user_agent"),
                    "ip_address": info.get("ip_address")
                }
                for client_id, info in self.client_info.items()
            ],
            "active_streams": len(self.chat_stream_manager.active_streams)
        }


# WebSocket event handlers for FastAPI
class WebSocketHandler:
    """WebSocket event handlers for FastAPI integration"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        
    async def websocket_endpoint(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Main WebSocket endpoint"""
        client_id = await self.connection_manager.connect(websocket, client_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                    await self.connection_manager.handle_message(client_id, message_data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received", client_id=client_id, data=data)
                    await self.connection_manager.send_message(client_id, {
                        "type": "error",
                        "error": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected", client_id=client_id)
        except Exception as e:
            logger.error("WebSocket error", client_id=client_id, error=str(e))
        finally:
            await self.connection_manager.disconnect(client_id)
            
    async def send_stream_event(self, client_id: str, event_data: Dict[str, Any]):
        """Send stream event to specific client"""
        await self.connection_manager.send_message(client_id, event_data)
        
    async def broadcast_hardware_update(self, hardware_status: Dict[str, Any]):
        """Broadcast hardware status update to all clients"""
        await self.connection_manager.chat_stream_manager.broadcast_hardware_update(hardware_status)
        
    async def broadcast_model_update(self, model_info: Dict[str, Any]):
        """Broadcast model status update to all clients"""
        await self.connection_manager.chat_stream_manager.broadcast_model_update(model_info)