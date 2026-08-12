#!/usr/bin/env python3
"""Offline integrity gate for the teacher-submission repository or ZIP extract."""

import argparse
import ast
import csv
import hashlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_ROOT = PROJECT_ROOT / "custom_9dtact"
ORIGINAL_ROOT = PROJECT_ROOT / "Original"

EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".runtime",
    "tmp",
    "output",
    "wandb",
    "runs",
    "Dataset_sensor_1",
    "Dataset_sensor_2",
    "saved_models_sensor_1",
    "saved_models_sensor_2",
}
ACTIVE_BOTA_TERMS = (
    "rokubimini",
    "bota",
    "/bus0/ft_sensor0",
    "ft_sensor0",
    "minione",
)
LOCAL_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"/home/[A-Za-z0-9._-]+"),
)
TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".launch",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run static checks only; no camera, ROS master, FT300, CUDA, or model"
    )
    parser.add_argument(
        "--original-baseline",
        type=Path,
        help="CSV containing relative_path,size,sha256 for the protected Original snapshot",
    )
    parser.add_argument(
        "--strict-package",
        action="store_true",
        help="reject caches, datasets, models, logs, and other excluded delivery artifacts",
    )
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = (
                path.stat().st_size,
                sha256_file(path),
            )
    return result


def read_manifest(path):
    rows = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        expected = {"relative_path", "size", "sha256"}
        if not reader.fieldnames or not expected.issubset(set(reader.fieldnames)):
            raise ValueError("manifest header is incomplete")
        for row in reader:
            rows[row["relative_path"].replace("\\", "/")] = (
                int(row["size"]),
                row["sha256"].lower(),
            )
    return rows


def check_original(baseline, failures):
    if not baseline:
        return
    try:
        expected = read_manifest(baseline.resolve())
    except Exception as exc:
        failures.append("Original baseline manifest is unreadable: {}".format(exc))
        return
    actual = inventory(ORIGINAL_ROOT)
    if expected != actual:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(
            key for key in set(expected) & set(actual) if expected[key] != actual[key]
        )
        failures.append(
            "Original mismatch: missing={}, extra={}, changed={}".format(
                missing[:10], extra[:10], changed[:10]
            )
        )
    else:
        print("[PASS] Original manifest: {} files unchanged".format(len(actual)))


def parse_python_38(path):
    text = path.read_text(encoding="utf-8-sig")
    if sys.version_info >= (3, 9):
        ast.parse(text, filename=str(path), feature_version=(3, 8))
    else:
        ast.parse(text, filename=str(path), feature_version=8)


def check_required_files(failures):
    required = (
        "README.md",
        "README_CN.md",
        "VERSION_INFO.md",
        "LICENSE",
        "NOTICE.md",
        "custom_9dtact/pyproject.toml",
        "custom_9dtact/requirements-core.txt",
        "custom_9dtact/requirements-pytorch.txt",
        "custom_9dtact/environment.yml",
        "custom_9dtact/shape_reconstruction/manual_camera_calibration_v2.py",
        "custom_9dtact/data_collection/collect_data_ft300.py",
        "custom_9dtact/tools/check_ft300_topic.py",
        "custom_9dtact/tools/check_dataset_integrity.py",
        "custom_9dtact/tools/verify_hybrid_calibration.py",
        "custom_9dtact/ros_ws/src/9dtact_ft300_ros/package.xml",
        "custom_9dtact/ros_ws/src/9dtact_ft300_ros/CMakeLists.txt",
        "scripts/install_core_ubuntu20.sh",
        "scripts/verify_installation.py",
        "scripts/verify_submission.py",
        "scripts/create_training_bundle.py",
    )
    required += tuple("docs/{:02d}_{}.md".format(index, name) for index, name in (
        (0, "PROJECT_OVERVIEW"),
        (1, "INSTALLATION_UBUNTU20"),
        (2, "SENSOR_CONFIGURATION"),
        (3, "CAMERA_CALIBRATION"),
        (4, "SENSOR_CALIBRATION"),
        (5, "SHAPE_RECONSTRUCTION"),
        (6, "FT300_SETUP"),
        (7, "DATA_COLLECTION"),
        (8, "DATA_PROCESSING"),
        (9, "MODEL_TRAINING"),
        (10, "FORCE_ESTIMATION"),
        (11, "ROS_WORKFLOW"),
        (12, "TROUBLESHOOTING"),
        (13, "PROJECT_TREE"),
    ))
    launch_root = Path("custom_9dtact/ros_ws/src/9dtact_ft300_ros/launch")
    required += tuple((launch_root / name).as_posix() for name in (
        "sensor1_shape.launch",
        "sensor2_shape.launch",
        "ft300_collection.launch",
        "force_estimation.launch",
        "shape_force_demo.launch",
        "compare_prediction_with_ft300.launch",
    ))
    for relative in required:
        if not (PROJECT_ROOT / relative).is_file():
            failures.append("Required file is missing: {}".format(relative))


