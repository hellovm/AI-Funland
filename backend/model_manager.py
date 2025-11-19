import os
import uuid
import threading
import time
import shutil
from typing import Dict
from openvino_genai import LLMPipeline
 

class ModelManager:
    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        self.downloads: Dict[str, Dict] = {}
        self.quant_jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.chat_sem = threading.Semaphore(1)
        self.metrics: Dict[str, float] = {}

    def list_models(self):
        items = []
        for name in os.listdir(self.models_dir):
            p = os.path.join(self.models_dir, name)
            if os.path.isdir(p):
                items.append({'id': name, 'path': p})
        return items

    def _model_path(self, model_id: str):
        safe = model_id.replace('/', '__')
        return os.path.join(self.models_dir, safe)

    def enqueue_download(self, model_id: str):
        task_id = str(uuid.uuid4())
        with self.lock:
            self.downloads[task_id] = {
                'model_id': model_id,
                'status': 'queued',
                'progress': 0,
                'speed_bps': 0,
                'eta_seconds': None,
                'downloaded_bytes': 0,
                'total_bytes': None,
                'paused': False
            }
        t = threading.Thread(target=self._download_worker, args=(task_id,), daemon=True)
        t.start()
        return task_id

    def _download_worker(self, task_id: str):
        from modelscope.hub.snapshot_download import snapshot_download
        from modelscope.hub.api import HubApi
        from modelscope.hub.file_download import model_file_download
        info = self.downloads.get(task_id)
        if not info:
            return
        model_id = info['model_id']
        info['status'] = 'running'
        dest = self._model_path(model_id)
        os.makedirs(dest, exist_ok=True)
        api = HubApi()
        try:
            repo = api.repo_info(model_id)
            siblings = repo.get('siblings') or []
            total = 0
            for s in siblings:
                sz = int(s.get('size') or 0)
                total += sz
            info['total_bytes'] = total if total > 0 else None
        except Exception:
            info['total_bytes'] = None
        start_time = time.time()
        try:
            if info['total_bytes']:
                for s in siblings:
                    if info.get('paused'):
                        while info.get('paused'):
                            time.sleep(0.2)
                    fname = s.get('rfilename') or s.get('filename') or s.get('path')
                    if not fname:
                        continue
                    try:
                        model_file_download(model_id, fname, dest, progress_callbacks=[self._make_progress_cb(info, start_time)])
                    except TypeError:
                        model_file_download(model_id, fname, dest)
                    info['downloaded_bytes'] = self._dir_size(dest)
                    if info['total_bytes']:
                        info['progress'] = int(info['downloaded_bytes'] * 100 / info['total_bytes'])
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        info['speed_bps'] = int(info['downloaded_bytes'] / elapsed)
                        if info['total_bytes'] and info['speed_bps'] > 0:
                            remaining = info['total_bytes'] - info['downloaded_bytes']
                            info['eta_seconds'] = int(remaining / info['speed_bps'])
                info['status'] = 'completed'
                info['path'] = dest
            else:
                path = snapshot_download(model_id, cache_dir=dest)
                info['downloaded_bytes'] = self._dir_size(dest)
                info['progress'] = 100
                info['speed_bps'] = int(info['downloaded_bytes'] / max(1, time.time() - start_time))
                info['eta_seconds'] = 0
                info['status'] = 'completed'
                info['path'] = path
        except Exception as e:
            info['status'] = 'error'
            info['error'] = str(e)
        try:
            logdir = os.path.join(os.path.dirname(self.models_dir), 'logs')
            os.makedirs(logdir, exist_ok=True)
            with open(os.path.join(logdir, 'app.log'), 'a', encoding='utf-8') as f:
                ts = time.strftime('%Y-%m-%dT%H:%M:%S')
                f.write(f"[{ts}] download {model_id} status={info.get('status')} progress={info.get('progress')} speed={info.get('speed_bps')}\n")
        except Exception:
            pass

    def _dir_size(self, d: str):
        total = 0
        for root, _, files in os.walk(d):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        return total

    def get_download_status(self, task_id: str):
        return self.downloads.get(task_id)

    def set_download_paused(self, task_id: str, paused: bool):
        info = self.downloads.get(task_id)
        if info:
            info['paused'] = paused
            return True
        return False

    def _make_progress_cb(self, info: Dict, start_time: float):
        class DownloadProgress:
            def __init__(self, file_name, file_size):
                self.file_name = file_name
                self.file_size = file_size or 0
                self.acc = 0
            def __call__(self, chunk):
                try:
                    if info.get('paused'):
                        while info.get('paused'):
                            time.sleep(0.2)
                    size = int(chunk) if isinstance(chunk, (int, float)) else 0
                    self.acc += size
                    info['downloaded_bytes'] = info.get('downloaded_bytes', 0) + size
                    if info.get('total_bytes'):
                        info['progress'] = int(info['downloaded_bytes'] * 100 / info['total_bytes'])
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        info['speed_bps'] = int(info['downloaded_bytes'] / elapsed)
                        if info.get('total_bytes') and info['speed_bps'] > 0:
                            remaining = info['total_bytes'] - info['downloaded_bytes']
                            info['eta_seconds'] = int(remaining / info['speed_bps'])
                except Exception:
                    pass
            def update(self, chunk):
                self.__call__(chunk)
        return DownloadProgress

    def enqueue_quantize(self, model_id: str, mode: str, device: str, config: Dict):
        job_id = str(uuid.uuid4())
        with self.lock:
            self.quant_jobs[job_id] = {'model_id': model_id, 'mode': mode, 'device': device, 'status': 'queued', 'config': config}
        t = threading.Thread(target=self._quantize_worker, args=(job_id,), daemon=True)
        t.start()
        return job_id

    def _quantize_worker(self, job_id: str):
        job = self.quant_jobs.get(job_id)
        if not job:
            return
        job['status'] = 'running'
        model_id = job['model_id']
        mode = job['mode']
        dest = os.path.join(self._model_path(model_id), mode)
        os.makedirs(dest, exist_ok=True)
        try:
            from optimum.intel.openvino import OVModelForCausalLM, OVQuantizationConfig, OVWeightQuantizationConfig
            if mode == 'FP16':
                m = OVModelForCausalLM.from_pretrained(model_id, export=True)
                m.save_pretrained(dest)
            else:
                cfg = job.get('config') or {}
                bits = int(cfg.get('bits') or 8)
                method = str(cfg.get('method') or 'weight')
                range_type = str(cfg.get('range') or 'per_tensor')
                dtype = str(cfg.get('weight_dtype') or ('int8' if bits == 8 else 'nf4'))
                dataset = cfg.get('dataset')
                act_dtype = str(cfg.get('activation_dtype') or 'f8e4m3')
                if method == 'mixed':
                    from optimum.intel.openvino import OVMixedQuantizationConfig
                    wcfg = OVWeightQuantizationConfig(bits=bits, dtype=dtype)
                    acfg = OVQuantizationConfig(dtype=act_dtype, dataset=dataset) if dataset else OVQuantizationConfig(dtype=act_dtype)
                    qcfg = OVMixedQuantizationConfig(wcfg, acfg)
                elif method == 'hybrid':
                    qcfg = OVWeightQuantizationConfig(bits=bits, dtype=dtype, quant_method='hybrid')
                else:
                    qcfg = OVWeightQuantizationConfig(bits=bits, dtype=dtype)
                m = OVModelForCausalLM.from_pretrained(model_id, export=True, quantization_config=qcfg)
                m.save_pretrained(dest)
            job['status'] = 'completed'
            job['path'] = dest
        except Exception as e:
            job['status'] = 'error'
            job['error'] = str(e)
        try:
            logdir = os.path.join(os.path.dirname(self.models_dir), 'logs')
            os.makedirs(logdir, exist_ok=True)
            with open(os.path.join(logdir, 'app.log'), 'a', encoding='utf-8') as f:
                ts = time.strftime('%Y-%m-%dT%H:%M:%S')
                f.write(f"[{ts}] quantize {model_id} mode={mode} status={job.get('status')}\n")
        except Exception:
            pass

    def get_quantize_status(self, job_id: str):
        return self.quant_jobs.get(job_id)

    def delete_model(self, model_id: str):
        p = self._model_path(model_id)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
            return True
        return False

    def generate_text(self, model_id: str, prompt: str, device: str, max_new_tokens: int):
        model_dir = self._model_path(model_id)
        if not os.path.isdir(model_dir):
            model_dir = model_id
        start = time.time()
        with self.chat_sem:
            pipe = LLMPipeline(model_dir, device)
            out = pipe.generate(prompt, max_new_tokens=max_new_tokens)
        self.metrics['last_infer_ms'] = (time.time() - start) * 1000.0
        return out