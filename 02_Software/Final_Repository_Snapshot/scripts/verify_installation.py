#!/usr/bin/env python3
"""Verify software dependencies without opening a camera or ROS hardware."""

import argparse
import importlib
import platform
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_ROOT = PROJECT_ROOT / "custom_9dtact"

PROFILES = {
    "core": (
        ("numpy", "NumPy"),
        ("cv2", "OpenCV"),
        ("scipy", "SciPy"),
        ("yaml", "PyYAML"),
        ("open3d", "Open3D"),
        ("ml_collections", "ml-collections"),
    ),
    "training": (
        ("torch", "PyTorch"),
        ("torchvision", "torchvision"),
        ("tensorboard", "TensorBoard"),
    ),
    "ros": (
        ("rospy", "rospy"),
        ("sensor_msgs.msg", "sensor_msgs"),
        ("geometry_msgs.msg", "geometry_msgs"),
        ("cv_bridge", "cv_bridge"),
        ("message_filters", "message_filters"),
        ("ros_numpy", "ros_numpy"),
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Check the Python and ROS environment only; no camera, FT300, CUDA "
            "kernel, model, or Shape Reconstruction is executed"
        )
    )
    parser.add_argument(
        "--profile",
        choices=("core", "training", "ros", "all"),
        default="core",
        help="dependency group to import",
    )
    parser.add_argument(
        "--allow-python-version-mismatch",
        action="store_true",
        help="report but do not fail when the interpreter is not Python 3.8",
    )
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="check repository files and Python version without importing dependencies",
    )
    return parser.parse_args()


def module_version(module):
    return str(getattr(module, "__version__", "version not exposed"))


def main():
    args = parse_args()
    failures = []
    warnings = []

    print("9DTact + FT300 installation verification")
    print("Platform: {}".format(platform.platform()))
    print("Python: {}".format(sys.version.replace("\n", " ")))

    if sys.version_info[:2] != (3, 8):
        message = "Expected Python 3.8; found {}.{}.".format(
            sys.version_info[0], sys.version_info[1]
        )
        if args.allow_python_version_mismatch:
            warnings.append(message)
        else:
            failures.append(message)

    required_files = (
        CUSTOM_ROOT / "requirements-core.txt",
        CUSTOM_ROOT / "requirements-pytorch.txt",
        CUSTOM_ROOT / "environment.yml",
        CUSTOM_ROOT / "configs" / "shape_sensor_1.yaml",
        CUSTOM_ROOT / "configs" / "shape_sensor_2.yaml",
        CUSTOM_ROOT / "ros_ws" / "src" / "9dtact_ft300_ros" / "package.xml",
    )
    for path in required_files:
        if path.is_file():
            print("[PASS] file: {}".format(path.relative_to(PROJECT_ROOT).as_posix()))
        else:
            failures.append("Missing file: {}".format(path))

    if not args.static_only:
        selected = tuple(PROFILES) if args.profile == "all" else (args.profile,)
        for profile in selected:
            print("Dependency profile: {}".format(profile))
            for import_name, label in PROFILES[profile]:
                try:
                    module = importlib.import_module(import_name)
                except Exception as exc:
                    failures.append("{} import failed: {}".format(label, exc))
                else:
                    print("[PASS] {}: {}".format(label, module_version(module)))

    for warning in warnings:
        print("[WARN] {}".format(warning))
    for failure in failures:
        print("[FAIL] {}".format(failure))

    print(
        "No camera, ROS master, FT300 device, CUDA kernel, model inference, or "
        "Shape Reconstruction was started."
    )
    if failures:
        print("Installation verification: FAILED")
        return 1
    print("Installation verification: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
