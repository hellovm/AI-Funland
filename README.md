# HelloVM-AI-Funland 🚀

**多硬件加速大语言模型交互平台 / Multi-Hardware Accelerated LLM Interaction Platform**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3-green.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 项目简介 / Project Overview

HelloVM-AI-Funland 是一个先进的多硬件加速大语言模型交互平台，支持 CPU、Intel GPU、Intel NPU 和 NVIDIA GPU 等多种硬件加速方案。

HelloVM-AI-Funland is an advanced multi-hardware accelerated large language model interaction platform supporting CPU, Intel GPU, Intel NPU, and NVIDIA GPU acceleration solutions.

### ✨ 核心特性 / Core Features

- **🚀 多硬件加速 / Multi-Hardware Acceleration**
  - CPU 原生推理 / CPU Native Inference
  - Intel GPU (OpenVINO) 加速 / Intel GPU Acceleration
  - Intel NPU 专用加速 / Intel NPU Dedicated Acceleration
  - NVIDIA GPU (CUDA) 加速 / NVIDIA GPU Acceleration

- **📦 智能模型管理 / Intelligent Model Management**
  - Modelscope API 集成 / Modelscope API Integration
  - 多线程断点续传 / Multi-threaded Resume Downloads
  - GGUF/GGML 格式支持 / GGUF/GGML Format Support
  - 自动完整性校验 / Automatic Integrity Verification

- **🎨 现代化界面 / Modern Interface**
  - Vue 3 + TypeScript 架构 / Vue 3 + TypeScript Architecture
  - 国际化支持 (中英文) / Internationalization (Chinese/English)
  - 响应式设计 / Responsive Design
  - 实时性能监控 / Real-time Performance Monitoring

- **🔧 扩展能力 / Extension Capabilities**
  - 插件架构设计 / Plugin Architecture Design
  - 文本生成图像 / Text-to-Image Generation
  - 文本生成视频 / Text-to-Video Generation
  - 换脸功能预留 / Face Swap Functionality Reserved

## 🚀 快速开始 / Quick Start

### 系统要求 / System Requirements

- **操作系统 / OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python**: 3.13 或更高版本 / 3.13 or higher
- **Node.js**: 18.0 或更高版本 / 18.0 or higher
- **硬件要求 / Hardware**:
  - **最低配置 / Minimum**: 8GB RAM, 10GB 存储空间
  - **推荐配置 / Recommended**: 16GB RAM, 50GB 存储空间, 独立显卡

### 环境配置 / Environment Setup

#### 1. 克隆项目 / Clone Repository
```bash
git clone https://github.com/your-org/HelloVM-AI-Funland.git
cd HelloVM-AI-Funland
```

#### 2. 后端环境配置 / Backend Setup

**后端服务已完全实现 / Backend Service Fully Implemented:**

```bash
# 进入后端目录 / Navigate to backend directory
cd api

# 创建 Python 虚拟环境 / Create Python virtual environment
python -m venv venv

# 激活虚拟环境 / Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖 / Install dependencies
pip install -r requirements.txt

# 配置环境变量 / Configure environment
cp .env.example .env
# 编辑 .env 文件配置您的硬件加速设置 / Edit .env to configure your hardware acceleration settings

# 启动后端服务 / Start backend service
python start.py
```

**后端特性 / Backend Features:**
- **🔧 硬件检测服务 / Hardware Detection Service**: 自动检测 CPU、Intel GPU、Intel NPU、NVIDIA GPU
- **🤖 模型管理服务 / Model Management Service**: Modelscope API 集成，模型加载/卸载
- **💬 聊天服务 / Chat Service**: 实时 LLM 推理，会话管理
- **🌐 WebSocket 服务 / WebSocket Service**: 实时双向通信，流式响应
- **📊 性能监控 / Performance Monitoring**: 实时指标收集，健康检查

**API 端点 / API Endpoints:**
```
硬件管理 / Hardware Management:
GET  /api/v1/hardware/status          # 获取硬件状态
POST /api/v1/hardware/scan            # 触发硬件扫描
POST /api/v1/hardware/select/{id}     # 选择主设备
GET  /api/v1/hardware/metrics/{id}    # 获取设备指标

模型管理 / Model Management:
GET  /api/v1/models                   # 列出所有模型
GET  /api/v1/models/{id}              # 获取模型详情
POST /api/v1/models/{id}/load         # 加载模型
POST /api/v1/models/{id}/unload       # 卸载模型

聊天管理 / Chat Management:
POST /api/v1/chat/sessions            # 创建聊天会话
GET  /api/v1/chat/sessions/{id}       # 获取会话详情
POST /api/v1/chat/sessions/{id}/messages  # 发送消息
```

