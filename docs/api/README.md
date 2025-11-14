# API 文档
# API Documentation

## 🚀 概述 / Overview

HelloVM-AI-Funland API 提供了完整的 RESTful 接口，用于管理硬件加速、模型下载、聊天交互和插件扩展等功能。

The HelloVM-AI-Funland API provides comprehensive RESTful interfaces for managing hardware acceleration, model downloads, chat interactions, and plugin extensions.

## 📋 API 规范 / API Specification

### 基础信息 / Base Information

- **API 版本 / API Version**: v1
- **基础 URL / Base URL**: `http://localhost:8000/api/v1`
- **认证方式 / Authentication**: Bearer Token
- **内容类型 / Content Type**: `application/json`
- **编码 / Encoding**: UTF-8

### 通用响应格式 / Common Response Format

```json
{
  "code": 200,
  "message": "Success",
  "data": {},
  "timestamp": "2024-11-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 错误响应格式 / Error Response Format

```json
{
  "code": 400,
  "message": "Bad Request",
  "error": {
    "type": "validation_error",
    "details": "Parameter validation failed",
    "field_errors": {
      "model_id": "Model ID is required"
    }
  },
  "timestamp": "2024-11-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

## 🔧 硬件管理 API / Hardware Management API

### 获取硬件信息 / Get Hardware Information

获取系统中所有可用的硬件加速设备信息。

Get information about all available hardware acceleration devices in the system.

#### 请求 / Request

```http
GET /api/v1/hardware
```

#### 查询参数 / Query Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `detailed` | boolean | 否 / No | 是否返回详细信息 / Whether to return detailed information |
| `refresh` | boolean | 否 / No | 是否刷新硬件检测 / Whether to refresh hardware detection |

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "devices": [
      {
        "id": "cpu_0",
        "type": "cpu",
        "name": "Intel Core i7-12700K",
        "vendor": "Intel",
        "architecture": "x86_64",
        "cores": 12,
        "threads": 20,
        "base_frequency": 3600,
        "max_frequency": 5000,
        "memory_total": 34359738368,
        "memory_available": 25769803776,
        "utilization": 25.5,
        "temperature": 45,
        "supported_instructions": ["AVX", "AVX2", "SSE", "SSE2", "SSE3", "SSE4.1", "SSE4.2"],
        "acceleration_support": true,
        "performance_level": "baseline",
        "status": "available"
      },
      {
        "id": "gpu_0",
        "type": "intel_gpu",
        "name": "Intel Iris Xe Graphics",
        "vendor": "Intel",
        "memory_total": 4294967296,
        "memory_available": 2147483648,
        "utilization": 15.2,
        "temperature": 52,
        "driver_version": "31.0.101.2115",
        "acceleration_technology": "OpenVINO",
        "acceleration_support": true,
        "performance_level": "medium",
        "status": "available"
      },
      {
        "id": "npu_0",
        "type": "intel_npu",
        "name": "Intel AI Boost NPU",
        "vendor": "Intel",
        "memory_total": 1073741824,
        "memory_available": 536870912,
        "utilization": 8.7,
        "temperature": 38,
        "driver_version": "1.0.0",
        "acceleration_technology": "Intel NPU",
        "acceleration_support": true,
        "performance_level": "high",
        "power_efficiency": "excellent",
        "status": "available"
      }
    ],
    "acceleration_recommendations": [
      {
        "device_id": "npu_0",
        "reason": "Best power efficiency for AI inference",
        "estimated_performance_gain": 3.5
      },
      {
        "device_id": "gpu_0",
        "reason": "Good balance of performance and power",
        "estimated_performance_gain": 2.2
      }
    ]
  }
}
```

### 获取设备性能指标 / Get Device Performance Metrics

获取指定硬件设备的实时性能指标。

Get real-time performance metrics for a specific hardware device.

#### 请求 / Request

```http
GET /api/v1/hardware/{device_id}/metrics
```

#### 路径参数 / Path Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `device_id` | string | 是 / Yes | 设备 ID / Device ID |

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "device_id": "gpu_0",
    "timestamp": "2024-11-14T10:30:00Z",
    "metrics": {
      "utilization": 45.2,
      "memory_used": 2147483648,
      "memory_total": 4294967296,
      "memory_percent": 50.0,
      "temperature": 58,
      "power_draw": 15.5,
      "power_limit": 25.0,
      "clock_speed": 1300,
      "memory_clock": 2400,
      "fan_speed": 35
    },
    "history": [
      {
        "timestamp": "2024-11-14T10:29:50Z",
        "utilization": 42.1,
        "temperature": 56,
        "memory_percent": 48.5
      },
      {
        "timestamp": "2024-11-14T10:29:40Z",
        "utilization": 38.9,
        "temperature": 54,
        "memory_percent": 47.2
      }
    ]
  }
}
```

