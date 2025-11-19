# Architecture

- Backend: Python, APIFlask
- Inference: OpenVINO GenAI LLMPipeline
- Quantization: Optimum Intel OpenVINO
- Downloader: ModelScope snapshot_download
- UI: Static HTML/CSS/JS with i18n
- Plugins: Extensible interfaces for T2I, T2V, I2V, FaceSwap

## Modules

- backend/app.py: HTTP API and static serving
- backend/hardware.py: hardware and devices
- backend/model_manager.py: models, download, quantize, generate
- web/: UI assets

## Extension Interfaces

- Text to Image
- Text to Video
- Image to Video
- Video Face Swap