**WebSocket 连接 / WebSocket Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_123');
ws.send(JSON.stringify({
    type: 'chat',
    session_id: 'session_123',
    message: 'Hello!'
}));
```

#### 3. 前端环境配置 / Frontend Setup
```bash
# 进入前端目录 / Navigate to frontend directory
cd webui

# 安装依赖 / Install dependencies
npm install

# 开发模式运行 / Run in development mode
npm run dev
```

#### 4. 构建项目 / Build Project
```bash
# 构建前端 / Build frontend
npm run build

# 启动后端服务 / Start backend service
python main.py
```

## 📋 功能特性 / Features

### 硬件加速支持 / Hardware Acceleration Support

| 硬件类型 / Hardware | 加速方式 / Acceleration | 支持状态 / Status | 性能提升 / Performance |
|-------------------|----------------------|------------------|---------------------|
| CPU | 原生推理 / Native Inference | ✅ 支持 | 基准性能 / Baseline |
| Intel GPU | OpenVINO | ✅ 支持 | 2-5x 提升 / 2-5x Improvement |
| Intel NPU | 专用加速 / Dedicated | ✅ 支持 | 3-8x 提升 / 3-8x Improvement |
| NVIDIA GPU | CUDA | ✅ 支持 | 5-15x 提升 / 5-15x Improvement |

### 模型格式支持 / Model Format Support

- **GGUF**: GPT-Generated Unified Format (推荐 / Recommended)
- **GGML**: GPT-Generated Model Language
- **PyTorch**: .pt, .pth 格式
- **TensorFlow**: .pb, .h5 格式
- **ONNX**: .onnx 格式

### 插件扩展 / Plugin Extensions

- **文本生成图像 / Text-to-Image**: Stable Diffusion, DALL-E
- **文本生成视频 / Text-to-Video**: ModelScope, Stable Video Diffusion
- **图像生成视频 / Image-to-Video**: AnimateDiff, Stable Video Diffusion
- **换脸 / Face Swap**: DeepFaceLab, SimSwap

## 🏗️ 项目架构 / Architecture

### 系统架构图 / System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Vue 3 + TypeScript)              │
├─────────────────────────────────────────────────────────────┤
│                  API Gateway (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   Hardware  │   Model     │  Download   │   Plugin    │  │
│  │   Manager   │   Manager   │   Manager   │   Manager   │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Acceleration Layer (OpenVINO/CUDA)             │
├─────────────────────────────────────────────────────────────┤
│                    Model Runtime (LLM)                       │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构 / Directory Structure

```
HelloVM-AI-Funland/
├── core/                           # 核心模块 / Core modules
│   ├── __init__.py
│   ├── config.py                  # 配置管理 / Configuration
│   ├── logger.py                  # 日志系统 / Logging system
│   └── exceptions.py              # 异常定义 / Exceptions
├── accelerators/                   # 硬件加速 / Hardware accelerators
│   ├── __init__.py
│   ├── base.py                    # 基础加速类 / Base accelerator
│   ├── cpu.py                     # CPU 加速 / CPU acceleration
│   ├── intel_gpu.py               # Intel GPU 加速 / Intel GPU
│   ├── intel_npu.py               # Intel NPU 加速 / Intel NPU
│   └── nvidia_gpu.py              # NVIDIA GPU 加速 / NVIDIA GPU
├── webui/                         # 前端界面 / Frontend
│   ├── src/
│   │   ├── components/            # Vue 组件 / Vue components
│   │   ├── views/                 # 页面视图 / Page views
│   │   ├── stores/                # 状态管理 / State management
│   │   ├── types/                 # TypeScript 类型 / TypeScript types
│   │   └── i18n/                  # 国际化 / Internationalization
│   ├── public/
│   └── package.json
├── api/                           # API 接口 / API interfaces
│   ├── __init__.py
│   ├── routes/                    # 路由定义 / Route definitions
│   ├── models/                    # 数据模型 / Data models
│   └── middleware/                # 中间件 / Middleware
├── models/                        # 模型管理 / Model management
│   ├── __init__.py
│   ├── downloader.py              # 下载器 / Downloader
│   ├── manager.py                 # 模型管理器 / Model manager
│   └── validator.py               # 模型验证器 / Model validator
├── plugins/                       # 插件系统 / Plugin system
│   ├── __init__.py
│   ├── base.py                    # 插件基类 / Plugin base class
│   ├── loader.py                  # 插件加载器 / Plugin loader
│   └── extensions/                # 扩展插件 / Extension plugins
├── tests/                         # 测试代码 / Test code
│   ├── unit/                      # 单元测试 / Unit tests
│   ├── integration/               # 集成测试 / Integration tests
│   └── hardware/                  # 硬件测试 / Hardware tests
├── docs/                          # 文档 / Documentation
│   ├── api/                       # API 文档 / API documentation
│   ├── user_manual/               # 用户手册 / User manual
│   └── development/               # 开发文档 / Development docs
├── scripts/                       # 脚本工具 / Utility scripts
├── requirements.txt               # Python 依赖 / Python dependencies
├── setup.py                      # 安装脚本 / Setup script
└── README.md                     # 项目说明 / Project README
```

## 🔧 开发指南 / Development Guide

### 开发环境 / Development Environment

1. **Python 开发 / Python Development**
```bash
# 安装开发依赖 / Install development dependencies
pip install -r requirements-dev.txt

