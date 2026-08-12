#!/usr/bin/env python3
"""Safely switch the active configuration between Sensor 1 and Sensor 2."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / ".runtime"
BACKUP_DIR = RUNTIME_DIR / "config_backups"
BACKUP_GROUP_LIMIT = 10
BACKUP_PATTERN = re.compile(r"^(?:shape|force)_config_(.+)\.yaml$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Activate the configuration for a specified 9DTact sensor"
    )
    parser.add_argument("--sensor-id", type=int, choices=(1, 2), required=True)
    return parser.parse_args()


def prune_old_backups() -> None:
    """Keep only the ten most recent grouped configuration backups."""
    groups: Dict[str, List[Path]] = {}
    for path in BACKUP_DIR.glob("*_config_*.yaml"):
        match = BACKUP_PATTERN.match(path.name)
        if match:
            groups.setdefault(match.group(1), []).append(path)

    for timestamp in sorted(groups, reverse=True)[BACKUP_GROUP_LIMIT:]:
        for path in groups[timestamp]:
            path.unlink()


def activate(sensor_id: int) -> None:
    configs_dir = PROJECT_ROOT / "configs"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    shape_source = configs_dir / f"shape_sensor_{sensor_id}.yaml"
    force_source = configs_dir / f"force_sensor_{sensor_id}.yaml"
    shape_target = PROJECT_ROOT / "shape_reconstruction" / "shape_config.yaml"
    force_target = PROJECT_ROOT / "force_estimation" / "force_config.yaml"

    for source in (shape_source, force_source):
        if not source.is_file():
            raise SystemExit(f"Missing configuration template: {source}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    for target in (shape_target, force_target):
        if target.is_file():
            backup_name = f"{target.stem}_{timestamp}{target.suffix}"
            shutil.copy2(target, BACKUP_DIR / backup_name)

    shutil.copy2(shape_source, shape_target)
    shutil.copy2(force_source, force_target)
    with (RUNTIME_DIR / "active_sensor.txt").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(f"Sensor {sensor_id}\n")
    prune_old_backups()

    calibration_dir = (
        PROJECT_ROOT / "shape_reconstruction" / "calibration" / f"sensor_{sensor_id}"
    )
    dataset_dir = PROJECT_ROOT / f"Dataset_sensor_{sensor_id}"
    model_dir = PROJECT_ROOT / f"saved_models_sensor_{sensor_id}"

    print(f"Activated Sensor {sensor_id}")
    print(f"Current Sensor ID: {sensor_id}")
    print(f"Shape configuration source: {shape_source}")
    print(f"Force configuration source: {force_source}")
    print(f"Runtime-state directory: {RUNTIME_DIR}")
    print(f"Calibration directory: {calibration_dir}")
    print(f"Dataset directory: {dataset_dir}")
    print(f"Model directory: {model_dir}")
    print("Suggested next command:")
    print(f"  python tools/check_sensor_setup.py --sensor-id {sensor_id}")
    print(
        "  Then perform calibration or acquisition only under Ubuntu 20.04/ROS Noetic "
        "with the corresponding hardware."
    )


def main() -> None:
    args = parse_args()
    activate(args.sensor_id)


if __name__ == "__main__":
    main()
