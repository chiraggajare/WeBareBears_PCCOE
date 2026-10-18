"""SHA-256 manifest for trained model files.

Models are saved with joblib (pickle). Unpickling a file can execute code, so the app only loads model
files that (a) live in the local models/ folder and (b) match the checksums written by our own training
run. Never copy model files from untrusted sources - retrain with `python -m src.pipeline` instead.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import MODELS

MANIFEST = MODELS / "manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> dict:
    files = sorted([*MODELS.glob("*.joblib"), MODELS / "folds.json"])
    data = {p.name: sha256(p) for p in files if p.exists()}
    MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


class IntegrityError(RuntimeError):
    pass


def verify(path: Path) -> Path:
    """Return path if it matches the manifest, else raise IntegrityError."""
    path = Path(path).resolve()
    if path.parent != MODELS.resolve():
        raise IntegrityError(f"refusing to load model outside {MODELS}: {path.name}")
    if not MANIFEST.exists():
        raise IntegrityError("models/manifest.json missing - run `python -m src.pipeline` to retrain")
    expected = json.loads(MANIFEST.read_text(encoding="utf-8")).get(path.name)
    if expected is None or sha256(path) != expected:
        raise IntegrityError(f"checksum mismatch for {path.name} - retrain with `python -m src.pipeline`")
    return path


def safe_load(path: Path):
    import joblib
    return joblib.load(verify(path))