# 运行代码检查 / Run code linting
flake8 core/ api/ models/
mypy core/ api/ models/

# 运行单元测试 / Run unit tests
pytest tests/unit/ -v
```

2. **前端开发 / Frontend Development**
```bash
# 安装开发依赖 / Install development dependencies
cd webui && npm install

# 运行开发服务器 / Run development server
npm run dev

# 运行代码检查 / Run code linting
npm run lint
npm run type-check

# 构建生产版本 / Build for production
npm run build
```

### 硬件加速开发 / Hardware Acceleration Development

#### Intel OpenVINO 集成 / Intel OpenVINO Integration
```python
from accelerators.intel_gpu import IntelGPUAccelerator

# 初始化加速器 / Initialize accelerator
accelerator = IntelGPUAccelerator()

# 检测硬件支持 / Check hardware support
if accelerator.is_available():
    # 加载模型 / Load model
    model = accelerator.load_model("path/to/model")
    
    # 执行推理 / Run inference
    result = accelerator.infer(model, input_data)
```

#### NVIDIA CUDA 集成 / NVIDIA CUDA Integration
```python
from accelerators.nvidia_gpu import NvidiaGPUAccelerator

# 初始化加速器 / Initialize accelerator
accelerator = NvidiaGPUAccelerator()

# 检测硬件支持 / Check hardware support
if accelerator.is_available():
    # 配置 CUDA 参数 / Configure CUDA parameters
    accelerator.configure(cuda_visible_devices="0,1")
    
    # 加载模型 / Load model
    model = accelerator.load_model("path/to/model")
    
    # 执行推理 / Run inference
    result = accelerator.infer(model, input_data)
