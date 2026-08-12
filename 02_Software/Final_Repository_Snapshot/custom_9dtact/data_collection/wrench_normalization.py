#!/usr/bin/env python3
"""Validate, clean, and normalize physical wrench labels; dry-run by default."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from force_estimation.wrench import (  # noqa: E402
    normalize_wrench,
    vector6,
    wrench_limits,
)


@dataclass(frozen=True)
class Sample:
    object_id: int
    stem: str
    image: Path
    mixed_image: Path
    wrench: Path

    def companions(self) -> Tuple[Path, Path, Path]:
        return self.image, self.mixed_image, self.wrench


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate, clean, and normalize physical 9DTact wrench labels"
    )
    parser.add_argument("--dataset-root", type=Path, default=Path("../Dataset"))
    parser.add_argument("--object-num", type=int, default=175)
    parser.add_argument(
        "--force-config",
        type=Path,
        help="YAML containing top-level wrench_min and wrench_max",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; make no changes (default)"
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Delete invalid triplets, renumber valid samples, and write normalized labels",
    )
    args = parser.parse_args()
    if args.object_num < 1:
        parser.error("--object-num must be greater than 0")
    return args


def load_force_config(path: Optional[Path]) -> Tuple[Optional[Path], Mapping[str, Any]]:
    selected = path
    if selected is None:
        active = PROJECT_ROOT / "force_estimation" / "force_config.yaml"
        if active.is_file():
            selected = active
    if selected is None:
        return None, {}
    selected = selected.expanduser().resolve()
    if not selected.is_file():
        raise FileNotFoundError("Force configuration does not exist: {}".format(selected))
    try:
        config = yaml.safe_load(selected.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError("Invalid force configuration {}: {}".format(selected, exc))
    if not isinstance(config, dict):
        raise ValueError("Force configuration must be a YAML mapping: {}".format(selected))
    return selected, config


def stems_in(directory: Path, pattern: str, normalized: bool = False) -> Iterable[str]:
    if not directory.is_dir():
        return []
    paths = directory.glob(pattern)
    if normalized:
        return (
            path.stem[: -len("_norm")]
            for path in paths
            if path.stem.endswith("_norm")
        )
    return (path.stem for path in paths if not path.stem.endswith("_norm"))


def collect_samples(root: Path, object_num: int) -> Tuple[List[Sample], List[Path]]:
    samples: List[Sample] = []
    normalized_paths: List[Path] = []
    for object_id in range(1, object_num + 1):
        image_dir = root / "image" / str(object_id)
        mixed_dir = root / "mixed_image" / str(object_id)
        wrench_dir = root / "wrench" / str(object_id)
        stems = set(stems_in(image_dir, "*.png"))
        stems.update(stems_in(mixed_dir, "*.png"))
        stems.update(stems_in(wrench_dir, "*.npy"))
        for stem in sorted(stems):
            samples.append(
                Sample(
                    object_id=object_id,
                    stem=stem,
                    image=image_dir / (stem + ".png"),
                    mixed_image=mixed_dir / (stem + ".png"),
                    wrench=wrench_dir / (stem + ".npy"),
                )
            )
        if wrench_dir.is_dir():
            normalized_paths.extend(sorted(wrench_dir.glob("*_norm.npy")))
    return samples, normalized_paths


def classify(
    samples: Iterable[Sample], minimum: np.ndarray, maximum: np.ndarray
) -> Tuple[List[Sample], List[Sample], List[Sample], List[str]]:
    valid: List[Sample] = []
    out_of_range: List[Sample] = []
    incomplete: List[Sample] = []
    unreadable: List[str] = []
    for sample in samples:
        if not all(path.is_file() for path in sample.companions()):
            incomplete.append(sample)
            continue
        try:
            wrench = vector6(
                np.load(str(sample.wrench), allow_pickle=False), str(sample.wrench)
            )
        except (OSError, ValueError) as exc:
            unreadable.append("{}: {}".format(sample.wrench, exc))
            incomplete.append(sample)
            continue
        if np.any(wrench < minimum) or np.any(wrench > maximum):
            out_of_range.append(sample)
        else:
            valid.append(sample)
    return valid, out_of_range, incomplete, unreadable


def report_dict(
    root: Path,
    config_path: Optional[Path],
    config: Mapping[str, Any],
    minimum: np.ndarray,
    maximum: np.ndarray,
    samples: List[Sample],
    normalized_paths: List[Path],
    valid: List[Sample],
    out_of_range: List[Sample],
    incomplete: List[Sample],
    unreadable: List[str],
) -> Dict[str, Any]:
    invalid = out_of_range + incomplete
    existing_invalid_files = sum(
        1 for sample in invalid for path in sample.companions() if path.exists()
    )
    report = {
        "schema_version": 2,
        "created_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "dataset_root": str(root),
        "force_config": str(config_path) if config_path is not None else None,
        "axis_order": ["Fx", "Fy", "Fz", "Tx", "Ty", "Tz"],
        "units": {"force": "N", "torque": "N*m"},
        "wrench_min": minimum.tolist(),
        "wrench_max": maximum.tolist(),
        "normalization": "(physical - wrench_min) / (wrench_max - wrench_min)",
        "raw_sample_keys": len(samples),
        "existing_norm_files": len(normalized_paths),
        "valid_samples": len(valid),
        "out_of_range_samples": len(out_of_range),
        "incomplete_or_unreadable_samples": len(incomplete),
        "files_to_delete": len(normalized_paths) + existing_invalid_files,
        "norm_files_to_generate": len(valid),
        "unreadable_details": unreadable,
        "hardware_validation_claimed": False,
    }
    if "sensor_id" in config:
        report["sensor_id"] = int(config["sensor_id"])
    if "img_size" in config:
        report["img_size"] = [int(value) for value in config["img_size"]]
    return report


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(str(temporary), str(path))


def write_preflight_report(root: Path, report: Mapping[str, Any]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = root / ("wrench_processing_report_" + timestamp + ".json")
    atomic_json(report_path, report)
    return report_path


def delete_paths(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.is_file():
            path.unlink()


def renumber_samples(valid: List[Sample]) -> List[Sample]:
    result: List[Sample] = []
    by_object: Dict[int, List[Sample]] = {}
    for sample in valid:
        by_object.setdefault(sample.object_id, []).append(sample)

    for object_id, object_samples in sorted(by_object.items()):
        ordered = sorted(
            object_samples,
            key=lambda sample: (sample.image.stat().st_mtime, sample.stem),
        )
        staged: List[Tuple[Path, Path, Path]] = []
        for sample in ordered:
            token = uuid.uuid4().hex
            temporary_paths = (
                sample.image.with_name(".__9dtact_{}.png".format(token)),
                sample.mixed_image.with_name(".__9dtact_{}.png".format(token)),
                sample.wrench.with_name(".__9dtact_{}.npy".format(token)),
            )
            for source, temporary in zip(sample.companions(), temporary_paths):
                source.replace(temporary)
            staged.append(temporary_paths)

        for index, temporary_paths in enumerate(staged, start=1):
            stem = str(index)
            final = Sample(
                object_id=object_id,
                stem=stem,
                image=temporary_paths[0].with_name(stem + ".png"),
                mixed_image=temporary_paths[1].with_name(stem + ".png"),
                wrench=temporary_paths[2].with_name(stem + ".npy"),
            )
            for temporary, destination in zip(temporary_paths, final.companions()):
                temporary.replace(destination)
            result.append(final)
    return result


def main() -> None:
    args = parse_args()
    root = args.dataset_root.expanduser().resolve()
    print(
        "Warning: --apply may delete out-of-range or incomplete sample triplets. "
        "Back up the selected Dataset_sensor_X directory first."
    )
    if not root.is_dir():
        raise SystemExit("Dataset directory does not exist: {}".format(root))

    config_path, config = load_force_config(args.force_config)
    minimum, maximum = wrench_limits(config)
    samples, normalized_paths = collect_samples(root, args.object_num)
    valid, out_of_range, incomplete, unreadable = classify(
        samples, minimum, maximum
    )
    report = report_dict(
        root,
        config_path,
        config,
        minimum,
        maximum,
        samples,
        normalized_paths,
        valid,
        out_of_range,
        incomplete,
        unreadable,
    )
    print("Raw wrench/sample keys found: {}".format(report["raw_sample_keys"]))
    print("Out-of-range samples: {}".format(report["out_of_range_samples"]))
    print(
        "Incomplete or unreadable samples: {}".format(
            report["incomplete_or_unreadable_samples"]
        )
    )
    print("Files to delete: {}".format(report["files_to_delete"]))
    print("_norm.npy files to generate: {}".format(report["norm_files_to_generate"]))
    for detail in unreadable:
        print("  Skipping invalid sample: {}".format(detail))

    if not args.apply:
        print("Dry run: no data was deleted, renamed, or generated.")
        return

    report_path = write_preflight_report(root, report)
    print("Pre-execution report written to: {}".format(report_path))
    delete_paths(normalized_paths)
    invalid_samples = out_of_range + incomplete
    delete_paths(path for sample in invalid_samples for path in sample.companions())
    remaining = [
        sample for sample in valid if all(path.is_file() for path in sample.companions())
    ]
    renumbered = renumber_samples(remaining)
    for sample in renumbered:
        physical = vector6(
            np.load(str(sample.wrench), allow_pickle=False), str(sample.wrench)
        )
        normalized = normalize_wrench(physical, minimum, maximum)
        np.save(
            str(sample.wrench.with_name(sample.wrench.stem + "_norm.npy")),
            normalized,
            allow_pickle=False,
        )
    completion = dict(report)
    completion["completed_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    completion["generated_norm_files"] = len(renumbered)
    atomic_json(root / "wrench_normalization_parameters.json", completion)
    print("Processing complete: generated {} _norm.npy files.".format(len(renumbered)))


if __name__ == "__main__":
    main()
