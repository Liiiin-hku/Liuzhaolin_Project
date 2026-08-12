#!/usr/bin/env python3
"""Perform an offline integrity check of one sensor-specific 9DTact dataset."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.path_utils import resolve_dataset_entry  # noqa: E402


SPLIT_FAMILIES = {
    "standard": "",
    "object": "_object",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--require-normalized", action="store_true")
    parser.add_argument("--check-splits", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args()


def relative_keys(paths: Iterable[Path], base: Path, suffix: str = "") -> Set[str]:
    result = set()
    for path in paths:
        relative = path.relative_to(base)
        stem = relative.stem
        if suffix and stem.endswith(suffix):
            stem = stem[: -len(suffix)]
        result.add((relative.parent / stem).as_posix())
    return result


def object_id_from_entry(value: object) -> Optional[str]:
    normalized = re.sub(r"/+", "/", str(value).replace("\\", "/"))
    match = re.search(r"/(?:image|mixed_image|wrench)/([^/]+)/", "/" + normalized)
    return match.group(1) if match else None


def sample_key_from_entry(value: object, directory: str) -> Optional[str]:
    normalized = re.sub(r"/+", "/", str(value).replace("\\", "/"))
    marker = "/" + directory + "/"
    wrapped = "/" + normalized.lstrip("/")
    if marker not in wrapped:
        return None
    tail = wrapped.split(marker, 1)[1]
    relative = Path(tail)
    stem = relative.stem
    if directory == "wrench" and stem.endswith("_norm"):
        stem = stem[: -len("_norm")]
    return (relative.parent / stem).as_posix()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_six_vector(path: Path) -> np.ndarray:
    values = np.asarray(np.load(str(path), allow_pickle=False), dtype=float).reshape(-1)
    if values.shape != (6,) or not np.all(np.isfinite(values)):
        raise ValueError("expected one finite six-vector")
    return values


def check_split_files(root: Path, errors: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    arrays: Dict[str, np.ndarray] = {}
    all_names = []
    for suffix in SPLIT_FAMILIES.values():
        for split in ("train", "test"):
            all_names.extend(
                [
                    "{}_images{}.npy".format(split, suffix),
                    "{}_mixed_images{}.npy".format(split, suffix),
                    "{}_wrench{}.npy".format(split, suffix),
                ]
            )
    for name in all_names:
        index_path = root / name
        if not index_path.is_file():
            continue
        try:
            values = np.asarray(
                np.load(str(index_path), allow_pickle=False)
            ).reshape(-1)
        except (OSError, ValueError) as exc:
            errors.append("Unreadable split index {}: {}".format(name, exc))
            continue
        arrays[name] = values
        counts[name] = len(values)
        for value in values:
            resolved = resolve_dataset_entry(root, value)
            if not is_within(resolved, root):
                errors.append(
                    "Non-portable split target outside dataset root {} -> {}".format(
                        name, resolved
                    )
                )
            elif not resolved.is_file():
                errors.append("Missing split target {} -> {}".format(name, resolved))

    for family, suffix in SPLIT_FAMILIES.items():
        family_names = [
            "{}_{}{}.npy".format(split, kind, suffix)
            for split in ("train", "test")
            for kind in ("images", "mixed_images", "wrench")
        ]
        family_present = any(name in arrays for name in family_names)
        objects: Dict[str, Set[str]] = {"train": set(), "test": set()}
        for split in ("train", "test"):
            names = {
                "image": "{}_images{}.npy".format(split, suffix),
                "mixed_image": "{}_mixed_images{}.npy".format(split, suffix),
                "wrench": "{}_wrench{}.npy".format(split, suffix),
            }
            present = {kind: name in arrays for kind, name in names.items()}
            if any(present.values()) and not all(present.values()):
                errors.append(
                    "Incomplete {} {} split index family: {}".format(
                        family,
                        split,
                        [name for kind, name in names.items() if not present[kind]],
                    )
                )
                continue
            if family_present and not any(present.values()):
                errors.append(
                    "Incomplete {} split family: all {} indexes are missing".format(
                        family, split
                    )
                )
                continue
            if not all(present.values()):
                continue

            image_values = arrays[names["image"]]
            mixed_values = arrays[names["mixed_image"]]
            wrench_values = arrays[names["wrench"]]
            lengths = (len(image_values), len(mixed_values), len(wrench_values))
            if len(set(lengths)) != 1:
                errors.append(
                    "{} {} image/mixed/wrench lengths differ: {}".format(
                        family, split, lengths
                    )
                )
                continue
            for index, (image, mixed, wrench) in enumerate(
                zip(image_values, mixed_values, wrench_values)
            ):
                keys = (
                    sample_key_from_entry(image, "image"),
                    sample_key_from_entry(mixed, "mixed_image"),
                    sample_key_from_entry(wrench, "wrench"),
                )
                if None in keys or len(set(keys)) != 1:
                    errors.append(
                        "{} {} split triplet key mismatch at index {}: {}".format(
                            family, split, index, keys
                        )
                    )
                object_id = object_id_from_entry(image)
                if object_id is None:
                    errors.append(
                        "Cannot determine object ID in {}: {}".format(
                            names["image"], image
                        )
                    )
                else:
                    objects[split].add(object_id)
        if family_present:
            leakage = objects["train"] & objects["test"]
            if leakage:
                errors.append(
                    "Object leakage across {} train/test indexes: {}".format(
                        family, sorted(leakage)
                    )
                )
    return counts


def check_normalization_parameters(root: Path, errors: List[str]) -> Dict[str, object]:
    path = root / "wrench_normalization_parameters.json"
    if not path.is_file():
        errors.append("Missing wrench_normalization_parameters.json")
        return {}
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append("Unreadable wrench normalization metadata: {}".format(exc))
        return {}
    if not isinstance(metadata, dict):
        errors.append("Wrench normalization metadata must be a JSON object")
        return {}
    try:
        minimum = np.asarray(metadata.get("wrench_min", []), dtype=float).reshape(-1)
        maximum = np.asarray(metadata.get("wrench_max", []), dtype=float).reshape(-1)
        if (
            minimum.shape != (6,)
            or maximum.shape != (6,)
            or not np.all(np.isfinite(minimum))
            or not np.all(np.isfinite(maximum))
            or np.any(maximum <= minimum)
        ):
            raise ValueError("expected six finite values with positive spans")
    except (TypeError, ValueError) as exc:
        errors.append("Invalid wrench normalization ranges: {}".format(exc))
    expected_axes = ["Fx", "Fy", "Fz", "Tx", "Ty", "Tz"]
    if "axis_order" in metadata and metadata["axis_order"] != expected_axes:
        errors.append("Invalid wrench normalization axis_order")
    if "units" in metadata and metadata["units"] != {
        "force": "N",
        "torque": "N*m",
    }:
        errors.append("Invalid wrench normalization units")
    if "dataset_root" in metadata:
        recorded = str(metadata["dataset_root"]).replace("\\", "/").rstrip("/")
        if recorded.rsplit("/", 1)[-1] != root.name:
            errors.append(
                "Normalization metadata dataset does not match {}".format(root.name)
            )
    match = re.fullmatch(r"Dataset_sensor_(\d+)", root.name, flags=re.IGNORECASE)
    if match and "sensor_id" in metadata:
        try:
            recorded_sensor = int(metadata["sensor_id"])
        except (TypeError, ValueError):
            errors.append("Normalization metadata sensor_id is not an integer")
        else:
            if recorded_sensor != int(match.group(1)):
                errors.append(
                    "Normalization metadata sensor_id does not match dataset directory"
                )
    if "img_size" in metadata:
        try:
            image_size = np.asarray(metadata["img_size"], dtype=float).reshape(-1)
            if (
                image_size.shape != (2,)
                or not np.all(np.isfinite(image_size))
                or np.any(image_size <= 0)
                or not np.all(image_size == np.floor(image_size))
            ):
                raise ValueError("expected two positive integers")
        except (TypeError, ValueError) as exc:
            errors.append("Invalid normalization img_size: {}".format(exc))
    return metadata


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args() if argv is None else parse_args_from(argv)
    root = args.dataset_root.expanduser().resolve()
    errors: List[str] = []
    if not root.is_dir():
        print("[FAILED] Dataset directory does not exist: {}".format(root))
        return 1

    image_root = root / "image"
    mixed_root = root / "mixed_image"
    wrench_root = root / "wrench"
    images = sorted(image_root.rglob("*.png")) if image_root.is_dir() else []
    mixed = sorted(mixed_root.rglob("*.png")) if mixed_root.is_dir() else []
    all_wrenches = sorted(wrench_root.rglob("*.npy")) if wrench_root.is_dir() else []
    normalized = [path for path in all_wrenches if path.stem.endswith("_norm")]
    raw = [path for path in all_wrenches if not path.stem.endswith("_norm")]

    image_keys = relative_keys(images, image_root)
    mixed_keys = relative_keys(mixed, mixed_root)
    raw_keys = relative_keys(raw, wrench_root)
    normalized_keys = relative_keys(normalized, wrench_root, suffix="_norm")
    complete = image_keys & mixed_keys & raw_keys
    incomplete = (image_keys | mixed_keys | raw_keys) - complete
    if incomplete:
        errors.append("Incomplete image/mixed-image/raw-wrench keys: {}".format(len(incomplete)))
    normalization_metadata: Dict[str, object] = {}
    if args.require_normalized:
        missing_norm = complete - normalized_keys
        if missing_norm:
            errors.append("Complete samples missing normalized labels: {}".format(len(missing_norm)))
        normalization_metadata = check_normalization_parameters(root, errors)

    for path in raw:
        try:
            load_six_vector(path)
        except (OSError, ValueError) as exc:
            errors.append("Invalid physical wrench {}: {}".format(path, exc))
    for path in normalized:
        try:
            values = load_six_vector(path)
            if np.any(values < -1e-9) or np.any(values > 1.0 + 1e-9):
                raise ValueError("normalized components are outside [0,1]")
        except (OSError, ValueError) as exc:
            errors.append("Invalid normalized wrench {}: {}".format(path, exc))

    split_counts = check_split_files(root, errors) if args.check_splits else {}
    report = {
        "dataset_root": str(root),
        "image_files": len(images),
        "mixed_image_files": len(mixed),
        "raw_wrench_files": len(raw),
        "normalized_wrench_files": len(normalized),
        "complete_triplets": len(complete),
        "incomplete_keys": len(incomplete),
        "split_counts": split_counts,
        "normalization_metadata_present": bool(normalization_metadata),
        "errors": errors,
        "hardware_validation_claimed": False,
    }
    if args.json_report:
        destination = args.json_report.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print("Dataset: {}".format(root))
    print("Complete triplets: {}".format(len(complete)))
    print("Raw wrench labels: {}".format(len(raw)))
    print("Normalized wrench labels: {}".format(len(normalized)))
    if errors:
        for error in errors:
            print("[FAILED] {}".format(error))
        print("Dataset integrity: FAILED")
        return 1
    print("Dataset integrity: PASSED")
    return 0


def parse_args_from(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--require-normalized", action="store_true")
    parser.add_argument("--check-splits", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run())
