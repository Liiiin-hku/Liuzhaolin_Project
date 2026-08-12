#!/usr/bin/env python3
"""Stable repository-root entry point for the per-sensor training bundler."""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = PROJECT_ROOT / "custom_9dtact" / "tools" / "prepare_training_bundle.py"


def main():
    if not IMPLEMENTATION.is_file():
        print("Training-bundle implementation not found: {}".format(IMPLEMENTATION))
        return 1
    command = [sys.executable, str(IMPLEMENTATION)] + sys.argv[1:]
    return subprocess.call(command, cwd=str(PROJECT_ROOT / "custom_9dtact"))


if __name__ == "__main__":
    sys.exit(main())
