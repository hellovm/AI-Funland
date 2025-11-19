from pathlib import Path

_pipe_cache = {}

def load_pipeline(model_dir: Path, device: str):
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
    key = (str(model_dir), device)
    p = _pipe_cache.get(key)
    if p is None:
        p = ov_genai.LLMPipeline(str(model_dir), device)
        _pipe_cache[key] = p
    return p

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
        return pipe.generate(prompt, gen)
    return pipe.generate(prompt)

def quantize_model(model_dir: Path, save_dir: Path, mode: str = "int8"):
    from optimum.intel.openvino import OVModelForCausalLM
    from optimum.intel.openvino import OVWeightQuantizationConfig, OVQuantizationConfig
    if mode == "int4":
        qc = OVWeightQuantizationConfig(bits=4)
        m = OVModelForCausalLM.from_pretrained(str(model_dir), quantization_config=qc)
        m.save_pretrained(str(save_dir))
        # fallthrough to tokenizer conversion
        # return str(save_dir)
    if mode == "int8":
        qc = OVWeightQuantizationConfig(bits=8)
        m = OVModelForCausalLM.from_pretrained(str(model_dir), quantization_config=qc)
        m.save_pretrained(str(save_dir))
        # fallthrough to tokenizer conversion
        # return str(save_dir)
    qc = OVQuantizationConfig(bits=8)
    m = OVModelForCausalLM.from_pretrained(str(model_dir), quantization_config=qc)
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