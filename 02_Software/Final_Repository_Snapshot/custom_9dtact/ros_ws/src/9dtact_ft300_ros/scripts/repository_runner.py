#!/usr/bin/env python3
"""Locate the checked-out custom_9dtact root and run a repository script."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def project_root() -> Path:
    configured = os.environ.get("NINE_DTACT_PROJECT_ROOT", "").strip()
    if configured:
        root = Path(configured).expanduser().resolve()
        if (root / "force_estimation").is_dir() and (root / "shape-force_ros").is_dir():
            return root
        raise RuntimeError(
            "NINE_DTACT_PROJECT_ROOT does not identify custom_9dtact: {}".format(root)
        )
    for parent in Path(__file__).resolve().parents:
        if (parent / "force_estimation").is_dir() and (parent / "shape-force_ros").is_dir():
            return parent
    raise RuntimeError(
        "Cannot locate custom_9dtact. Set NINE_DTACT_PROJECT_ROOT to its absolute path."
    )


def run(relative_script: str, working_directory: str) -> None:
    root = project_root()
    target = root / relative_script
    if not target.is_file():
        raise RuntimeError("Repository script is missing: {}".format(target))
    os.chdir(str(root / working_directory))
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
