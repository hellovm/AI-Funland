import os
import platform
import subprocess
from pathlib import Path

def _nvidia_info():
    try:
        out = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader"
        ], stderr=subprocess.STDOUT, shell=True, text=True)
        gpus = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                gpus.append({"name": parts[0], "memory_total": parts[1]})
        return gpus
    except Exception:
        return []

def _openvino_devices():
    try:
        from openvino.runtime import Core
        core = Core()
        return core.available_devices
    except Exception:
        return []

def get_info():
    devices = _openvino_devices()
    nvidia = _nvidia_info()
    accelerators = []
    if "CPU" in devices:
        accelerators.append({"id": "CPU", "label": "CPU"})
    if any(d.startswith("GPU") for d in devices):
        accelerators.append({"id": "GPU", "label": "Intel GPU"})
    if any(d.startswith("NPU") for d in devices):
        accelerators.append({"id": "NPU", "label": "Intel NPU"})
    if nvidia:
        accelerators.append({"id": "NVIDIA", "label": "NVIDIA GPU"})
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "openvino_devices": devices,
        "nvidia_gpus": nvidia,
        "accelerators": accelerators,
        "cwd": str(Path.cwd()),
    }