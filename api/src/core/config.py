"""
Core configuration for HelloVM AI Funland Backend
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "HelloVM AI Funland"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:4173", "http://127.0.0.1:5173"],
        env="ALLOWED_ORIGINS"
    )
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    MODELS_DIR: Path = Field(default=Path("models"), env="MODELS_DIR")
    DOWNLOADS_DIR: Path = Field(default=Path("downloads"), env="DOWNLOADS_DIR")
    LOGS_DIR: Path = Field(default=Path("logs"), env="LOGS_DIR")
    PLUGINS_DIR: Path = Field(default=Path("plugins"), env="PLUGINS_DIR")
    
    # Hardware detection
    AUTO_DETECT_HARDWARE: bool = Field(default=True, env="AUTO_DETECT_HARDWARE")
    HARDWARE_SCAN_INTERVAL: int = Field(default=30, env="HARDWARE_SCAN_INTERVAL")  # seconds
    
    # Model settings
    DEFAULT_MODEL_ID: str = Field(default="qwen2.5-7b-instruct-q4", env="DEFAULT_MODEL_ID")
    MAX_CONCURRENT_DOWNLOADS: int = Field(default=3, env="MAX_CONCURRENT_DOWNLOADS")
    DOWNLOAD_CHUNK_SIZE: int = Field(default=8192, env="DOWNLOAD_CHUNK_SIZE")
    
    # Hardware acceleration
    ENABLE_OPENVINO: bool = Field(default=True, env="ENABLE_OPENVINO")
    ENABLE_CUDA: bool = Field(default=True, env="ENABLE_CUDA")
    ENABLE_NPU: bool = Field(default=True, env="ENABLE_NPU")
    
    # Modelscope API
    MODELSCOPE_API_KEY: Optional[str] = Field(default=None, env="MODELSCOPE_API_KEY")
    MODELSCOPE_BASE_URL: str = Field(default="https://www.modelscope.cn/api/v1", env="MODELSCOPE_BASE_URL")
    
    # Performance monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json or text
    
    # WebSocket
    WS_MAX_CONNECTIONS: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    WS_PING_INTERVAL: int = Field(default=30, env="WS_PING_INTERVAL")
    WS_PING_TIMEOUT: int = Field(default=10, env="WS_PING_TIMEOUT")
    
    # Security
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    JWT_SECRET: str = Field(default="your-secret-key", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.MODELS_DIR.mkdir(exist_ok=True)
        self.DOWNLOADS_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.PLUGINS_DIR.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()