### 设置加速设备 / Set Acceleration Device

设置用于 AI 推理的硬件加速设备。

Set the hardware acceleration device for AI inference.

#### 请求 / Request

```http
POST /api/v1/hardware/acceleration
```

#### 请求体 / Request Body

```json
{
  "primary_device": "npu_0",
  "secondary_devices": ["gpu_0"],
  "acceleration_mode": "hybrid",
  "config": {
    "cpu_threads": 8,
    "gpu_memory_fraction": 0.8,
    "npu_power_mode": "balanced"
  }
}
```

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Acceleration configuration updated successfully",
  "data": {
    "primary_device": "npu_0",
    "secondary_devices": ["gpu_0"],
    "acceleration_mode": "hybrid",
    "status": "active",
    "estimated_performance": {
      "tokens_per_second": 85,
      "memory_usage": "optimized",
      "power_efficiency": "excellent"
    }
  }
}
```

## 📦 模型管理 API / Model Management API

### 搜索模型 / Search Models

在 Modelscope 中搜索可用的 AI 模型。

Search for available AI models in Modelscope.

#### 请求 / Request

```http
GET /api/v1/models/search
```

#### 查询参数 / Query Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `query` | string | 是 / Yes | 搜索关键词 / Search keyword |
| `format` | string | 否 / No | 模型格式 / Model format (gguf, ggml, pytorch) |
| `quantization` | string | 否 / No | 量化类型 / Quantization type |
| `limit` | integer | 否 / No | 返回结果数量 / Number of results to return |
| `offset` | integer | 否 / No | 偏移量 / Offset |

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "models": [
      {
        "id": "qwen/Qwen-7B-Chat",
        "name": "Qwen-7B-Chat",
        "description": "A large language model with 7 billion parameters",
        "size": "4.2GB",
        "format": "gguf",
        "quantization": "q4_k_m",
        "context_length": 32768,
        "tags": ["chat", "chinese", "english", "multilingual"],
        "downloads": 1250000,
        "rating": 4.8,
        "last_updated": "2024-11-01T00:00:00Z",
        "download_url": "https://modelscope.cn/api/v1/models/qwen/Qwen-7B-Chat/repo?Revision=master&FilePath=qwen-7b-chat-q4_k_m.gguf",
        "checksum": "sha256:abc123def456...",
        "is_downloaded": false,
        "local_path": null
      },
      {
        "id": "meta-llama/Llama-2-13b-chat",
        "name": "Llama-2-13B-Chat",
        "description": "A helpful and harmless language model",
        "size": "8.5GB",
        "format": "gguf",
        "quantization": "q5_k_m",
        "context_length": 4096,
        "tags": ["chat", "english", "helpful", "safe"],
        "downloads": 890000,
        "rating": 4.7,
        "last_updated": "2024-10-15T00:00:00Z",
        "download_url": "https://modelscope.cn/api/v1/models/meta-llama/Llama-2-13b-chat/repo?Revision=master&FilePath=llama-2-13b-chat-q5_k_m.gguf",
        "checksum": "sha256:def456ghi789...",
        "is_downloaded": true,
        "local_path": "/models/llama-2-13b-chat-q5_k_m.gguf"
      }
    ],
    "total": 1250,
    "page": 1,
    "page_size": 20,
    "has_next": true
  }
}
```

### 获取模型详情 / Get Model Details

