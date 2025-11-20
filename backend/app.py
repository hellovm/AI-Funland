import json
import threading
import subprocess
import shlex
import shutil
from pathlib import Path
from apiflask import APIFlask
from flask import request, jsonify, send_from_directory
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.services.system import get_info
from backend.services.models import list_models, delete_model, models_root
from backend.services.inference import load_pipeline, generate, quantize_model, is_model_in_use, release_model, is_model_loaded
from backend.utils.tasks import task_store

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = models_root(BASE_DIR)
PERF = {"lat": {"CPU": [], "GPU": [], "NPU": [], "NVIDIA": []}, "ttft": {"CPU": [], "GPU": [], "NPU": [], "NVIDIA": []}, "tpot": {"CPU": [], "GPU": [], "NPU": [], "NVIDIA": []}, "throughput": {"CPU": [], "GPU": [], "NPU": [], "NVIDIA": []}, "gen": {"CPU": [], "GPU": [], "NPU": [], "NVIDIA": []}, "last": {}, "warn": None}
PMODE_STATE = {"CPU": {"mode": "LATENCY", "stable": 0}, "GPU": {"mode": "LATENCY", "stable": 0}, "NPU": {"mode": "LATENCY", "stable": 0}, "NVIDIA": {"mode": "LATENCY", "stable": 0}}

def _choose_perf_mode(config, device):
    key = device if device in PERF["lat"] else ("NPU" if "NPU" in device else ("GPU" if "GPU" in device else ("CPU" if "CPU" in device else "CPU")))
    tt = PERF["ttft"].get(key) or []
    th = PERF["throughput"].get(key) or []
    lat = PERF["lat"].get(key) or []
    def _avg(a):
        return float(sum(a)/len(a)) if a else None
    def _var(a):
        if not a:
            return None
        m = _avg(a)
        return float(sum((x-m)*(x-m) for x in a)/len(a))
    tt_m = _avg(tt) or 0.0
    tt_v = _var(tt) or 0.0
    th_m = _avg(th) or 0.0
    lat_m = _avg(lat) or 0.0
    max_new = int(config.get("max_new_tokens")) if config.get("max_new_tokens") is not None else 512
    num_req = int(config.get("num_requests")) if config.get("num_requests") is not None else 1
    want_thr = (max_new >= 512 or num_req > 1) or (th_m >= 1.0 and tt_m >= 800)
    want_lat = tt_m >= 1500 and th_m < 2.0
    st = PMODE_STATE.get(key)
    cur = st["mode"]
    if want_thr and cur != "THROUGHPUT":
        st["stable"] += 1
        if st["stable"] >= 3:
            st["mode"] = "THROUGHPUT"
            st["stable"] = 0
    elif want_lat and cur != "LATENCY":
        st["stable"] += 1
        if st["stable"] >= 3:
            st["mode"] = "LATENCY"
            st["stable"] = 0
    else:
        st["stable"] = max(0, st["stable"]-1)
    return st["mode"]

app = APIFlask(
    __name__,
    title="AI Funland",
    version="V0.0.1 Dev",
    static_folder=str(BASE_DIR / "web"),
    static_url_path="/static",
)

@app.get("/")
def index():
    return app.send_static_file("index.html")

 

@app.get("/api/system/info")
def api_system_info():
    return jsonify(get_info())

@app.get("/api/models/list")
def api_models_list():
    return jsonify({"items": list_models(BASE_DIR)})

@app.get("/api/models/is_loaded")
def api_models_is_loaded():
    model_id = request.args.get("model_id")
    device = request.args.get("device", "CPU")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    model_dir = MODELS_DIR / model_id.replace("/", "__")
    ok = is_model_loaded(model_dir, device)
    return jsonify({"loaded": bool(ok)})

def _get_cache_dir():
    import os
    v = os.environ.get("AIFUNLAND_CACHE_DIR")
    return Path(v) if v else (BASE_DIR / "tmp")