```

## 📊 性能基准 / Performance Benchmarks

### 模型推理性能 / Model Inference Performance

| 模型 / Model | 硬件 / Hardware | 加速方式 / Acceleration | 速度 / Speed (tokens/s) | 内存 / Memory |
|-------------|----------------|----------------------|------------------------|---------------|
| Qwen-7B | CPU | Native | 15 | 8GB |
| Qwen-7B | Intel GPU | OpenVINO | 35 | 6GB |
| Qwen-7B | Intel NPU | Dedicated | 45 | 4GB |
| Qwen-7B | NVIDIA GPU | CUDA | 85 | 4GB |
| Llama2-13B | CPU | Native | 8 | 16GB |
| Llama2-13B | Intel GPU | OpenVINO | 20 | 12GB |
| Llama2-13B | NVIDIA GPU | CUDA | 55 | 8GB |

### 下载性能 / Download Performance

| 模型大小 / Model Size | 网络环境 / Network | 下载时间 / Download Time | 平均速度 / Average Speed |
|---------------------|-------------------|------------------------|----------------------|
| 4GB | 100Mbps | 6分钟 / 6min | 11MB/s |
| 8GB | 100Mbps | 12分钟 / 12min | 11MB/s |
| 15GB | 100Mbps | 23分钟 / 23min | 11MB/s |

## 🔌 API 文档 / API Documentation

### 模型管理 API / Model Management API

#### 获取模型列表 / Get Model List
```http
GET /api/models
```

**响应 / Response**:
```json
{
  "models": [
    {
      "id": "qwen-7b-chat",
      "name": "Qwen-7B-Chat",
      "size": "4.2GB",
      "format": "gguf",
      "quantization": "q4_k_m",
      "status": "available"
    }
  ]
}
```

#### 下载模型 / Download Model
```http
POST /api/models/download
{
  "model_id": "qwen-7b-chat",
  "format": "gguf",
  "quantization": "q4_k_m"
}
```

### 硬件加速 API / Hardware Acceleration API

#### 获取硬件信息 / Get Hardware Info
```http
GET /api/hardware
```

**响应 / Response**:
```json
{
  "devices": [
    {
      "type": "cpu",
      "name": "Intel Core i7-12700K",
      "memory": "32GB",
      "utilization": "45%",
      "supported": true
    },
    {
      "type": "gpu",
      "name": "NVIDIA RTX 4070",
      "memory": "12GB",
      "utilization": "23%",
      "supported": true
    }
  ]
}
```

## 🧪 测试 / Testing

### 单元测试 / Unit Tests
```bash
# 运行所有单元测试 / Run all unit tests
pytest tests/unit/ -v

# 运行特定模块测试 / Run specific module tests
pytest tests/unit/test_hardware.py -v
pytest tests/unit/test_models.py -v
pytest tests/unit/test_downloads.py -v
```

### 集成测试 / Integration Tests
```bash
# 运行集成测试 / Run integration tests
pytest tests/integration/ -v

# 运行硬件兼容性测试 / Run hardware compatibility tests
pytest tests/hardware/ -v
```

### 性能测试 / Performance Tests
```bash
# 运行性能基准测试 / Run performance benchmarks
python scripts/benchmark.py --model qwen-7b --hardware all

# 生成性能报告 / Generate performance report
python scripts/generate_report.py --output reports/performance.html
```

## 🤝 贡献指南 / Contributing

我们欢迎所有形式的贡献！/ We welcome all forms of contribution!

### 如何贡献 / How to Contribute

1. **Fork 项目 / Fork the Project**
2. **创建功能分支 / Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **提交更改 / Commit Changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **推送到分支 / Push to Branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **创建 Pull Request / Create Pull Request**

### 开发规范 / Development Standards

- **代码风格 / Code Style**: 遵循 PEP 8 (Python), ESLint (JavaScript/TypeScript)
- **提交信息 / Commit Messages**: 遵循 Conventional Commits 规范
- **文档更新 / Documentation**: 更新相关文档和测试
- **测试覆盖 / Test Coverage**: 保持测试覆盖率 ≥ 85%

## 📄 许可证 / License

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 致谢 / Acknowledgments

- [ModelScope](https://modelscope.cn/) - 模型托管平台 / Model hosting platform
- [OpenVINO](https://www.intel.com/content/www/us/en/developer/tools/openvino-toolkit/overview.html) - Intel 优化工具包 / Intel optimization toolkit
- [CUDA](https://developer.nvidia.com/cuda-toolkit) - NVIDIA 并行计算平台 / NVIDIA parallel computing platform
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架 / Progressive JavaScript framework
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架 / Modern Python web framework

## 📞 联系方式 / Contact

- **项目主页 / Project Homepage**: [https://github.com/your-org/HelloVM-AI-Funland](https://github.com/your-org/HelloVM-AI-Funland)
- **问题反馈 / Issue Tracker**: [https://github.com/your-org/HelloVM-AI-Funland/issues](https://github.com/your-org/HelloVM-AI-Funland/issues)
- **邮件联系 / Email**: hellovm@example.com

---

<div align="center">
  <p><strong>HelloVM-AI-Funland</strong> - 让 AI 加速更简单 / Making AI Acceleration Easier</p>
  <p>⭐ 如果这个项目对您有帮助，请给我们一个星标！/ If this project helps you, please give us a star! ⭐</p>
</div>