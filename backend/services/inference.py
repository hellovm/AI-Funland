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
    def _ordered_gpu_list(core):
        try:
            avail = core.available_devices
        except Exception:
            avail = []
        gpu_devs = [d for d in avail if d.startswith("GPU")]
        if not gpu_devs:
            return []
        info = {}
        for d in gpu_devs:
            try:
                fn = core.get_property(d, "FULL_DEVICE_NAME")
                fn = str(fn) if fn is not None else ""
            except Exception:
                fn = ""
            info[d] = fn
        def _is_igpu(name):
            if not name:
                return False
            ln = name.lower()
            if "(igpu)" in ln or " igpu" in ln:
                return True
            for k in ("integrated", "uhd", "iris", "hd graphics"):
                if k in ln:
                    return True
            return False
        integrated = [d for d, n in info.items() if _is_igpu(n)]
        if integrated:
            try:
                integrated.sort(key=lambda s: int(s.split(".")[1]) if "." in s and s.split(".")[1].isdigit() else 0)
            except Exception:
                pass
            others = [d for d in gpu_devs if d not in integrated]
            return integrated + others
        try:
            import platform, subprocess
            if platform.system() == "Windows":
                out = subprocess.check_output(["wmic", "path", "Win32_VideoController", "get", "Name"], stderr=subprocess.STDOUT, shell=True, text=True)
                controllers = [ln.strip() for ln in out.splitlines() if ln.strip() and not ln.strip().lower().startswith("name")]
                intel_names = [n for n in controllers if "intel" in n.lower()]
                if intel_names:
                    key = intel_names[0].lower()
                    matched = [d for d, fn in info.items() if key in fn.lower()]
                    if matched:
                        others = [d for d in gpu_devs if d not in matched]
                        return matched + others
        except Exception:
            pass
        intel_list = [d for d, fn in info.items() if fn and "intel" in fn.lower()]
        if intel_list:
            others = [d for d in gpu_devs if d not in intel_list]
            return intel_list + others
        return gpu_devs
    try:
        from pathlib import Path as _P
        _base = os.environ.get("AIFUNLAND_CACHE_DIR") or str(_P.cwd() / "tmp")
        _cd = _P(_base) / "ov_cache"
        _cd.mkdir(parents=True, exist_ok=True)
        os.environ["OV_CACHE_DIR"] = str(_cd)
        os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    except Exception:
        pass
    if config and ((device == "NPU") or ("NPU" in device) or device.startswith("AUTO") or device.startswith("MULTI")):
        try:
            from openvino.runtime import Core as _Core
            _core = _Core()
            _devs = _core.available_devices
            ordered_gpus = _ordered_gpu_list(_core)
            igpu = ordered_gpus[0] if ordered_gpus else None
            if config.get("hetero_enable"):
                prio = []
                if "NPU" in _devs:
                    prio.append("NPU")
                if igpu:
                    prio.append(igpu)
                if "CPU" in _devs:
                    prio.append("CPU")
                if prio:
                    device = f"HETERO:{','.join(prio)}"
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
        perf_mode = "CUMULATIVE_THROUGHPUT"
    try:
        if perf_mode in ("LATENCY", "THROUGHPUT", "CUMULATIVE_THROUGHPUT"):
            os.environ["OV_PERFORMANCE_HINT"] = perf_mode
    except Exception:
        pass
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
            os.environ.setdefault("OV_NUM_STREAMS", "2")
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
            else:
                os.environ.setdefault("OV_HINT_NUM_REQUESTS", "6")
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
        def _try(dev_str):
            pipe_cfg = {}
            try:
                from pathlib import Path as _P
                _base = os.environ.get("AIFUNLAND_CACHE_DIR") or str(_P.cwd() / "tmp")
                _cd = _P(_base) / "ov_cache"
                pipe_cfg["CACHE_DIR"] = str(_cd)
            except Exception:
                pass
            try:
                if dev_str.startswith("HETERO:") or dev_str.startswith("MULTI:") or dev_str.startswith("AUTO:"):
                    devs = dev_str.split(":",1)[1] if (":" in dev_str) else ""
                    pipe_cfg["MODEL_DISTRIBUTION_POLICY"] = "PIPELINE_PARALLEL"
                    if devs:
                        pipe_cfg["MULTI_DEVICE_PRIORITIES"] = devs
                        pipe_cfg["DEVICE_PRIORITIES"] = devs
            except Exception:
                pass
            try:
                if config:
                    mpl = config.get("max_prompt_len")
                    mrl = config.get("min_response_len")
                    if mpl:
                        pipe_cfg["MAX_PROMPT_LEN"] = int(mpl)
                    if mrl:
                        pipe_cfg["MIN_RESPONSE_LEN"] = int(mrl)
            except Exception:
                pass
            obj = ov_genai.LLMPipeline(str(model_dir), dev_str, pipe_cfg)
            try:
                setattr(obj, "_af_device_real", dev_str)
            except Exception:
                pass
            return obj
        try:
            if device.startswith("HETERO:"):
                devs = device.split(":",1)[1]
                # map generic GPU to Intel iGPU first when available
                try:
                    from openvino.runtime import Core as _Core
                    _hc = _Core()
                    ordered_gpus = _ordered_gpu_list(_hc)
                    igpu = ordered_gpus[0] if ordered_gpus else None
                    parts = [d.strip() for d in devs.split(",") if d.strip()]
                    mapped = []
                    for d in parts:
                        if d == "GPU" and igpu:
                            mapped.append(igpu)
                        else:
                            mapped.append(d)
                    devs = ",".join(mapped)
                    try:
                        _hc.set_property("HETERO", {"MODEL_DISTRIBUTION_POLICY": "PIPELINE_PARALLEL"})
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    p = _try(f"HETERO:{devs}")
                except Exception as e:
                    try:
                        import os as _os
                        _os.environ.setdefault("AUTO_DEVICE_PRIORITY", devs)
                    except Exception:
                        pass
                    try:
                        from openvino.runtime import Core as _Core
                        _c = _Core()
                        _c.set_property("AUTO", {"PERFORMANCE_HINT": perf_mode, "MODEL_DISTRIBUTION_POLICY": "PIPELINE_PARALLEL"})
                    except Exception:
                        pass
                    try:
                        p = _try(f"AUTO:{devs}")
                    except Exception:
                        p = None
                        raise e
            elif device.startswith("MULTI:"):
                devs = device.split(":",1)[1]
                # map to HETERO with pipeline parallelism, GPU prioritized to Intel iGPU
                try:
                    from openvino.runtime import Core as _Core
                    _hc = _Core()
                    ordered_gpus = _ordered_gpu_list(_hc)
                    igpu = ordered_gpus[0] if ordered_gpus else None
                    parts = [d.strip() for d in devs.split(",") if d.strip()]
                    mapped = []
                    for d in parts:
                        if d == "GPU" and igpu:
                            mapped.append(igpu)
                        else:
                            mapped.append(d)
                    devs = ",".join(mapped)
                    try:
                        _hc.set_property("HETERO", {"MODEL_DISTRIBUTION_POLICY": "PIPELINE_PARALLEL"})
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    p = _try(f"HETERO:{devs}")
                except Exception as e:
                    # fallback to individual devices in order
                    order = [d.strip() for d in devs.split(",") if d.strip()]
                    for d in order:
                        try:
                            p = _try(d)
                            break
                        except Exception:
                            p = None
                    if p is None:
                        raise e
            elif device.startswith("AUTO"):
                devs = None
                if ":" in device:
                    devs = device.split(":",1)[1]
                else:
                    try:
                        from openvino.runtime import Core
                        c = Core()
                        avail = c.available_devices
                        prio = []
                        ordered_gpus = _ordered_gpu_list(c)
                        if ordered_gpus:
                            prio.extend(ordered_gpus)
                        if any(d.startswith("NPU") for d in avail) and (not any(d.startswith("NPU") for d in prio)):
                            prio.append("NPU")
                        if "CPU" in avail and ("CPU" not in prio):
                            prio.append("CPU")
                        devs = ",".join(prio) if prio else None
                    except Exception:
                        devs = None
                if devs:
                    os.environ.setdefault("AUTO_DEVICE_PRIORITY", devs)
                    if perf_mode in ("THROUGHPUT", "CUMULATIVE_THROUGHPUT"):
                        os.environ.setdefault("OV_HINT_NUM_REQUESTS", "4")
                    try:
                        from openvino.runtime import Core
                        c = Core()
                        c.set_property("AUTO", {"PERFORMANCE_HINT": perf_mode, "MODEL_DISTRIBUTION_POLICY": "PIPELINE_PARALLEL"})
                    except Exception:
                        pass
                    try:
                        p = _try(f"AUTO:{devs}")
                    except Exception as e:
                        order = [d.strip() for d in devs.split(",") if d.strip()]
                        for d in order:
                            try:
                                p = _try(d)
                                break
                            except Exception:
                                p = None
                        if p is None:
                            raise e
                else:
                    try:
                        p = _try("AUTO")
                    except Exception:
                        p = _try("CPU")
            else:
                p = _try(device)
            if p:
                try:
                    setattr(p, "_af_device", device)
                except Exception:
                    pass
        except Exception as e:
            msg = str(e)
            order = []
            try:
                from openvino.runtime import Core
                core = Core()
                order = core.available_devices
            except Exception:
                order = ["GPU","CPU"]
            for d in order:
                try:
                    p = _try(d)
                    break
                except Exception:
                    p = None
            if p is None:
                raise
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
        try:
            res = pipe.generate(prompt, gen)
        except Exception:
            res = pipe.generate([prompt], gen)
    else:
        try:
            res = pipe.generate(prompt)
        except Exception:
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

