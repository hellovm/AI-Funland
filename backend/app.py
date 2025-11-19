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
from backend.services.inference import load_pipeline, generate, quantize_model
from backend.utils.tasks import task_store

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = models_root(BASE_DIR)

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

def _get_cache_dir():
    import os
    v = os.environ.get("AIFUNLAND_CACHE_DIR")
    return Path(v) if v else (BASE_DIR / "tmp")

def _run_modelscope_download(task_id, model_id, local_dir, include=None, exclude=None, revision=None):
    import sys as _sys
    import re as _re
    exe = str((Path(_sys.executable).parent / "Scripts" / "modelscope.exe"))
    use_exe = Path(exe).exists()
    base_cmd = [exe if use_exe else "modelscope", "download", "--model", model_id, "--local_dir", str(local_dir)]
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
                task_store.update(task_id, message="api")
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
            task_store.complete(task_id, result=result)
        except Exception as e:
            task_store.update(task_id, status="error", error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"task_id": task_id})

@app.delete("/api/models/delete")
def api_models_delete():
    data = request.get_json(force=True)
    model_id = data.get("model_id")
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    ok = delete_model(BASE_DIR, model_id.replace("/", "__"))
    return jsonify({"ok": ok})

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
        pipe = load_pipeline(model_dir, device)
        output = generate(pipe, prompt, config)
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run():
    app.run(host="127.0.0.1", port=8000)

if __name__ == "__main__":
    run()