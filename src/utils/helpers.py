import base64
from datetime import datetime
from pathlib import Path
import re
import uuid


def decode_data_url(value: str) -> bytes:
    if not value or "," not in value:
        raise ValueError("A webcam image is required.")
    try:
        return base64.b64decode(value.split(",", 1)[1], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("The captured image is invalid.") from exc


def safe_filename(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_")
    return value[:50] or uuid.uuid4().hex


def export_path(export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir / f"attendance_{datetime.now():%Y%m%d_%H%M%S}.csv"