def generate_stream(pipe, prompt: str, config: dict, streamer):
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
        try:
            res = pipe.generate(prompt, gen, streamer=streamer)
        except Exception:
            res = pipe.generate(prompt, streamer=streamer)
    else:
        res = pipe.generate(prompt, streamer=streamer)
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

def web_search(query: str, max_results: int = 5):
    items = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                items.append({
                    "title": r.get("title"),
                    "url": r.get("href") or r.get("url"),
                    "snippet": r.get("body")
                })
    except Exception:
        try:
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            w = DuckDuckGoSearchAPIWrapper()
            for r in w.results(query, max_results=max_results):
                items.append({
                    "title": r.get("title"),
                    "url": r.get("link"),
                    "snippet": r.get("snippet") or r.get("body")
                })
        except Exception:
            items = []
    return items

def augment_with_sources(prompt: str, sources: list[dict], lang: str = "zh"):
    lines = []
    if lang == "zh":
        lines.append("请基于以下网络检索资料进行分析并回答：")
    else:
        lines.append("Please analyze and answer using the following web sources:")
    for i, s in enumerate(sources[:5], 1):
        t = str(s.get("title") or "")
        u = str(s.get("url") or "")
        sn = str(s.get("snippet") or "")
        lines.append(f"[{i}] {t} \n{u} \n{sn}")
    if lang == "zh":
        lines.append("问题：")
    else:
        lines.append("Question:")
    lines.append(prompt)
    if lang == "zh":
        lines.append("要求：先分析再给出结论，并在<final>中输出答案。")
    else:
        lines.append("Instruction: reason first, then output the final answer in <final>.")
    return "\n".join(lines)

def quantize_model(model_dir: Path, save_dir: Path, mode: str = "int8", params: dict | None = None):
    from optimum.intel.openvino import OVModelForCausalLM
    from optimum.intel.openvino import OVWeightQuantizationConfig
    mmode = str(mode).lower()
    if mmode != "int8":
        raise ValueError("int4_disabled")
    qc = OVWeightQuantizationConfig(bits=8)
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