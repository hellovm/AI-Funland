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
    has_npu = any(d.startswith("NPU") for d in devices)
    has_gpu = any(d.startswith("GPU") for d in devices)
    has_cpu = "CPU" in devices
    if has_npu:
        accelerators.append({"id": "NPU", "label": "Intel NPU"})
    if has_gpu:
        accelerators.append({"id": "GPU", "label": "Intel GPU"})
    if has_cpu:
        accelerators.append({"id": "CPU", "label": "CPU"})
    if nvidia:
        accelerators.append({"id": "NVIDIA", "label": "NVIDIA GPU"})
    # cooperative acceleration options
    combos = []
    if has_npu and has_gpu:
        combos.append({"id": "MULTI:NPU,GPU", "label": "Intel NPU+GPU (协同)"})
    if has_npu and has_cpu:
        combos.append({"id": "MULTI:NPU,CPU", "label": "Intel NPU+CPU (协同)"})
    if has_npu and has_gpu and has_cpu:
        combos.append({"id": "MULTI:NPU,GPU,CPU", "label": "Intel NPU+GPU+CPU (协同)"})
    accelerators = combos + accelerators
    # library versions
    tv = None
    ovv = None
    optv = None
    genv = None
    try:
        import transformers as _tr
        tv = getattr(_tr, "__version__", None)
    except Exception:
        tv = None
    try:
        import openvino as _ov
        ovv = getattr(_ov, "__version__", None)
    except Exception:
        ovv = None
    try:
        import optimum as _opt
        optv = getattr(_opt, "__version__", None)
        if not optv:
            try:
                import importlib.metadata as md
                optv = md.version("optimum")
            except Exception:
                pass
    except Exception:
        try:
            import importlib.metadata as md
            optv = md.version("optimum")
        except Exception:
            optv = None
    # add optimum-intel version
    try:
        import importlib.metadata as md
        optintel = md.version("optimum-intel")
    except Exception:
        optintel = None
    try:
        import openvino_genai as _og
        genv = getattr(_og, "__version__", None)
    except Exception:
        genv = None
    arch = {}
    try:
        from openvino.runtime import Core as _Core
        _c = _Core()
        if "NPU" in devices:
            try:
                a = _c.get_property("NPU", "DEVICE_ARCHITECTURE")
                arch["NPU"] = str(a)
            except Exception:
                pass
        if any(d.startswith("GPU") for d in devices):
            try:
                a = _c.get_property("GPU", "DEVICE_ARCHITECTURE")
                arch["GPU"] = str(a)
            except Exception:
                pass
    except Exception:
        pass
    import os as _os
    hints = {
        "OV_PERFORMANCE_HINT": _os.environ.get("OV_PERFORMANCE_HINT"),
        "OV_NUM_STREAMS": _os.environ.get("OV_NUM_STREAMS"),
        "OV_HINT_NUM_REQUESTS": _os.environ.get("OV_HINT_NUM_REQUESTS"),
        "NPU_TILES": _os.environ.get("NPU_TILES"),
    }
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
        "device_architecture": arch,
        "ov_hints": hints,
        "library_versions": {
            "transformers": tv,
            "optimum": optv,
            "optimum_intel": optintel,
            "openvino": ovv,
            "openvino_genai": genv,
        }
    }