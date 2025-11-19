import os
import json
import threading
import time
from apiflask import APIFlask
from flask import request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from .hardware import get_hardware_info, get_available_accelerators
from .model_manager import ModelManager

app = APIFlask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB_DIR = os.path.join(BASE_DIR, 'web')
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(DATA_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

manager = ModelManager(MODELS_DIR)

TORCH_TARGET = '2.4'

def _check_torch_compat():
    info = {'installed': None, 'compatible': False, 'target': TORCH_TARGET}
    try:
        import torch
        v = getattr(torch, '__version__', None)
        info['installed'] = v
        def norm(s):
            import re
            m = re.match(r'^(\d+\.\d+)', s or '')
            return m.group(1) if m else ''
        info['compatible'] = norm(v) == norm(TORCH_TARGET)
    except Exception:
        info['installed'] = None
        info['compatible'] = False
    if not info['compatible']:
        print('[warn] torch version incompatible:', info)
    return info

@app.get('/api/hardware')
def api_hardware():
    return jsonify(get_hardware_info())

@app.get('/api/accelerators')
def api_accelerators():
    return jsonify({'devices': get_available_accelerators()})

@app.get('/api/models')
def api_models():
    return jsonify({'models': manager.list_models()})

@app.post('/api/models/download')
def api_models_download():
    body = request.get_json() or {}
    model_id = body.get('model_id')
    if not model_id:
        return jsonify({'error': 'model_id required'}), 400
    task_id = manager.enqueue_download(model_id)
    return jsonify({'task_id': task_id})

@app.get('/api/models/download/status/<task_id>')
def api_download_status(task_id):
    status = manager.get_download_status(task_id)
    if not status:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(status)

@app.post('/api/models/download/pause')
def api_download_pause():
    body = request.get_json() or {}
    task_id = body.get('task_id')
    ok = manager.set_download_paused(task_id, True)
    return jsonify({'paused': bool(ok)})

@app.post('/api/models/download/resume')
def api_download_resume():
    body = request.get_json() or {}
    task_id = body.get('task_id')
    ok = manager.set_download_paused(task_id, False)
    return jsonify({'resumed': bool(ok)})

@app.post('/api/models/quantize')
def api_quantize():
    body = request.get_json() or {}
    model_id = body.get('model_id')
    mode = body.get('mode')
    device = body.get('device') or 'CPU'
    config = body.get('config') or {}
    if not model_id or mode not in ('FP16', 'INT8'):
        return jsonify({'error': 'model_id and mode FP16/INT8 required'}), 400
    job_id = manager.enqueue_quantize(model_id, mode, device, config)
    return jsonify({'job_id': job_id})

@app.get('/api/models/quantize/status/<job_id>')
def api_quantize_status(job_id):
    status = manager.get_quantize_status(job_id)
    if not status:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(status)

@app.delete('/api/models')
def api_delete_model():
    body = request.get_json() or {}
    model_id = body.get('model_id')
    if not model_id:
        return jsonify({'error': 'model_id required'}), 400
    ok = manager.delete_model(model_id)
    return jsonify({'deleted': bool(ok)})

@app.post('/api/chat')
def api_chat():
    body = request.get_json() or {}
    model_id = body.get('model_id')
    prompt = body.get('prompt')
    device = body.get('device') or 'CPU'
    max_new_tokens = int(body.get('max_new_tokens') or 256)
    if not model_id or not prompt:
        return jsonify({'error': 'model_id and prompt required'}), 400
    try:
        result = manager.generate_text(model_id, prompt, device, max_new_tokens)
        return jsonify({'text': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get('/api/monitor')
def api_monitor():
    return jsonify(manager.metrics)

@app.get('/api/system/check')
def api_system_check():
    return jsonify({'torch': _check_torch_compat()})

@app.get('/')
def index():
    return app.send_static_file('index.html')

app.static_folder = WEB_DIR
app.static_url_path = ''

@app.get('/favicon.ico')
def favicon():
    return ('', 204)

@app.get('/styles.css')
def styles():
    return send_from_directory(WEB_DIR, 'styles.css')

@app.get('/app.js')
def script():
    return send_from_directory(WEB_DIR, 'app.js')

def run():
    app.run(host='127.0.0.1', port=8000)

if __name__ == '__main__':
    run()