def _run_modelscope_download(task_id, model_id, local_dir, include=None, exclude=None, revision=None):
    import sys as _sys
    import re as _re
    exe = str((Path(_sys.executable).parent / "Scripts" / "modelscope.exe"))
    pyexe = str(_sys.executable)
    use_exe = Path(exe).exists()
    base_cmd = ([exe] if use_exe else [pyexe, "-m", "modelscope"]) + ["download", "--model", model_id, "--local_dir", str(local_dir)]
    if revision:
        base_cmd += ["--revision", revision]
    if include:
        base_cmd += ["--include"] + include
    if exclude:
        base_cmd += ["--exclude"] + exclude
    try:
        cache_dir = _get_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        task_store.update(task_id, status="running", progress=1, message=f"starting: cache={cache_dir}")
        proc = subprocess.Popen(base_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(BASE_DIR), env={**_os_environ(cache_dir)})
        for line in proc.stdout:
            s = line.strip()
            if not s:
                continue
            if ("uvicorn" in s) or ("UvicornWorker" in s):
                continue
            task_store.update(task_id, message=s)
            m = _re.search(r"(\d{1,3})%", s)
            if m:
                try:
                    pct = int(m.group(1))
                    task_store.update(task_id, progress=max(0, min(100, pct)))
                except Exception:
                    pass
        code = proc.wait()
        if code == 0:
            task_store.complete(task_id, result=str(local_dir))
        else:
            parts = model_id.split("/")
            if len(parts) == 2 and parts[0] != parts[0].lower():
                alt_id = parts[0].lower() + "/" + parts[1]
                alt_cmd = base_cmd.copy()
                i = alt_cmd.index("--model")
                alt_cmd[i+1] = alt_id
                task_store.update(task_id, message="retry")
                proc2 = subprocess.Popen(alt_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(BASE_DIR), env={**_os_environ(cache_dir)})
                for line in proc2.stdout:
                    s2 = line.strip()
                    if not s2:
                        continue
                    if ("uvicorn" in s2) or ("UvicornWorker" in s2):
                        continue
                    task_store.update(task_id, message=s2)
                    m2 = _re.search(r"(\d{1,3})%", s2)
                    if m2:
                        try:
                            pct2 = int(m2.group(1))
                            task_store.update(task_id, progress=max(0, min(100, pct2)))
                        except Exception:
                            pass
                code2 = proc2.wait()
                if code2 == 0:
                    task_store.complete(task_id, result=str(local_dir))
                    return
            try:
                from modelscope import snapshot_download
                task_store.update(task_id, message="api_download")
                def _run_api():
                    p = snapshot_download(model_id, cache_dir=str(cache_dir), revision=revision)
                    src = Path(p)
                    if local_dir.exists():
                        try:
                            shutil.rmtree(local_dir)
                        except Exception:
                            pass
                    shutil.move(str(src), str(local_dir))
                t = threading.Thread(target=_run_api, daemon=True)
                t.start()
                def _monitor_progress():
                    import time
                    pct = 3
                    while t.is_alive():
                        try:
                            task_store.update(task_id, status="running", progress=pct, message="api_download")
                            pct = pct + 2 if pct < 40 else (pct + 3 if pct < 75 else (pct + 1))
                            if pct > 95:
                                pct = 95
                        except Exception:
                            pass
                        time.sleep(1)
                mon = threading.Thread(target=_monitor_progress, daemon=True)
                mon.start()
                t.join()
                task_store.complete(task_id, result=str(local_dir))
            except Exception as e2:
                task_store.update(task_id, status="error", error=f"exit {code}: {str(e2)}")
    except Exception as e:
        task_store.update(task_id, status="error", error=str(e))

def _os_environ(cache_dir: Path = None):
    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if cache_dir is None:
        cache_dir = _get_cache_dir()
    try:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    env["MODELSCOPE_CACHE"] = str(cache_dir)
    env["MS_CACHE_HOME"] = str(cache_dir)
    return env

@app.post("/api/models/download")
def api_models_download():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    include = data.get("include")
    exclude = data.get("exclude")
    revision = data.get("revision")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    dest = MODELS_DIR / model_id.replace("/", "__")
    task_id = task_store.create("download")
    t = threading.Thread(target=_run_modelscope_download, args=(task_id, model_id, dest, include, exclude, revision), daemon=True)
    t.start()
    return jsonify({"task_id": task_id})

@app.get("/api/tasks/<task_id>")
def api_task_status(task_id):
    t = task_store.get(task_id)
    if not t:
        return jsonify({"error": "not_found"}), 404
    return jsonify(t)

@app.post("/api/models/quantize")
def api_models_quantize():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    mode = data.get("mode", "int8")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    src = MODELS_DIR / model_id.replace("/", "__")
    if not src.exists():
        return jsonify({"error": "model_not_found"}), 404
    out = MODELS_DIR / (src.name + f"_quant_{mode}")
    out.mkdir(parents=True, exist_ok=True)
    task_id = task_store.create("quantize")

    def _run():
        task_store.update(task_id, status="running", message="quantizing")
        try:
            result = quantize_model(src, out, mode)
            try:
                release_model(src)
            except Exception:
                pass
            try:
                import shutil
                shutil.rmtree(src)
            except Exception:
                pass
            task_store.complete(task_id, result=result)
        except Exception as e:
            msg = str(e)
            if ("does not recognize this architecture" in msg) or ("model type" in msg and "qwen3" in msg.lower()):
                msg = "当前模型架构(qwen3)不受当前 Transformers/Optimum 版本支持，建议：1) 升级 Transformers/Optimum 至支持 qwen3 的版本 2) 更换为兼容模型 (如 qwen/Qwen2.5-0.5B/1.5B/3B-Instruct)。"
            task_store.update(task_id, status="error", error=msg)

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"task_id": task_id})

