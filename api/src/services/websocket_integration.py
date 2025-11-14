"""
WebSocket integration service for real-time chat streaming
Integrates with the Vue frontend for seamless real-time communication
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable
import structlog
from datetime import datetime

from ..services.chat import ChatService
from ..services.hardware import HardwareService
from ..services.model import ModelService

logger = structlog.get_logger(__name__)


class ChatStreamManager:
    """Manages real-time chat streaming with WebSocket integration"""
    
    def __init__(self, chat_service: ChatService, hardware_service: HardwareService, model_service: ModelService):
        self.chat_service = chat_service
        self.hardware_service = hardware_service
        self.model_service = model_service
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.stream_callbacks: Dict[str, Callable] = {}
        
    async def start_chat_stream(self, client_id: str, session_id: str, message: str, model_id: Optional[str] = None) -> str:
        """Start a real-time chat streaming session"""
        stream_id = f"{client_id}_{session_id}_{int(datetime.now().timestamp() * 1000)}"
        
        try:
            # Create streaming task
            stream_task = asyncio.create_task(
                self._stream_chat_response(client_id, session_id, message, model_id, stream_id)
            )
            
            self.active_streams[stream_id] = stream_task
            
            logger.info("Chat stream started", 
                       stream_id=stream_id, 
                       client_id=client_id, 
                       session_id=session_id,
                       model_id=model_id)
            
            return stream_id
            
        except Exception as e:
            logger.error("Failed to start chat stream", 
                        stream_id=stream_id, 
                        error=str(e))
            raise
            
    async def _stream_chat_response(self, client_id: str, session_id: str, message: str, model_id: Optional[str], stream_id: str):
        """Stream chat response in real-time"""
        try:
            # Get current hardware and model info
            hardware_status = self.hardware_service.get_status()
            model_info = None
            if model_id:
                model_info = self.model_service.get_model(model_id)
                
            # Send stream start notification
            await self._send_stream_event(client_id, {
                "type": "chat_stream_start",
                "stream_id": stream_id,
                "session_id": session_id,
                "hardware": hardware_status.primary_device.name if hardware_status.primary_device else "cpu",
                "model": model_info.get("name") if model_info else "default"
            })
            
            # Simulate streaming response (would be replaced with actual LLM streaming)
            response_chunks = await self._generate_streaming_response(message, model_id, hardware_status)
            
            full_response = ""
            for i, chunk in enumerate(response_chunks):
                full_response += chunk
                
                # Send chunk to client
                await self._send_stream_event(client_id, {
                    "type": "chat_stream_chunk",
                    "stream_id": stream_id,
                    "chunk": chunk,
                    "progress": (i + 1) / len(response_chunks),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Small delay to simulate real streaming
                await asyncio.sleep(0.1)
                
            # Send stream completion
            await self._send_stream_event(client_id, {
                "type": "chat_stream_complete",
                "stream_id": stream_id,
                "full_response": full_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Store the complete response in chat service
            await self._store_chat_response(session_id, message, full_response, model_id, hardware_status)
            
            logger.info("Chat stream completed", 
                       stream_id=stream_id, 
                       response_length=len(full_response))
                       
        except asyncio.CancelledError:
            logger.info("Chat stream cancelled", stream_id=stream_id)
            await self._send_stream_event(client_id, {
                "type": "chat_stream_cancelled",
                "stream_id": stream_id
            })
            
        except Exception as e:
            logger.error("Chat stream error", stream_id=stream_id, error=str(e))
            await self._send_stream_event(client_id, {
                "type": "chat_stream_error",
                "stream_id": stream_id,
                "error": str(e)
            })
            
        finally:
            # Clean up stream
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                
    async def _generate_streaming_response(self, message: str, model_id: Optional[str], hardware_status) -> list[str]:
        """Generate streaming response chunks (placeholder implementation)"""
        # This would be replaced with actual LLM streaming logic
        # For now, simulate intelligent response based on message content
        
        if "hello" in message.lower() or "hi" in message.lower():
            return [
                "Hello! ",
                "I'm your AI assistant ",
                "powered by HelloVM AI Funland. ",
                "How can I help you today?"
            ]
        elif "help" in message.lower():
            return [
                "I'd be happy to help! ",
                "I can assist with various tasks ",
                "including answering questions, ",
                "providing information, and more."
            ]
        elif "hardware" in message.lower():
            device_name = hardware_status.primary_device.name if hardware_status.primary_device else "CPU"
            return [
                "I'm currently running on ",
                f"{device_name}. ",
                "This platform supports multiple ",
                "hardware acceleration options!"
            ]
        elif "model" in message.lower():
            return [
                "I can work with various models ",
                "including Qwen, Llama, DeepSeek, and more. ",
                "Each model has different capabilities ",
                "and performance characteristics."
            ]
        else:
            # Generic response for other queries
            return [
                "I understand you're asking about ",
                f"'{message[:30]}...' ",
                "Based on my analysis, ",
                "this is a complex topic that requires ",
                "careful consideration. ",
                "Let me provide you with a comprehensive answer."
            ]
            
    async def _store_chat_response(self, session_id: str, user_message: str, assistant_response: str, model_id: Optional[str], hardware_status):
        """Store the complete chat response in the chat service"""
        try:
            # Add user message
            await self.chat_service.send_message(session_id, user_message)
            
            # For now, we'll simulate the assistant response being added
            # In a real implementation, this would be handled by the LLM service
            logger.debug("Chat response stored", session_id=session_id, response_length=len(assistant_response))
            
        except Exception as e:
            logger.error("Failed to store chat response", session_id=session_id, error=str(e))
            
    async def _send_stream_event(self, client_id: str, event_data: Dict[str, Any]):
        """Send stream event to client via WebSocket"""
        try:
            # Import WebSocket manager instance
            from ...main import websocket_handler
            
            # Send event through WebSocket handler
            await websocket_handler.send_stream_event(client_id, event_data)
            
            logger.debug("Stream event sent", client_id=client_id, event_type=event_data.get("type"))
            
        except Exception as e:
            logger.error("Failed to send stream event", client_id=client_id, error=str(e))
            
    async def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active stream"""
        if stream_id not in self.active_streams:
            return False
            
        try:
            stream_task = self.active_streams[stream_id]
            if not stream_task.done():
                stream_task.cancel()
                
            del self.active_streams[stream_id]
            
            logger.info("Stream cancelled", stream_id=stream_id)
            return True
            
        except Exception as e:
            logger.error("Failed to cancel stream", stream_id=stream_id, error=str(e))
            return False
            
    def get_active_streams(self) -> Dict[str, Any]:
        """Get information about active streams"""
        return {
            stream_id: {
                "status": "running" if not task.done() else "completed",
                "cancelled": task.cancelled() if task.done() else False
            }
            for stream_id, task in self.active_streams.items()
        }
        
    async def broadcast_hardware_update(self, hardware_status: Dict[str, Any]):
        """Broadcast hardware status updates to all connected clients"""
        try:
            event_data = {
                "type": "hardware_status_update",
                "timestamp": datetime.now().isoformat(),
                "hardware": hardware_status
            }
            
            # This would broadcast to all WebSocket clients
            logger.debug("Hardware update broadcast", hardware_devices=len(hardware_status.get("devices", [])))
            
        except Exception as e:
            logger.error("Failed to broadcast hardware update", error=str(e))
            
    async def broadcast_model_update(self, model_info: Dict[str, Any]):
        """Broadcast model status updates to all connected clients"""
        try:
            event_data = {
                "type": "model_status_update",
                "timestamp": datetime.now().isoformat(),
                "model": model_info
            }
            
            # This would broadcast to all WebSocket clients
            logger.debug("Model update broadcast", model_id=model_info.get("id"))
            
        except Exception as e:
            logger.error("Failed to broadcast model update", error=str(e))


# Integration helper for Vue frontend
class VueIntegrationHelper:
    """Helper class for Vue.js frontend integration"""
    
    @staticmethod
    def create_websocket_connection(url: str) -> Dict[str, Any]:
        """Create WebSocket connection configuration for Vue.js"""
        return {
            "url": url,
            "protocols": [],
            "reconnect": True,
            "reconnect_interval": 3000,
            "max_reconnects": 5,
            "binary_type": "blob"
        }
        
    @staticmethod
    def format_stream_message(chunk: str, progress: float) -> Dict[str, Any]:
        """Format streaming message for Vue.js consumption"""
        return {
            "content": chunk,
            "progress": progress,
            "timestamp": datetime.now().isoformat(),
            "is_complete": progress >= 1.0
        }
        
    @staticmethod
    def create_chat_message_event(session_id: str, message: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Create chat message event for WebSocket transmission"""
        return {
            "type": "chat_message",
            "session_id": session_id,
            "message": message,
            "model_id": model_id,
            "timestamp": datetime.now().isoformat()
        }