import os
import shutil
from pathlib import Path

def models_root(base: Path) -> Path:
    p = base / "models"
    p.mkdir(parents=True, exist_ok=True)
    return p

def list_models(base: Path):
    root = models_root(base)
    items = []
    for d in root.iterdir():
        if d.is_dir():
            size = 0
            for path, _, files in os.walk(d):
                for f in files:
                    fp = Path(path) / f
                    try:
                        size += fp.stat().st_size
                    except Exception:
                        pass
            items.append({
                "id": d.name,
                "path": str(d),
                "size_bytes": size,
            })
    return items

def delete_model(base: Path, model_id: str):
    root = models_root(base)
    target = root / model_id
    if target.exists():
        shutil.rmtree(target)
        return True
    return False