@app.delete("/api/models/delete")
def api_models_delete():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    target = MODELS_DIR / model_id.replace("/", "__")
    if is_model_in_use(target):
        return jsonify({
            "error_code": "model_in_use",
            "friendly": True,
            "message": "模型正在使用，无法删除。请先释放模型后再删除。",
            "action": "release_then_delete"
        }), 409
    try:
        ok = delete_model(BASE_DIR, model_id.replace("/", "__"))
        return jsonify({"ok": ok})
    except Exception as e:
        return jsonify({
            "error_code": "delete_failed",
            "friendly": True,
            "message": "删除失败，可能由于文件占用。请释放模型后重试。",
            "detail": str(e)
        }), 409

@app.post("/api/models/release")
def api_models_release():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    target = MODELS_DIR / model_id.replace("/", "__")
    release_model(target)
    return jsonify({"ok": True})

@app.post("/api/infer/chat")
def api_infer_chat():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    device = data.get("device", "CPU")
    prompt = data.get("prompt")
    config = data.get("config", {})
    if not model_id or not prompt:
        return jsonify({"error": "model_id and prompt required"}), 400
    model_dir = MODELS_DIR / model_id.replace("/", "__")
    if not model_dir.exists():
        return jsonify({"error": "model_not_found"}), 404
    try:
        import time
        t0 = time.time()
        if str(config.get("perf_mode", "")).upper() == "AUTO":
            config["perf_mode"] = _choose_perf_mode(config, device)
        pipe = load_pipeline(model_dir, device, config)
        output, metrics = generate(pipe, prompt, config)
        dt = int((time.time() - t0) * 1000)
        key = device if device in PERF["lat"] else ("NPU" if "NPU" in device else ("GPU" if "GPU" in device else ("CPU" if "CPU" in device else None)))
        arr = PERF["lat"].get(key)
        if arr is not None:
            arr.append(dt)
            if len(arr) > 30:
                del arr[:len(arr)-30]
        PERF["last"] = {"device": device, "latency_ms": dt, "metrics": metrics}
        if metrics and key:
            try:
                if metrics.get("ttft_ms"):
                    PERF["ttft"][key].append(metrics["ttft_ms"]) 
                if metrics.get("tpot_ms"):
                    PERF["tpot"][key].append(metrics["tpot_ms"]) 
                if metrics.get("throughput_tps"):
                    PERF["throughput"][key].append(metrics["throughput_tps"]) 
                if metrics.get("generate_ms"):
                    PERF["gen"][key].append(metrics["generate_ms"]) 
                for k in ("ttft","tpot","throughput","gen"):
                    if len(PERF[k][key]) > 30:
                        del PERF[k][key][:len(PERF[k][key])-30]
            except Exception:
                pass
        cpu_avg = sum(PERF["lat"]["CPU"]) / len(PERF["lat"]["CPU"]) if PERF["lat"]["CPU"] else None
        npu_avg = sum(PERF["lat"]["NPU"]) / len(PERF["lat"]["NPU"]) if PERF["lat"]["NPU"] else None
        PERF["warn"] = None
        if (device == "NPU" or ("NPU" in device)) and cpu_avg is not None and npu_avg is not None and npu_avg > cpu_avg * 1.2:
            PERF["warn"] = "npu_slower_than_cpu"
        return jsonify({"output": output, "metrics": metrics})
    except Exception as e:
        msg = str(e)
        if ("does not recognize this architecture" in msg) or ("model type" in msg and "qwen3" in msg.lower()):
            return jsonify({
                "error_code": "unsupported_architecture",
                "friendly": True,
                "message": "当前模型架构(qwen3)不受当前 Transformers/Optimum 版本支持，建议：1) 升级 Transformers/Optimum 至支持 qwen3 的版本 2) 更换为兼容模型 (如 qwen/Qwen2.5-0.5B/1.5B/3B-Instruct)",
                "device": device
            }), 200
        if device in ("NPU", "GPU") and ("Could not find a model" in msg or "Jenkins" in msg or "not supported" in msg):
            return jsonify({
                "error_code": "incompatible_acceleration",
                "friendly": True,
                "message": "当前模型不支持硬件加速功能，建议：1) 更换为兼容模型 2) 使用CPU模式运行",
                "docs_link": "https://github.com/openvinotoolkit/openvino.genai",
                "recommended": [
                    "qwen/Qwen2.5-0.5B-Instruct",
                    "qwen/Qwen2.5-1.5B-Instruct",
                    "qwen/Qwen2.5-3B-Instruct"
                ],
                "device": device
            }), 200
        return jsonify({"error": msg}), 500

