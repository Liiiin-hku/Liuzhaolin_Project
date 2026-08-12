"""Portable resolution helpers for dataset-relative and legacy index entries."""

import re
from pathlib import Path


def resolve_dataset_entry(dataset_root, value):
    root = Path(dataset_root).expanduser().resolve()
    raw = str(value)
    path = Path(raw).expanduser()
    # Some historical NumPy indexes contain doubled Windows separators. Collapse
    # them before looking for the portable dataset-root anchor.
    normalized = re.sub(r"/+", "/", raw.replace("\\", "/"))
    marker = "/" + root.name + "/"
    if marker in normalized:
        suffix = normalized.split(marker, 1)[1].lstrip("/")
        return root / Path(suffix)
    if path.is_absolute() and path.exists():
        return path
    if path.is_absolute():
        return path
    return root / path