def check_source_files(failures):
    python_count = 0
    for path in sorted(PROJECT_ROOT.rglob("*.py")):
        if ".git" in path.parts:
            continue
        python_count += 1
        try:
            parse_python_38(path)
        except Exception as exc:
            failures.append("Python 3.8 syntax: {}: {}".format(path, exc))
    print("[INFO] Python files checked: {}".format(python_count))

    try:
        import yaml
    except Exception as exc:
        failures.append("PyYAML is required for static YAML checks: {}".format(exc))
    else:
        yaml_count = 0
        for suffix in ("*.yaml", "*.yml"):
            for path in sorted(PROJECT_ROOT.rglob(suffix)):
                if ".git" in path.parts:
                    continue
                yaml_count += 1
                try:
                    yaml.safe_load(path.read_text(encoding="utf-8-sig"))
                except Exception as exc:
                    failures.append("YAML parse: {}: {}".format(path, exc))
        print("[INFO] YAML files checked: {}".format(yaml_count))

    xml_paths = list(PROJECT_ROOT.rglob("package.xml")) + list(PROJECT_ROOT.rglob("*.launch"))
    for path in sorted(set(xml_paths)):
        try:
            ET.parse(str(path))
        except Exception as exc:
            failures.append("XML parse: {}: {}".format(path, exc))
    print("[INFO] ROS XML files checked: {}".format(len(set(xml_paths))))


def check_calibration_and_configs(failures):
    try:
        import numpy as np
        import yaml
    except Exception as exc:
        failures.append("NumPy and PyYAML are required for calibration checks: {}".format(exc))
        return

    for sensor_id in (1, 2):
        base = CUSTOM_ROOT / "shape_reconstruction" / "calibration" / "sensor_{}".format(sensor_id)
        expected = {
            "row_index.npy": (480, 640),
            "col_index.npy": (480, 640),
            "position_scale.npy": (3,),
        }
        for name, shape in expected.items():
            path = base / "camera_calibration" / name
            try:
                array = np.load(str(path), allow_pickle=False)
            except Exception as exc:
                failures.append("Sensor {} {} load failed: {}".format(sensor_id, name, exc))
                continue
            if array.shape != shape:
                failures.append(
                    "Sensor {} {} shape {} != {}".format(sensor_id, name, array.shape, shape)
                )
            if not bool(np.isfinite(array).all()):
                failures.append("Sensor {} {} contains non-finite values".format(sensor_id, name))
        position_path = base / "camera_calibration" / "position_scale.npy"
        if position_path.is_file():
            position = np.load(str(position_path), allow_pickle=False)
            if position.shape == (3,) and float(position[2]) <= 0:
                failures.append("Sensor {} position scale must be positive".format(sensor_id))

        shape_path = CUSTOM_ROOT / "configs" / "shape_sensor_{}.yaml".format(sensor_id)
        force_path = CUSTOM_ROOT / "configs" / "force_sensor_{}.yaml".format(sensor_id)
        shape_cfg = yaml.safe_load(shape_path.read_text(encoding="utf-8-sig"))
        force_cfg = yaml.safe_load(force_path.read_text(encoding="utf-8-sig"))
        if shape_cfg.get("sensor_id") != sensor_id or force_cfg.get("sensor_id") != sensor_id:
            failures.append("Sensor {} configuration ID isolation failed".format(sensor_id))
        crop = shape_cfg.get("camera_calibration", {}).get("crop_size")
        image_size = force_cfg.get("img_size")
        if crop != image_size:
            failures.append(
                "Sensor {} crop_size {} != img_size {}".format(sensor_id, crop, image_size)
            )
        if "Dataset_sensor_{}".format(sensor_id) not in str(force_cfg.get("data_dir")):
            failures.append("Sensor {} dataset path is not isolated".format(sensor_id))
        if "saved_models_sensor_{}".format(sensor_id) not in str(force_cfg.get("save_dir")):
            failures.append("Sensor {} model path is not isolated".format(sensor_id))


