#!/usr/bin/env python3
"""Check static sensor state without loading ROS, OpenCV, or PyTorch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Set, Tuple

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / ".runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check configuration and data status for a specified 9DTact sensor"
    )
    parser.add_argument("--sensor-id", type=int, choices=(1, 2), required=True)
    parser.add_argument(
        "--require-data",
        action="store_true",
        help="fail when no complete image/mixed-image/raw-wrench sample exists",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"  [ERROR] Failed to read {path.name}: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def relative_keys(paths: Iterable[Path], base: Path, suffix: str = "") -> Set[Tuple[str, str]]:
    keys: Set[Tuple[str, str]] = set()
    for path in paths:
        relative = path.relative_to(base)
        stem = path.stem
        if suffix and stem.endswith(suffix):
            stem = stem[: -len(suffix)]
        keys.add((relative.parent.as_posix(), stem))
    return keys


def normalized_path_text(value: Any) -> str:
    return str(value or "").replace("\\", "/").rstrip("/")


def mark(ok: bool) -> str:
    return "OK" if ok else "ERROR"


def main() -> int:
    args = parse_args()
    failures = []
    sensor_id = args.sensor_id
    expected_dataset = f"Dataset_sensor_{sensor_id}"
    expected_models = f"saved_models_sensor_{sensor_id}"

    shape_template_path = PROJECT_ROOT / "configs" / f"shape_sensor_{sensor_id}.yaml"
    force_template_path = PROJECT_ROOT / "configs" / f"force_sensor_{sensor_id}.yaml"
    active_shape_path = PROJECT_ROOT / "shape_reconstruction" / "shape_config.yaml"
    active_force_path = PROJECT_ROOT / "force_estimation" / "force_config.yaml"
    active_marker = RUNTIME_DIR / "active_sensor.txt"

    shape_template = load_yaml(shape_template_path)
    force_template = load_yaml(force_template_path)

    print(f"=== Sensor {sensor_id} Static Status Check ===")
    print(f"Shape template: {mark(shape_template_path.is_file())} - {shape_template_path}")
    print(f"Force template: {mark(force_template_path.is_file())} - {force_template_path}")
    print(f"Shape sensor_id: {mark(shape_template.get('sensor_id') == sensor_id)}")
    print(f"Force sensor_id: {mark(force_template.get('sensor_id') == sensor_id)}")
    if not shape_template_path.is_file() or shape_template.get("sensor_id") != sensor_id:
        failures.append("invalid shape configuration template")
    if not force_template_path.is_file() or force_template.get("sensor_id") != sensor_id:
        failures.append("invalid force configuration template")

    data_text = normalized_path_text(force_template.get("data_dir"))
    save_text = normalized_path_text(force_template.get("save_dir"))
    data_ok = data_text.endswith("/" + expected_dataset) or data_text == expected_dataset
    save_ok = save_text.endswith("/" + expected_models) or save_text == expected_models
    other_id = 2 if sensor_id == 1 else 1
    wrong_reference = (
        f"Dataset_sensor_{other_id}" in data_text
        or f"saved_models_sensor_{other_id}" in save_text
    )
    print(f"Dataset directory: {mark(data_ok)} - {data_text or 'Not configured'}")
    print(f"Model directory: {mark(save_ok)} - {save_text or 'Not configured'}")
    print(f"References the other sensor: {'Yes (error)' if wrong_reference else 'No'}")
    if not data_ok or not save_ok or wrong_reference:
        failures.append("force template contains an invalid sensor-specific path")

    if not (
        active_shape_path.is_file()
        and active_force_path.is_file()
        and active_marker.is_file()
    ):
        print("No sensor is active. Run:")
        print(f"python tools/activate_sensor.py --sensor-id {sensor_id}")
        return 1

    active_shape = load_yaml(active_shape_path)
    active_force = load_yaml(active_force_path)

    calibration_dir = (
        PROJECT_ROOT / "shape_reconstruction" / "calibration" / f"sensor_{sensor_id}"
    )
    camera_dir = calibration_dir / "camera_calibration"
    depth_dir = calibration_dir / "depth_calibration"
    camera_names = ("row_index.npy", "col_index.npy", "position_scale.npy")
    missing_camera = [name for name in camera_names if not (camera_dir / name).is_file()]
    missing_depth = [] if (depth_dir / "Pixel_to_Depth.npy").is_file() else ["Pixel_to_Depth.npy"]
    if missing_camera:
        print("Calibration status: Camera Calibration incomplete")
        print("  Missing: " + ", ".join(missing_camera))
        failures.append("camera calibration files are missing")
    else:
        print("Calibration status: Camera Calibration files complete")
    if missing_depth:
        print("Calibration status: Sensor Calibration incomplete")
        print("  Missing: Pixel_to_Depth.npy")
        failures.append("depth calibration file is missing")
    else:
        print("Calibration status: Sensor Calibration files complete")

    dataset_dir = PROJECT_ROOT / expected_dataset
    image_dir = dataset_dir / "image"
    mixed_dir = dataset_dir / "mixed_image"
    wrench_dir = dataset_dir / "wrench"
    images = sorted(image_dir.rglob("*.png")) if image_dir.is_dir() else []
    mixed_images = sorted(mixed_dir.rglob("*.png")) if mixed_dir.is_dir() else []
    wrench_files = sorted(wrench_dir.rglob("*.npy")) if wrench_dir.is_dir() else []
    norm_wrenches = [path for path in wrench_files if path.name.endswith("_norm.npy")]
    raw_wrenches = [path for path in wrench_files if not path.name.endswith("_norm.npy")]

    print("Data file counts:")
    print(f"  image: {len(images)}")
    print(f"  mixed_image: {len(mixed_images)}")
    print(f"  Raw wrench files: {len(raw_wrenches)}")
    print(f"  wrench _norm.npy: {len(norm_wrenches)}")

    image_keys = relative_keys(images, image_dir)
    mixed_keys = relative_keys(mixed_images, mixed_dir)
    raw_keys = relative_keys(raw_wrenches, wrench_dir)
    norm_keys = relative_keys(norm_wrenches, wrench_dir, suffix="_norm")
    complete_keys = image_keys & mixed_keys & raw_keys
    incomplete = (image_keys | mixed_keys | raw_keys) - complete_keys
    print(f"Complete image/mixed-image/raw-wrench samples: {len(complete_keys)}")
    print(f"Image and wrench-label counts differ: {'Yes' if incomplete else 'No'}")
    if incomplete:
        print(f"  Incomplete samples: {len(incomplete)}")
    print(f"Complete samples missing _norm.npy: {len(complete_keys - norm_keys)}")
    if args.require_data and not complete_keys:
        failures.append("no complete acquisition sample was found")

    marker_ok = active_marker.read_text(encoding="utf-8").strip() == f"Sensor {sensor_id}"
    active_ok = (
        active_shape.get("sensor_id") == sensor_id
        and active_force.get("sensor_id") == sensor_id
        and normalized_path_text(active_force.get("data_dir")).endswith("/" + expected_dataset)
        and normalized_path_text(active_force.get("save_dir")).endswith("/" + expected_models)
        and marker_ok
    )
    print(f"Active configuration matches Sensor {sensor_id}: {'Yes' if active_ok else 'No'}")
    if not active_ok:
        print(f"  To switch, run: python tools/activate_sensor.py --sensor-id {sensor_id}")
        failures.append("active configuration does not match the requested sensor")

    if failures:
        print("Static result: FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("Static result: PASSED")
    print(
        "This tool inspected only files and configuration; it did not access a camera, "
        "ROS, FT300 hardware, or a model."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