获取指定模型的详细信息。

Get detailed information about a specific model.

#### 请求 / Request

```http
GET /api/v1/models/{model_id}
```

#### 路径参数 / Path Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `model_id` | string | 是 / Yes | 模型 ID / Model ID |

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": "qwen/Qwen-7B-Chat",
    "name": "Qwen-7B-Chat",
    "description": "A large language model with 7 billion parameters",
    "full_description": "Qwen-7B-Chat is a large language model developed by Alibaba Cloud...",
    "size": "4.2GB",
    "format": "gguf",
    "quantization": "q4_k_m",
    "context_length": 32768,
    "architecture": "transformer",
    "parameters": "7B",
    "training_data": "Mixed dataset including web text, books, and code",
    "license": "apache-2.0",
    "tags": ["chat", "chinese", "english", "multilingual"],
    "capabilities": [
      "text_generation",
      "question_answering",
      "translation",
      "summarization"
    ],
    "supported_languages": ["zh", "en", "ja", "ko", "fr", "de", "es"],
    "performance_metrics": {
      "reasoning_score": 0.78,
      "knowledge_score": 0.82,
      "coding_score": 0.65,
      "math_score": 0.45
    },
    "downloads": 1250000,
    "rating": 4.8,
    "reviews": 892,
    "last_updated": "2024-11-01T00:00:00Z",
    "created_at": "2023-08-01T00:00:00Z",
    "download_url": "https://modelscope.cn/api/v1/models/qwen/Qwen-7B-Chat/repo?Revision=master&FilePath=qwen-7b-chat-q4_k_m.gguf",
    "checksum": "sha256:abc123def456...",
    "files": [
      {
        "name": "qwen-7b-chat-q4_k_m.gguf",
        "size": 4512345678,
        "checksum": "sha256:abc123def456...",
        "download_url": "https://modelscope.cn/api/v1/models/qwen/Qwen-7B-Chat/repo?Revision=master&FilePath=qwen-7b-chat-q4_k_m.gguf"
      },
      {
        "name": "README.md",
        "size": 12345,
        "download_url": "https://modelscope.cn/api/v1/models/qwen/Qwen-7B-Chat/repo?Revision=master&FilePath=README.md"
      }
    ],
    "is_downloaded": false,
    "local_path": null,
    "download_progress": null
  }
}
```

### 下载模型 / Download Model

开始下载指定的 AI 模型。

Start downloading a specified AI model.

#### 请求 / Request

```http
POST /api/v1/models/download
```

#### 请求体 / Request Body

```json
{
  "model_id": "qwen/Qwen-7B-Chat",
  "format": "gguf",
  "quantization": "q4_k_m",
  "download_path": "/models",
  "options": {
    "max_threads": 8,
    "resume_download": true,
    "verify_checksum": true,
    "priority": "high"
  }
}
```

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Download started successfully",
  "data": {
    "download_id": "download_123456",
    "model_id": "qwen/Qwen-7B-Chat",
    "status": "downloading",
    "progress": {
      "percent": 0,
      "downloaded_bytes": 0,
      "total_bytes": 4512345678,
      "speed": 0,
      "eta": null
    },
    "threads": 8,
    "start_time": "2024-11-14T10:30:00Z",
    "estimated_completion": "2024-11-14T10:45:00Z"
  }
}
```

## 📥 下载管理 API / Download Management API

### 获取下载任务 / Get Download Tasks

获取所有下载任务的状态信息。

Get status information for all download tasks.

#### 请求 / Request

```http
GET /api/v1/downloads
```

