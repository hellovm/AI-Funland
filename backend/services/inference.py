from pathlib import Path

_pipe_cache = {}

def load_pipeline(model_dir: Path, device: str, config: dict | None = None):
    import openvino_genai as ov_genai
    # ensure tokenizer IR exists in model_dir; if missing, try to convert from HF tokenizer
    tok_xml = model_dir / "openvino_tokenizer.xml"
    if not tok_xml.exists():
        try:
            from transformers import AutoTokenizer
            from openvino_tokenizers import convert_tokenizer
            import openvino as ov
            src_dir = model_dir
            has_tok = any((src_dir / n).exists() for n in ("tokenizer.json","tokenizer_config.json","vocab.json","merges.txt"))
            if not has_tok:
                base_name = model_dir.name.split("_quant_")[0]
                cand = model_dir.parent / base_name
                if any((cand / n).exists() for n in ("tokenizer.json","tokenizer_config.json","vocab.json","merges.txt")):
                    src_dir = cand
            hf_tok = AutoTokenizer.from_pretrained(str(src_dir), trust_remote_code=True)
            ov_tok, ov_detok = convert_tokenizer(hf_tok, with_detokenizer=True)
            ov.save_model(ov_tok, str(tok_xml))
            ov.save_model(ov_detok, str(model_dir / "openvino_detokenizer.xml"))
        except Exception:
            pass
    import os
    try:
        from pathlib import Path as _P
        _base = os.environ.get("AIFUNLAND_CACHE_DIR") or str(_P.cwd() / "tmp")
        _cd = _P(_base) / "ov_cache"
        _cd.mkdir(parents=True, exist_ok=True)
        os.environ["OV_CACHE_DIR"] = str(_cd)
    except Exception:
        pass
    if config and (device == "NPU" or ("NPU" in device)):
        try:
            from openvino.runtime import Core as _Core
            _core = _Core()
            _devs = _core.available_devices
            if config.get("auto_multi"):
                if any(d.startswith("GPU") for d in _devs):
                    device = "MULTI:NPU,GPU"
                elif "CPU" in _devs:
                    device = "MULTI:NPU,CPU"
        except Exception:
            pass
    if device == "NPU" or ("NPU" in device):
        os.environ.setdefault("OV_NUM_STREAMS", "1")
    import os
    # apply device-specific performance hints
    perf_mode = None
    if config:
        perf_mode = config.get("perf_mode")
    if (perf_mode is None) or (str(perf_mode).upper() == "AUTO"):
        try:
            max_new = int(config.get("max_new_tokens")) if config and (config.get("max_new_tokens") is not None) else 512
            num_req = int(config.get("num_requests")) if config and (config.get("num_requests") is not None) else 1
            perf_mode = "THROUGHPUT" if (max_new >= 512 or num_req > 1) else "LATENCY"
        except Exception:
            perf_mode = "LATENCY"
    if device == "NPU" or ("NPU" in device):
        streams = None
        if config:
            streams = config.get("npu_streams")
        tiles = None
        num_req = None
        if config:
            tiles = config.get("npu_tiles")
            num_req = config.get("num_requests")
        if streams:
            os.environ["OV_NUM_STREAMS"] = str(streams)
        else:
            os.environ.setdefault("OV_NUM_STREAMS", "1" if perf_mode in (None, "LATENCY") else "2")
        if perf_mode in ("LATENCY", "THROUGHPUT", "CUMULATIVE_THROUGHPUT"):
            os.environ["OV_PERFORMANCE_HINT"] = perf_mode
        else:
            os.environ.setdefault("OV_PERFORMANCE_HINT", "LATENCY")
        try:
            ov_mode = "latency" if perf_mode in (None, "LATENCY") else "efficiency"
            os.environ.setdefault("NPU_COMPILATION_MODE_PARAMS", f"optimization-level=2 performance-hint-override={ov_mode}")
            os.environ.setdefault("NPU_TURBO", "YES")
            os.environ.setdefault("NPU_COMPILER_DYNAMIC_QUANTIZATION", "YES")
            # prefer sequential in latency mode, allow concurrency in throughput mode
            os.environ.setdefault("NPU_RUN_INFERENCES_SEQUENTIALLY", "YES" if ov_mode == "latency" else "NO")
            if tiles:
                os.environ["NPU_TILES"] = str(tiles)
            if num_req:
                os.environ["OV_HINT_NUM_REQUESTS"] = str(num_req)
            # detect NPU architecture to set tiles and num_requests
            try:
                from openvino.runtime import Core
                core = Core()
                arch = core.get_property("NPU", "DEVICE_ARCHITECTURE")
                arch_s = str(arch).lower()
                if "4000" in arch_s:
                    os.environ.setdefault("NPU_TILES", "4")
                    if perf_mode in ("THROUGHPUT", "CUMULATIVE_THROUGHPUT"):
                        os.environ.setdefault("OV_HINT_NUM_REQUESTS", "8")
                    else:
                        os.environ.setdefault("OV_HINT_NUM_REQUESTS", "1")
                else:
                    os.environ.setdefault("NPU_TILES", "2")
                    if perf_mode in ("THROUGHPUT", "CUMULATIVE_THROUGHPUT"):
                        os.environ.setdefault("OV_HINT_NUM_REQUESTS", "4")
                    else:
                        os.environ.setdefault("OV_HINT_NUM_REQUESTS", "1")
            except Exception:
                # fallback num_requests for unknown arch
                os.environ.setdefault("OV_HINT_NUM_REQUESTS", "1" if ov_mode == "latency" else "4")
            os.environ.setdefault("OV_ENABLE_PROFILING", "YES")
        except Exception:
            pass
    elif device == "GPU" or ("GPU" in device):
        streams = None
        if config:
            streams = config.get("gpu_streams")
        if streams:
            os.environ["OV_NUM_STREAMS"] = str(streams)
        else:
            os.environ.setdefault("OV_NUM_STREAMS", "1" if perf_mode in (None, "LATENCY") else "2")
        if perf_mode in ("LATENCY", "THROUGHPUT", "CUMULATIVE_THROUGHPUT"):
            os.environ["OV_PERFORMANCE_HINT"] = perf_mode
    elif device == "CPU" or ("CPU" in device):
        try:
            nt = os.cpu_count() or 4
            os.environ.setdefault("OV_INFERENCE_NUM_THREADS", str(max(2, nt // 2)))
        except Exception:
            pass
    key = (str(model_dir), device)
    p = _pipe_cache.get(key)
    if p is None:
        try:
            if device.startswith("MULTI:"):
                devs = device.split(":",1)[1]
                os.environ.setdefault("MULTI_DEVICE_PRIORITIES", devs)
                if perf_mode in ("CUMULATIVE_THROUGHPUT", "THROUGHPUT"):
                    os.environ.setdefault("OV_PERFORMANCE_HINT", perf_mode)
                try:
                    p = ov_genai.LLMPipeline(str(model_dir), f"MULTI:{devs}")
                except Exception:
                    os.environ.setdefault("AUTO_DEVICE_PRIORITY", devs)
                    p = ov_genai.LLMPipeline(str(model_dir), f"AUTO:{devs}")
            elif device.startswith("AUTO:"):
                devs = device.split(":",1)[1]
                os.environ.setdefault("AUTO_DEVICE_PRIORITY", devs)
                p = ov_genai.LLMPipeline(str(model_dir), device)
            else:
                p = ov_genai.LLMPipeline(str(model_dir), device)
        except Exception:
            fallback = None
            if "NPU" in device:
                fallback = "NPU"
            elif "GPU" in device:
                fallback = "GPU"
            elif "CPU" in device:
                fallback = "CPU"
            else:
                fallback = device
            p = ov_genai.LLMPipeline(str(model_dir), fallback)
        _pipe_cache[key] = p
    return p

def is_model_in_use(model_dir: Path) -> bool:
    s = str(model_dir)
    for (md, _dev), _p in list(_pipe_cache.items()):
        if md == s:
            return True
    return False

def release_model(model_dir: Path):
    s = str(model_dir)
    for k in list(_pipe_cache.keys()):
        if k[0] == s:
            try:
                _pipe_cache[k] = None
            except Exception:
                pass
            try:
                del _pipe_cache[k]
            except Exception:
                pass

def is_model_loaded(model_dir: Path, device: str) -> bool:
    return _pipe_cache.get((str(model_dir), device)) is not None

def generate(pipe, prompt: str, config: dict):
    if config:
        gen = pipe.get_generation_config()
        if "max_new_tokens" in config:
            gen.max_new_tokens = int(config["max_new_tokens"])
        if "temperature" in config:
            gen.temperature = float(config["temperature"])
        if "top_k" in config:
            gen.top_k = int(config["top_k"])
        if "top_p" in config:
            gen.top_p = float(config["top_p"])
        if "repetition_penalty" in config:
            gen.repetition_penalty = float(config["repetition_penalty"])
        res = pipe.generate([prompt], gen)
    else:
        res = pipe.generate([prompt])
    try:
        text = res.text if hasattr(res, "text") else (res[0] if isinstance(res, (list, tuple)) and len(res)>0 else str(res))
    except Exception:
        text = str(res)
    metrics = None
    try:
        pm = getattr(res, "perf_metrics", None)
        if pm is not None:
            metrics = {
                "generate_ms": float(getattr(pm.get_generate_duration(), "mean", None) or 0.0),
                "ttft_ms": float(getattr(pm.get_ttft(), "mean", None) or 0.0),
                "tpot_ms": float(getattr(pm.get_tpot(), "mean", None) or 0.0),
                "throughput_tps": float(getattr(pm.get_throughput(), "mean", None) or 0.0),
            }
    except Exception:
        metrics = None
    return text, metrics

def quantize_model(model_dir: Path, save_dir: Path, mode: str = "int8"):
    from optimum.intel.openvino import OVModelForCausalLM
    from optimum.intel.openvino import OVWeightQuantizationConfig
    bits = 4 if str(mode).lower() == "int4" else 8
    qc = OVWeightQuantizationConfig(bits=bits)
    m = OVModelForCausalLM.from_pretrained(str(model_dir), quantization_config=qc, trust_remote_code=True)
    m.save_pretrained(str(save_dir))
    # ensure tokenizer IR exists in save_dir by converting from source HF tokenizer
    try:
        from transformers import AutoTokenizer
        from openvino_tokenizers import convert_tokenizer
        import openvino as ov
        hf_tok = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
        ov_tok, ov_detok = convert_tokenizer(hf_tok, with_detokenizer=True)
        ov.save_model(ov_tok, str(save_dir / "openvino_tokenizer.xml"))
        ov.save_model(ov_detok, str(save_dir / "openvino_detokenizer.xml"))
    except Exception:
        pass
    return str(save_dir)