def iter_text_files(root):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and ".git" not in path.parts:
            yield path


def check_active_bota_and_local_paths(failures):
    active_roots = (
        CUSTOM_ROOT / "configs",
        CUSTOM_ROOT / "data",
        CUSTOM_ROOT / "data_collection",
        CUSTOM_ROOT / "force_estimation",
        CUSTOM_ROOT / "model",
        CUSTOM_ROOT / "shape-force_ros",
        CUSTOM_ROOT / "shape_reconstruction",
        CUSTOM_ROOT / "tools",
        CUSTOM_ROOT / "ros_ws",
    )
    for root in active_roots:
        if not root.exists():
            continue
        for path in iter_text_files(root):
            text = path.read_text(encoding="utf-8-sig", errors="replace").lower()
            for term in ACTIVE_BOTA_TERMS:
                if term in text:
                    failures.append("Active BOTA reference {} in {}".format(term, path))

    for path in iter_text_files(PROJECT_ROOT):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for pattern in LOCAL_PATH_PATTERNS:
            if pattern.search(text):
                failures.append("Local absolute path found in {}".format(path))
                break


def check_strict_package(failures):
    for path in PROJECT_ROOT.rglob("*"):
        if path.is_dir() and path.name in EXCLUDED_DIRECTORY_NAMES:
            failures.append("Excluded directory is present: {}".format(path))
        elif path.is_file() and path.suffix.lower() in {".pyc", ".log", ".tmp"}:
            failures.append("Excluded file is present: {}".format(path))
        elif path.is_dir() and path.name.startswith("training_bundle_sensor_"):
            failures.append("Generated training bundle is present: {}".format(path))


def check_hybrid_script(failures):
    script = CUSTOM_ROOT / "tools" / "verify_hybrid_calibration.py"
    if not script.is_file():
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    print(result.stdout.rstrip())
    if result.returncode != 0:
        failures.append("verify_hybrid_calibration.py returned {}".format(result.returncode))


def main():
    args = parse_args()
    failures = []
    print("Repository: {}".format(PROJECT_ROOT))
    print("Static submission verification only")

    check_required_files(failures)
    check_source_files(failures)
    check_calibration_and_configs(failures)
    check_active_bota_and_local_paths(failures)
    check_original(args.original_baseline, failures)
    check_hybrid_script(failures)
    if args.strict_package:
        check_strict_package(failures)

    if failures:
        for failure in failures:
            print("[FAIL] {}".format(failure))
        print("Submission verification: FAILED ({})".format(len(failures)))
        return 1

    print("Submission verification: PASSED")
    print(
        "No camera, ROS master, FT300 hardware, CUDA workload, Shape Reconstruction, "
        "or neural-network training was executed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