#### 查询参数 / Query Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `status` | string | 否 / No | 任务状态过滤 / Task status filter |
| `model_id` | string | 否 / No | 模型 ID 过滤 / Model ID filter |
| `limit` | integer | 否 / No | 返回结果数量 / Number of results |

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "downloads": [
      {
        "id": "download_123456",
        "model_id": "qwen/Qwen-7B-Chat",
        "model_name": "Qwen-7B-Chat",
        "filename": "qwen-7b-chat-q4_k_m.gguf",
        "status": "downloading",
        "progress": {
          "percent": 65.5,
          "downloaded_bytes": 2955589064,
          "total_bytes": 4512345678,
          "speed": 12500000,
          "eta": 124
        },
        "threads": 8,
        "active_connections": 6,
        "max_connections": 16,
        "resumable": true,
        "start_time": "2024-11-14T10:30:00Z",
        "estimated_completion": "2024-11-14T10:45:00Z"
      },
      {
        "id": "download_789012",
        "model_id": "meta-llama/Llama-2-13b-chat",
        "model_name": "Llama-2-13B-Chat",
        "filename": "llama-2-13b-chat-q5_k_m.gguf",
        "status": "completed",
        "progress": {
          "percent": 100,
          "downloaded_bytes": 9123456789,
          "total_bytes": 9123456789,
          "speed": 0,
          "eta": 0
        },
        "threads": 8,
        "active_connections": 0,
        "max_connections": 16,
        "resumable": true,
        "start_time": "2024-11-14T09:15:00Z",
        "completion_time": "2024-11-14T09:35:00Z",
        "checksum_verified": true
      }
    ],
    "summary": {
      "total_downloads": 2,
      "active_downloads": 1,
      "completed_downloads": 1,
      "failed_downloads": 0,
      "total_speed": 12500000,
      "total_downloaded": 12079045853
    }
  }
}
```

### 控制下载任务 / Control Download Task

控制下载任务的执行（暂停、恢复、取消）。

Control the execution of download tasks (pause, resume, cancel).

#### 请求 / Request

```http
POST /api/v1/downloads/{download_id}/control
```

#### 路径参数 / Path Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `download_id` | string | 是 / Yes | 下载任务 ID / Download task ID |

#### 请求体 / Request Body

```json
{
  "action": "pause",
  "reason": "User requested pause"
}
```

#### 可能的操作 / Possible Actions

- `pause`: 暂停下载 / Pause download
- `resume`: 恢复下载 / Resume download
- `cancel`: 取消下载 / Cancel download
- `retry`: 重试下载 / Retry download

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Download paused successfully",
  "data": {
    "download_id": "download_123456",
    "status": "paused",
    "action": "pause",
    "timestamp": "2024-11-14T10:35:00Z"
  }
}
```

## 💬 聊天 API / Chat API

### 创建聊天会话 / Create Chat Session

创建新的聊天会话。

Create a new chat session.

#### 请求 / Request

```http
POST /api/v1/chat/sessions
```

#### 请求体 / Request Body

```json
{
  "model_id": "qwen/Qwen-7B-Chat",
  "device_id": "npu_0",
  "config": {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_tokens": 512,
    "system_prompt": "You are a helpful AI assistant."
  },
  "metadata": {
    "title": "AI Assistant Chat",
    "tags": ["general", "help"]
  }
}
```

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Chat session created successfully",
  "data": {
    "session_id": "session_abc123",
    "model_id": "qwen/Qwen-7B-Chat",
    "device_id": "npu_0",
    "status": "active",
    "created_at": "2024-11-14T10:30:00Z",
    "config": {
      "temperature": 0.7,
      "top_p": 0.95,
      "top_k": 40,
      "max_tokens": 512,
      "system_prompt": "You are a helpful AI assistant."
    },
    "message_count": 0,
    "ws_url": "ws://localhost:8000/api/v1/chat/sessions/session_abc123/stream"
  }
}
```

### 发送消息 / Send Message

向聊天会话发送消息。

Send a message to the chat session.

#### 请求 / Request

```http
POST /api/v1/chat/sessions/{session_id}/messages
```

#### 路径参数 / Path Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `session_id` | string | 是 / Yes | 会话 ID / Session ID |

#### 请求体 / Request Body

```json
{
  "message": "Hello, how are you today?",
  "stream": true,
  "metadata": {
    "client_id": "user123",
    "timestamp": "2024-11-14T10:30:00Z"
  }
}
```

#### 响应 / Response (非流式 / Non-streaming)

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "message_id": "msg_xyz789",
    "session_id": "session_abc123",
    "role": "assistant",
    "content": "Hello! I'm doing well, thank you for asking. How can I help you today?",
    "tokens": 18,
    "inference_time": 0.85,
    "device_used": "npu_0",
    "timestamp": "2024-11-14T10:30:01Z"
  }
}
```

