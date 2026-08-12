#!/usr/bin/env python3
"""Offline verification for the experimental hybrid calibration layout.

This script performs file, NumPy-array, and SHA-256 checks only.  It does not
import or run the camera, ROS, FT300, or Shape Reconstruction code.
"""

import hashlib
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


EXPECTED_CAMERA_SHAPES = {
    "row_index.npy": (480, 640),
    "col_index.npy": (480, 640),
    "position_scale.npy": (3,),
}


class VerificationError(Exception):
    """Raised when the calibration layout cannot be verified safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(
            project_root.resolve(strict=False)
        ).as_posix()
    except ValueError:
        return str(path.resolve(strict=False))


def strip_yaml_comment(line: str) -> str:
    """Remove a YAML comment while preserving hash characters inside quotes."""
    single_quoted = False
    double_quoted = False
    escaped = False
    output = []

    for character in line:
        if escaped:
            output.append(character)
            escaped = False
            continue
        if character == "\\" and double_quoted:
            output.append(character)
            escaped = True
            continue
        if character == "'" and not double_quoted:
            single_quoted = not single_quoted
        elif character == '"' and not single_quoted:
            double_quoted = not double_quoted
        elif character == "#" and not single_quoted and not double_quoted:
            break
        output.append(character)

    return "".join(output).rstrip()


def yaml_scalar(config_path: Path, key: str) -> str:
    """Read one simple scalar from YAML without adding a PyYAML dependency."""
    pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*:\s*(.*?)\s*$")
    values = []

    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise VerificationError(
            "cannot read {}: {}".format(config_path, exc)
        )

    for raw_line in lines:
        line = strip_yaml_comment(raw_line)
        match = pattern.match(line)
        if match and match.group(1):
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            values.append(value)

    if len(values) != 1:
        raise VerificationError(
            "{} must contain exactly one scalar {!r}; found {}".format(
                config_path, key, len(values)
            )
        )
    return values[0]


def resolve_lut_from_config(config_path: Path) -> Tuple[Path, int]:
    try:
        sensor_id = int(yaml_scalar(config_path, "sensor_id"))
    except ValueError as exc:
        raise VerificationError(
            "{} has a non-integer sensor_id: {}".format(config_path, exc)
        )

    calibration_root = yaml_scalar(config_path, "calibration_root_dir")
    depth_directory = yaml_scalar(config_path, "depth_calibration_dir")
    lut_name = yaml_scalar(config_path, "Pixel_to_Depth_path")

    # The Original runtime opens shape_config.yaml from its containing working
    # directory, then concatenates these values in camera.py and sensor.py.
    calibration_path = (config_path.parent / calibration_root).resolve(strict=False)
    resolved = (
        calibration_path
        / ("sensor_{}".format(sensor_id))
        / depth_directory.lstrip("/\\")
        / lut_name.lstrip("/\\")
    ).resolve(strict=False)
    return resolved, sensor_id


def candidate_details(candidates: List[Path], project_root: Path) -> List[str]:
    details = []
    for candidate in candidates:
        try:
            details.append(
                "  - {} ({} bytes, SHA-256 {})".format(
                    display_path(candidate, project_root),
                    candidate.stat().st_size,
                    sha256_file(candidate),
                )
            )
        except OSError as exc:
            details.append(
                "  - {} (metadata error: {})".format(
                    display_path(candidate, project_root), exc
                )
            )
    return details


def locate_official_lut(original_root: Path, project_root: Path) -> Tuple[Path, str]:
    if not original_root.is_dir():
        raise VerificationError(
            "Original directory not found: {}".format(
                display_path(original_root, project_root)
            )
        )

    candidates = sorted(
        (
            path.resolve(strict=False)
            for path in original_root.rglob("Pixel_to_Depth.npy")
            if path.is_file()
        ),
        key=lambda path: str(path).lower(),
    )
    if not candidates:
        raise VerificationError("no Pixel_to_Depth.npy was found under Original")
    if len(candidates) == 1:
        return candidates[0], "only Pixel_to_Depth.npy found under Original"

    config_paths = sorted(
        original_root.rglob("shape_config.yaml"), key=lambda path: str(path).lower()
    )
    if not config_paths:
        message = [
            "multiple official LUT candidates were found, but no shape_config.yaml exists:"
        ]
        message.extend(candidate_details(candidates, project_root))
        raise VerificationError("\n".join(message))

    candidate_set = set(candidates)
    resolved_matches: Dict[Path, List[str]] = {}
    diagnostics = []
    for config_path in config_paths:
        try:
            resolved_path, sensor_id = resolve_lut_from_config(config_path)
            diagnostics.append(
                "{} (sensor_id={}) -> {}".format(
                    display_path(config_path, project_root),
                    sensor_id,
                    display_path(resolved_path, project_root),
                )
            )
            if resolved_path in candidate_set:
                resolved_matches.setdefault(resolved_path, []).append(
                    display_path(config_path, project_root)
                )
        except VerificationError as exc:
            diagnostics.append(
                "{} -> configuration error: {}".format(
                    display_path(config_path, project_root), exc
                )
            )

    if len(resolved_matches) == 1:
        selected = next(iter(resolved_matches))
        reason = "runtime path resolved by {}".format(
            ", ".join(resolved_matches[selected])
        )
        return selected, reason

    message = [
        "could not uniquely disambiguate multiple official LUT candidates from runtime configuration:",
    ]
    message.extend(candidate_details(candidates, project_root))
    message.append("Configuration resolutions:")
    message.extend("  - {}".format(item) for item in diagnostics)
    raise VerificationError("\n".join(message))


def load_array(path: Path) -> np.ndarray:
    if not path.is_file():
        raise VerificationError("file not found: {}".format(path))
    try:
        return np.load(str(path), allow_pickle=False)
    except Exception as exc:
        raise VerificationError("cannot load {}: {}".format(path, exc))


def validate_shape(path: Path, expected_shape: Tuple[int, ...]) -> None:
    array = load_array(path)
    if array.shape != expected_shape:
        raise VerificationError(
            "{} has shape {}; expected {}".format(path, array.shape, expected_shape)
        )


def validate_lut(path: Path) -> np.ndarray:
    array = load_array(path)
    if array.ndim != 1:
        raise VerificationError("{} is not one-dimensional: {}".format(path, array.shape))
    if array.size <= 2:
        raise VerificationError("{} contains only {} values".format(path, array.size))
    if not np.issubdtype(array.dtype, np.number) or not np.isrealobj(array):
        raise VerificationError("{} is not a real numeric array".format(path))
    if not bool(np.isfinite(array).all()):
        raise VerificationError("{} contains NaN or Inf".format(path))
    if float(np.max(array)) <= 0.0:
        raise VerificationError("{} has no value greater than zero".format(path))
    return array


def verify_sensor(
    sensor_id: int,
    custom_root: Path,
    official_lut: Path,
    official_sha: str,
    project_root: Path,
) -> bool:
    calibration_root = (
        custom_root / "shape_reconstruction" / "calibration" / "sensor_{}".format(sensor_id)
    )
    camera_directory = calibration_root / "camera_calibration"
    depth_lut = calibration_root / "depth_calibration" / "Pixel_to_Depth.npy"
    failures = []
    camera_hashes: Dict[str, str] = {}

    for file_name, expected_shape in EXPECTED_CAMERA_SHAPES.items():
        path = camera_directory / file_name
        try:
            camera_hashes[file_name] = sha256_file(path)
        except OSError as exc:
            camera_hashes[file_name] = "UNAVAILABLE"
            failures.append(str(exc))
        try:
            validate_shape(path, expected_shape)
        except VerificationError as exc:
            failures.append(str(exc))

    depth_sha = "UNAVAILABLE"
    try:
        depth_sha = sha256_file(depth_lut)
    except OSError as exc:
        failures.append(str(exc))
    try:
        validate_lut(depth_lut)
        if depth_sha != official_sha:
            failures.append(
                "{} SHA-256 {} does not match official SHA-256 {}".format(
                    depth_lut, depth_sha, official_sha
                )
            )
    except VerificationError as exc:
        failures.append(str(exc))

    print("\nSensor ID: {}".format(sensor_id))
    print("Camera Calibration path: {}".format(display_path(camera_directory, project_root)))
    for file_name in EXPECTED_CAMERA_SHAPES:
        print("  {} SHA-256: {}".format(file_name, camera_hashes[file_name]))
    print("Depth LUT source: {}".format(display_path(official_lut, project_root)))
    print("Depth LUT source SHA-256: {}".format(official_sha))
    print("Depth LUT target: {}".format(display_path(depth_lut, project_root)))
    print("Depth LUT target SHA-256: {}".format(depth_sha))

    if failures:
        print("Check: FAILED")
        for failure in failures:
            print("  - {}".format(failure))
        return False

    print("Check: PASSED")
    return True


def main() -> int:
    script_path = Path(__file__).resolve()
    custom_root = script_path.parents[1]
    project_root = script_path.parents[2]
    original_root = project_root / "Original"

    try:
        official_lut, selection_reason = locate_official_lut(
            original_root, project_root
        )
        official_array = validate_lut(official_lut)
        official_sha = sha256_file(official_lut)
    except (OSError, VerificationError) as exc:
        print("Official Depth LUT check: FAILED", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print("Hybrid Calibration Verification")
    print("Official Depth LUT: {}".format(display_path(official_lut, project_root)))
    print("Selection reason: {}".format(selection_reason))
    print("Official Depth LUT SHA-256: {}".format(official_sha))
    print("Official Depth LUT shape: {}".format(official_array.shape))
    print(
        "Official Depth LUT range: {} to {}".format(
            float(np.min(official_array)), float(np.max(official_array))
        )
    )

    results = [
        verify_sensor(
            sensor_id, custom_root, official_lut, official_sha, project_root
        )
        for sensor_id in (1, 2)
    ]

    if all(results):
        print("\nOverall result: PASSED")
        return 0

    print("\nOverall result: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
