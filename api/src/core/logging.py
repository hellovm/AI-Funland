"""
Logging configuration for HelloVM AI Funland Backend
"""

import logging
import sys
from pathlib import Path
import structlog
from structlog.stdlib import LoggerFactory
from structlog.dev import ConsoleRenderer
from pythonjsonlogger import jsonlogger

from .config import settings


def setup_logging():
    """Setup structured logging configuration"""
    
    # Create logs directory
    settings.LOGS_DIR.mkdir(exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        logger_factory=LoggerFactory(),
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Setup file logging if enabled
    if settings.LOG_FORMAT == "json":
        # JSON file handler
        file_handler = logging.FileHandler(settings.LOGS_DIR / "app.json")
        file_handler.setFormatter(jsonlogger.JsonFormatter())
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    # Create separate loggers for different components
    loggers = {
        "hardware": settings.LOGS_DIR / "hardware.log",
        "models": settings.LOGS_DIR / "models.log",
        "chat": settings.LOGS_DIR / "chat.log",
        "downloads": settings.LOGS_DIR / "downloads.log",
        "plugins": settings.LOGS_DIR / "plugins.log",
    }
    
    for name, log_file in loggers.items():
        # Create component-specific logger
        component_logger = logging.getLogger(name)
        
        # File handler for component
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)
        
        # Formatter based on log format setting
        if settings.LOG_FORMAT == "json":
            formatter = jsonlogger.JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        component_logger.addHandler(handler)
        component_logger.setLevel(logging.DEBUG)
        component_logger.propagate = False


def get_logger(name: str = None):
    """Get a structured logger instance"""
    return structlog.get_logger(name)