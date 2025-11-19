# Development Guide

## Architecture

- Backend: Python `APIFlask` with modular services
- Frontend: Static HTML/CSS/JS served by backend
- Inference: `openvino-genai` LLMPipeline
- Quantization: `optimum[openvino]` weight quantization
- Downloader: `modelscope` CLI via `python -m modelscope download`

## Modules

- `backend/services/system.py`: hardware and accelerator detection
- `backend/services/models.py`: model listing and deletion
- `backend/services/inference.py`: pipeline, generation and quantization
- `backend/utils/tasks.py`: background task store and progress

## API

- `GET /api/system/info`
- `GET /api/models/list`
- `POST /api/models/download`
- `GET /api/tasks/<id>`
- `POST /api/models/quantize`
- `DELETE /api/models/delete`
- `POST /api/infer/chat`

## Bilingual UI

- Client-side i18n with map and toggler

## Accelerators

- Devices from `openvino.runtime.Core().available_devices`
- NVIDIA detection via `nvidia-smi`

## Best Practices

- Follow OpenVINO LLMPipeline usage
- Use weight-only quantization when calibration data is absent
- Lazy-load models per request