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

def _cpu_model():
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(["wmic", "cpu", "get", "Name"], stderr=subprocess.STDOUT, shell=True, text=True)
            for ln in out.splitlines():
                s = ln.strip()
                if not s or s.lower().startswith("name"):
                    continue
                return s
        elif platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":", 1)[1].strip()
            except Exception:
                pass
        return platform.processor() or platform.machine()
    except Exception:
        return platform.processor() or platform.machine()

def _windows_video_controllers():
    try:
        out = subprocess.check_output(["wmic", "path", "Win32_VideoController", "get", "Name"], stderr=subprocess.STDOUT, shell=True, text=True)
        names = []
        for ln in out.splitlines():
            s = ln.strip()
            if not s or s.lower().startswith("name"):
                continue
            names.append(s)
        return names
    except Exception:
        return []

def _memory_info():
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        if ok:
            total = int(stat.ullTotalPhys)
            avail = int(stat.ullAvailPhys)
            used = total - avail
            perc = float(stat.dwMemoryLoad)
            return {"total_bytes": total, "available_bytes": avail, "used_bytes": used, "used_percent": perc}
    except Exception:
        pass
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {"total_bytes": int(vm.total), "available_bytes": int(vm.available), "used_bytes": int(vm.used), "used_percent": float(vm.percent)}
    except Exception:
        return None

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
    # cooperative acceleration options
    combos = []
    if has_npu and has_gpu and has_cpu:
        combos.append({"id": "HETERO:NPU,GPU,CPU", "label": "Intel NPU+Intel GPU+Intel CPU（异构）"})
        combos.append({"id": "HETERO:NPU,CPU", "label": "Intel NPU+Intel CPU（异构）"})
        combos.append({"id": "HETERO:GPU,CPU", "label": "Intel GPU+Intel CPU（异构）"})
    elif has_npu and has_cpu:
        combos.append({"id": "HETERO:NPU,CPU", "label": "Intel NPU+Intel CPU（异构）"})
    elif has_gpu and has_cpu:
        combos.append({"id": "HETERO:GPU,CPU", "label": "Intel GPU+Intel CPU（异构）"})
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
        try:
            full_gpu = _c.get_property("GPU", "FULL_DEVICE_NAME")
            if isinstance(full_gpu, (str, bytes)):
                arch["GPU_FULL_NAME"] = str(full_gpu)
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
    try:
        from openvino.runtime import Core as _Core
        _hc = _Core()
        try:
            hp = _hc.get_property("HETERO", "MULTI_DEVICE_PRIORITIES")
            hints["HETERO_PRIORITIES"] = hp
        except Exception:
            pass
        try:
            pol = _hc.get_property("HETERO", "MODEL_DISTRIBUTION_POLICY")
            hints["HETERO_MODEL_DISTRIBUTION_POLICY"] = str(pol)
        except Exception:
            pass
    except Exception:
        pass
    cpu_model = _cpu_model()
    vc = _windows_video_controllers() if platform.system() == "Windows" else []
    vc_intel = [n for n in vc if ("intel" in n.lower()) or ("arc" in n.lower())]
    hw_models = {
        "cpu": cpu_model,
        "npu": arch.get("NPU"),
        "gpu": vc_intel or ([arch.get("GPU_FULL_NAME")] if arch.get("GPU_FULL_NAME") else ([] if not arch.get("GPU") else [arch.get("GPU")])),
        "nvidia": [g.get("name") for g in nvidia] if nvidia else [],
    }
    mem = _memory_info()
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
        "hardware_models": hw_models,
        "memory": mem,
        "library_versions": {
            "transformers": tv,
            "optimum": optv,
            "optimum_intel": optintel,
            "openvino": ovv,
            "openvino_genai": genv,
        }
    }