@app.post("/api/infer/preload")
def api_infer_preload():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    device = data.get("device", "CPU")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    model_dir = MODELS_DIR / model_id.replace("/", "__")
    if not model_dir.exists():
        return jsonify({"error": "model_not_found"}), 404
    try:
        _ = load_pipeline(model_dir, device, data.get("config", {}))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.get("/api/infer/stream")
def api_infer_stream():
    model_id = request.args.get("model_id")
    device = request.args.get("device", "CPU")
    prompt = request.args.get("prompt")
    cfg_s = request.args.get("config")
    try:
        config = json.loads(cfg_s) if cfg_s else {}
    except Exception:
        config = {}
    if not model_id or not prompt:
        def _err():
            yield "event: error\n"
            yield "data: {\"error\": \"model_id and prompt required\"}\n\n"
        return app.response_class(_err(), mimetype="text/event-stream")
    model_dir = MODELS_DIR / model_id.replace("/", "__")
    if not model_dir.exists():
        def _err2():
            yield "event: error\n"
            yield "data: {\"error\": \"model_not_found\"}\n\n"
        return app.response_class(_err2(), mimetype="text/event-stream")
    def _gen():
        import time
        yield "event: start\n"
        yield "data: {}\n\n"
        t0 = time.time()
        if str(config.get("perf_mode", "")).upper() == "AUTO":
            config["perf_mode"] = _choose_perf_mode(config, device)
        pipe = load_pipeline(model_dir, device, config)
        output, metrics = generate(pipe, prompt, config)
        dt = int((time.time() - t0) * 1000)
        key = device if device in PERF["lat"] else ("NPU" if "NPU" in device else ("GPU" if "GPU" in device else ("CPU" if "CPU" in device else None)))
        arr = PERF["lat"].get(key)
        if arr is not None:
            arr.append(dt)
            if len(arr) > 30:
                del arr[:len(arr)-30]
        PERF["last"] = {"device": device, "latency_ms": dt, "metrics": metrics}
        if metrics and key:
            try:
                if metrics.get("ttft_ms"):
                    PERF["ttft"][key].append(metrics["ttft_ms"]) 
                if metrics.get("tpot_ms"):
                    PERF["tpot"][key].append(metrics["tpot_ms"]) 
                if metrics.get("throughput_tps"):
                    PERF["throughput"][key].append(metrics["throughput_tps"]) 
                if metrics.get("generate_ms"):
                    PERF["gen"][key].append(metrics["generate_ms"]) 
                for k in ("ttft","tpot","throughput","gen"):
                    if len(PERF[k][key]) > 30:
                        del PERF[k][key][:len(PERF[k][key])-30]
            except Exception:
                pass
        cpu_avg = sum(PERF["lat"]["CPU"]) / len(PERF["lat"]["CPU"]) if PERF["lat"]["CPU"] else None
        npu_avg = sum(PERF["lat"]["NPU"]) / len(PERF["lat"]["NPU"]) if PERF["lat"]["NPU"] else None
        PERF["warn"] = None
        if (device == "NPU" or ("NPU" in device)) and cpu_avg is not None and npu_avg is not None and npu_avg > cpu_avg * 1.2:
            PERF["warn"] = "npu_slower_than_cpu"
        s = str(output or "")
        try:
            step = 80
            i = 0
            while i < len(s):
                seg = s[i:i+step]
                yield "event: chunk\n"
                yield "data: " + json.dumps({"text": seg}) + "\n\n"
                i += step
            yield "event: final\n"
            yield "data: " + json.dumps({"text": s, "metrics": metrics}) + "\n\n"
        except Exception:
            yield "event: final\n"
            yield "data: " + json.dumps({"text": s, "metrics": metrics}) + "\n\n"
    return app.response_class(_gen(), mimetype="text/event-stream")
@app.get("/api/perf")
def api_perf():
    def avg(a):
        return float(sum(a)/len(a)) if a else None
    return jsonify({
        "avg": {k: (int(avg(v)) if avg(v) is not None else None) for k, v in PERF["lat"].items()},
        "avg_details": {
            "ttft": {k: avg(v) for k, v in PERF["ttft"].items()},
            "tpot": {k: avg(v) for k, v in PERF["tpot"].items()},
            "throughput": {k: avg(v) for k, v in PERF["throughput"].items()},
            "generate": {k: avg(v) for k, v in PERF["gen"].items()},
        },
        "last": PERF["last"],
        "warn": PERF["warn"]
    })

def run():
    app.run(host="127.0.0.1", port=8000)

if __name__ == "__main__":
    run()