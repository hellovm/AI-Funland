import platform
import subprocess
import psutil
from openvino import Core

def get_hardware_info():
    core = Core()
    devices = core.available_devices
    cpu = platform.processor() or platform.machine()
    mem = psutil.virtual_memory().total
    gpu_name = None
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], capture_output=True, text=True, timeout=2)
        if out.returncode == 0:
            gpu_name = out.stdout.strip().splitlines()[0] if out.stdout.strip() else None
    except Exception:
        gpu_name = None
    return {'cpu': cpu, 'memory_bytes': mem, 'openvino_devices': devices, 'nvidia_gpu': gpu_name}

def get_available_accelerators():
    core = Core()
    devices = core.available_devices
    acc = []
    for d in devices:
        if d.upper().startswith('CPU'):
            acc.append('CPU')
        elif d.upper().startswith('GPU'):
            acc.append('GPU')
        elif d.upper().startswith('NPU'):
            acc.append('NPU')
    res = []
    seen = set()
    for a in acc:
        if a not in seen:
            res.append(a)
            seen.add(a)
    return res