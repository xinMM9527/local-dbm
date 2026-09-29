"""Configuration file management - plain JSON storage."""
import json
import uuid
from pathlib import Path
from typing import Any

# Use project-local data dir; override with DBM_CONFIG_DIR env var for production
import os
CONFIG_DIR = Path(os.environ.get("DBM_CONFIG_DIR", str(Path(__file__).resolve().parent.parent / "data")))
CONFIG_FILE = CONFIG_DIR / "config.json"


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {"connections": [], "query_history": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict[str, Any]):
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def generate_id() -> str:
    return uuid.uuid4().hex[:12]