## 🔌 插件 API / Plugin API

### 获取插件列表 / Get Plugin List

获取所有可用插件的信息。

Get information about all available plugins.

#### 请求 / Request

```http
GET /api/v1/plugins
```

#### 查询参数 / Query Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `category` | string | 否 / No | 插件类别 / Plugin category |
| `status` | string | 否 / No | 插件状态 / Plugin status |

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "plugins": [
      {
        "id": "text_to_image",
        "name": "Text to Image Generator",
        "description": "Generate images from text descriptions",
        "version": "1.0.0",
        "category": "generation",
        "author": "HelloVM Team",
        "status": "enabled",
        "capabilities": ["text_to_image", "image_generation", "stable_diffusion"],
        "supported_formats": ["png", "jpg", "webp"],
        "max_resolution": "1024x1024",
        "config_schema": {
          "type": "object",
          "properties": {
            "model": {
              "type": "string",
              "enum": ["stable-diffusion-v1.5", "stable-diffusion-v2.1"],
              "default": "stable-diffusion-v1.5"
            },
            "steps": {
              "type": "integer",
              "minimum": 10,
              "maximum": 100,
              "default": 20
            },
            "guidance_scale": {
              "type": "number",
              "minimum": 1.0,
              "maximum": 20.0,
              "default": 7.5
            }
          }
        }
      },
      {
        "id": "text_to_video",
        "name": "Text to Video Generator",
        "description": "Generate videos from text descriptions",
        "version": "0.9.0",
        "category": "generation",
        "author": "HelloVM Team",
        "status": "beta",
        "capabilities": ["text_to_video", "video_generation"],
        "supported_formats": ["mp4", "webm"],
        "max_resolution": "512x512",
        "max_duration": 10
      }
    ],
    "categories": ["generation", "processing", "analysis", "utility"],
    "total": 8,
    "enabled": 5,
    "beta": 2,
    "disabled": 1
  }
}
```

### 执行插件 / Execute Plugin

执行指定的插件功能。

Execute the specified plugin functionality.

#### 请求 / Request

```http
POST /api/v1/plugins/{plugin_id}/execute
```

#### 路径参数 / Path Parameters

| 参数 / Parameter | 类型 / Type | 必填 / Required | 描述 / Description |
|----------------|-------------|-----------------|-------------------|
| `plugin_id` | string | 是 / Yes | 插件 ID / Plugin ID |

#### 请求体 / Request Body

```json
{
  "input": {
    "text": "A beautiful sunset over the ocean with mountains in the background",
    "style": "photorealistic",
    "resolution": "512x512"
  },
  "config": {
    "model": "stable-diffusion-v1.5",
    "steps": 20,
    "guidance_scale": 7.5,
    "seed": 42
  },
  "output_format": "png",
  "async": false
}
```

#### 响应 / Response

```json
{
  "code": 200,
  "message": "Plugin executed successfully",
  "data": {
    "plugin_id": "text_to_image",
    "execution_id": "exec_123456",
    "status": "completed",
    "input": {
      "text": "A beautiful sunset over the ocean with mountains in the background",
      "style": "photorealistic",
      "resolution": "512x512"
    },
    "output": {
      "type": "image",
      "format": "png",
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
      "width": 512,
      "height": 512,
      "size": 123456
    },
    "metadata": {
      "execution_time": 8.5,
      "device_used": "gpu_0",
      "model_version": "stable-diffusion-v1.5",
      "seed": 42,
      "generation_steps": 20
    },
    "timestamp": "2024-11-14T10:30:00Z"
  }
}
```

## 🔧 系统管理 API / System Management API

### 获取系统状态 / Get System Status

获取系统的整体状态信息。

Get overall system status information.

#### 请求 / Request

```http
GET /api/v1/system/status
```

#### 响应 / Response

```json
{
  "code": 200,
  "message": "System status retrieved successfully",
  "data": {
    "system": {
      "version": "1.0.0",
      "uptime": 3600,
      "status": "healthy",
      "start_time": "2024-11-14T09:30:00Z"
    },
    "hardware": {
      "total_devices": 4,
      "active_devices": 3,
      "acceleration_enabled": true,
      "primary_device": "npu_0"
    },
    "models": {
      "total_models": 15,
      "downloaded_models": 8,
      "active_models": 2,
      "total_size": "45.2GB"
    },
    "downloads": {
      "active_downloads": 1,
      "completed_downloads": 23,
      "failed_downloads": 2,
      "total_downloaded": "156.8GB"
    },
    "performance": {
      "average_inference_time": 0.85,
      "tokens_per_second": 45.2,
      "memory_usage": 68.5,
      "cpu_usage": 25.3
    },
    "plugins": {
      "total_plugins": 8,
      "enabled_plugins": 5,
      "active_plugins": 2
    }
  }
}
```

### 获取系统配置 / Get System Configuration

获取系统配置信息。

Get system configuration information.

#### 请求 / Request

```http
GET /api/v1/system/config
```

#### 响应 / Response

```json
{
  "code": 200,
  "message": "System configuration retrieved successfully",
  "data": {
    "general": {
      "language": "zh-CN",
      "theme": "auto",
      "auto_start": true,
      "minimize_to_tray": true
    },
    "hardware": {
      "auto_detection": true,
      "preferred_device": "npu",
      "acceleration_mode": "hybrid",
      "cpu_threads": 8,
      "gpu_memory_fraction": 0.8
    },
    "downloads": {
      "max_concurrent": 3,
      "max_threads": 8,
      "download_path": "/models",
      "auto_verify": true,
      "resume_downloads": true
    },
    "chat": {
      "default_model": "qwen/Qwen-7B-Chat",
      "max_context_length": 32768,
      "auto_save": true,
      "enable_streaming": true
    },
    "plugins": {
      "auto_load": true,
      "sandbox_mode": true,
      "max_memory": "2GB"
    }
  }
}
```

## 📋 错误处理 / Error Handling

### 错误码说明 / Error Code Description

| 错误码 / Error Code | 描述 / Description | 说明 / Explanation |
|-------------------|------------------|-------------------|
| 200 | Success | 请求成功 / Request successful |
| 400 | Bad Request | 请求参数错误 / Invalid request parameters |
| 401 | Unauthorized | 未授权 / Unauthorized |
| 403 | Forbidden | 权限不足 / Insufficient permissions |
| 404 | Not Found | 资源不存在 / Resource not found |
| 409 | Conflict | 资源冲突 / Resource conflict |
| 422 | Unprocessable Entity | 请求体格式错误 / Invalid request body format |
| 429 | Too Many Requests | 请求频率限制 / Rate limit exceeded |
| 500 | Internal Server Error | 服务器内部错误 / Internal server error |
| 503 | Service Unavailable | 服务不可用 / Service unavailable |

### 常见错误示例 / Common Error Examples

#### 400 Bad Request

```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "error": {
    "type": "validation_error",
    "details": "Model ID format is invalid",
    "field_errors": {
      "model_id": "Model ID must be in format 'owner/model-name'"
    }
  },
  "timestamp": "2024-11-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

#### 404 Not Found

```json
{
  "code": 404,
  "message": "Resource not found",
  "error": {
    "type": "not_found",
    "details": "The requested model was not found",
    "resource": "model",
    "resource_id": "invalid-model-id"
  },
  "timestamp": "2024-11-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

#### 500 Internal Server Error

```json
{
  "code": 500,
  "message": "Internal server error",
  "error": {
    "type": "internal_error",
    "details": "An unexpected error occurred while processing your request",
    "error_id": "err_987654321",
    "support_reference": "Please contact support with error ID: err_987654321"
  },
  "timestamp": "2024-11-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

---

<div align="center">
  <p><strong>HelloVM-AI-Funland API 文档</strong></p>
  <p>版本 / Version: 1.0.0 | 更新日期 / Last Updated: 2024-11-14</p>
</div>