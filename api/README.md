# HelloVM AI Funland Backend

Multi-hardware accelerated LLM platform backend service with support for CPU, Intel GPU, Intel NPU, and NVIDIA GPU acceleration.

## Features

### 🚀 Multi-Hardware Acceleration
- **CPU**: Native CPU acceleration with OpenVINO
- **Intel GPU**: Intel Arc GPU acceleration via OpenVINO
- **Intel NPU**: Intel Neural Processing Unit support
- **NVIDIA GPU**: CUDA and TensorRT acceleration

### 🔧 Core Services
- **Hardware Detection**: Automatic hardware discovery and monitoring
- **Model Management**: Model loading, unloading, and format conversion
- **Chat Service**: Real-time LLM inference with streaming support
- **WebSocket Communication**: Real-time bidirectional communication
- **Performance Monitoring**: Real-time metrics and health monitoring

### 📊 API Endpoints
- **Hardware Management**: Device status, selection, and metrics
- **Model Management**: Model listing, loading, and configuration
- **Chat Management**: Session management and message processing
- **System Monitoring**: Health checks and system information

## Installation

### Prerequisites
- Python 3.8+
- CUDA Toolkit (for NVIDIA GPU support)
- Intel OpenVINO Toolkit (for Intel hardware support)

### Install Dependencies
```bash
cd api
pip install -r requirements.txt
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

### Hardware Acceleration
```bash
# Enable/disable specific hardware
ENABLE_OPENVINO=true
ENABLE_CUDA=true
ENABLE_NPU=true

# Hardware scanning interval (seconds)
HARDWARE_SCAN_INTERVAL=30
```

### Model Management
```bash
# Default model configuration
DEFAULT_MODEL_ID=qwen2.5-7b-instruct-q4
MAX_CONCURRENT_DOWNLOADS=3

# Modelscope API (optional)
MODELSCOPE_API_KEY=your_api_key_here
```

### WebSocket Configuration
```bash
# WebSocket settings
WS_MAX_CONNECTIONS=100
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=10
```

## Usage

### Start the Server
```bash
# Development mode
python start.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Hardware Management
```http
GET /api/v1/hardware/status          # Get hardware status
POST /api/v1/hardware/scan           # Trigger hardware scan
POST /api/v1/hardware/select/{id}    # Select primary device
GET /api/v1/hardware/metrics/{id}    # Get device metrics
```

### Model Management
```http
GET /api/v1/models                   # List all models
GET /api/v1/models/{id}              # Get model details
POST /api/v1/models/{id}/load        # Load model
POST /api/v1/models/{id}/unload      # Unload model
GET /api/v1/models/search?query=     # Search models
```

### Chat Management
```http
POST /api/v1/chat/sessions           # Create chat session
GET /api/v1/chat/sessions/{id}       # Get session details
POST /api/v1/chat/sessions/{id}/messages  # Send message
GET /api/v1/chat/sessions/{id}/messages   # Get messages
```

### System Information
```http
GET /api/v1/system/info              # System information
GET /api/v1/system/health            # Health check
```

### WebSocket
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/client_123');

// Subscribe to channels
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'hardware_status'
}));

// Send chat message
ws.send(JSON.stringify({
    type: 'chat',
    session_id: 'session_123',
    message: 'Hello!'
}));
```

## Hardware Detection

### CPU Detection
- Core count and frequency
- Memory usage and availability
- Temperature monitoring (if available)

### Intel GPU Detection
- OpenVINO runtime detection
- Intel Arc GPU identification
- Memory and utilization metrics

### Intel NPU Detection
- Intel NPU compiler detection
- Neural processing unit identification
- Performance metrics

### NVIDIA GPU Detection
- CUDA device enumeration
- Memory usage and temperature
- Compute capability detection
- Driver version information

## Performance Monitoring

### Real-time Metrics
- **Tokens per second**: Inference performance
- **Memory usage**: RAM and VRAM utilization
- **Hardware utilization**: CPU, GPU, NPU usage
- **Latency**: Response time measurements

### Health Monitoring
- Service availability checks
- Hardware temperature monitoring
- Memory leak detection
- Performance degradation alerts

## Development

### Project Structure
```
api/
├── src/
│   ├── core/           # Core functionality
│   │   ├── config.py   # Configuration management
│   │   └── logging.py  # Structured logging
│   ├── api/            # API endpoints
│   │   ├── routes.py   # REST API routes
│   │   └── websocket.py # WebSocket manager
│   └── services/       # Business logic
│       ├── hardware.py # Hardware detection
│       ├── model.py    # Model management
│       └── chat.py     # Chat service
├── requirements.txt    # Python dependencies
├── start.py           # Startup script
└── main.py            # FastAPI application
```

### Adding New Hardware Support
1. Create hardware detection function in `services/hardware.py`
2. Add hardware type to device enumeration
3. Implement metrics collection
4. Add API endpoints if needed

### Extending Model Support
1. Add model format detection in `services/model.py`
2. Implement model loading logic
3. Add format conversion if needed
4. Update API endpoints

## Testing

### Unit Tests
```bash
pytest tests/ -v
```

### Hardware Detection Test
```bash
python -c "from src.services.hardware import HardwareService; import asyncio; asyncio.run(HardwareService().scan_hardware())"
```

### API Integration Test
```bash
curl http://localhost:8000/api/v1/system/health
```

## Troubleshooting

### Common Issues

#### Hardware Not Detected
- Check hardware drivers are installed
- Verify OpenVINO/CUDA installation
- Check system permissions

#### Model Loading Fails
- Verify model file exists
- Check available memory
- Review model format compatibility

#### WebSocket Connection Issues
- Check firewall settings
- Verify WebSocket URL format
- Review connection limits

### Debug Mode
```bash
DEBUG=true LOG_LEVEL=DEBUG python start.py
```

## Security Considerations

### Production Deployment
- Change default JWT secret
- Enable API key authentication
- Use HTTPS for external access
- Implement rate limiting

### Hardware Access
- Run with appropriate permissions
- Secure hardware interfaces
- Monitor resource usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

This project is part of the HelloVM AI Funland platform and follows the same licensing terms.