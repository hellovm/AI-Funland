"""
HelloVM AI Funland Backend Server
Multi-hardware accelerated LLM platform backend
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import structlog

# Add api directory to Python path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

from src.core.config import settings
from src.core.logging import setup_logging
from src.api.routes import router, set_services
from src.services.websocket_manager import ConnectionManager, WebSocketHandler
from src.services.hardware import HardwareService
from src.services.model import ModelService
from src.services.chat import ChatService

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Global services
hardware_service: HardwareService
model_service: ModelService
chat_service: ChatService
websocket_handler: WebSocketHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global hardware_service, model_service, chat_service, websocket_handler
    
    # Startup
    logger.info("Starting HelloVM AI Funland Backend")
    
    try:
        # Initialize services
        hardware_service = HardwareService()
        model_service = ModelService()
        chat_service = ChatService()
        
        # Initialize WebSocket handler
        connection_manager = ConnectionManager(chat_service, hardware_service, model_service)
        websocket_handler = WebSocketHandler(connection_manager)
        
        # Set services in routes
        set_services(hardware_service, model_service, chat_service)
        
        # Start hardware detection
        await hardware_service.start_detection()
        
        logger.info("Backend services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down HelloVM AI Funland Backend")
    
    try:
        await hardware_service.stop_detection()
        logger.info("Backend services stopped successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="HelloVM AI Funland Backend",
    description="Multi-hardware accelerated LLM platform backend API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket_handler.websocket_endpoint(websocket, client_id)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HelloVM AI Funland Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check service health
        hardware_status = await hardware_service.get_status()
        model_status = await model_service.get_status()
        
        return {
            "status": "healthy",
            "services": {
                "hardware": hardware_status,
                "models": model_status
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting HelloVM AI Funland Backend Server")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )