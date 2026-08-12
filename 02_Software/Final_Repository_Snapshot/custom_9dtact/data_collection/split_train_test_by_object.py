#!/usr/bin/env python3
"""Split a 9DTact dataset without leaking an object across train and test."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np


@dataclass(frozen=True)
class Sample:
    object_id: int
    image: Path
    mixed_image: Path
    wrench: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a 9DTact dataset into disjoint training and test objects"
    )
    parser.add_argument("--dataset-root", type=Path, default=Path("../Dataset"))
    parser.add_argument("--object-number", type=int, default=175)
    parser.add_argument("--test-object-number", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.object_number < 1 or args.test_object_number < 1:
        parser.error("Object-count parameters must be greater than 0")
    return args


def collect(root: Path, object_number: int) -> Dict[int, List[Sample]]:
    image_root = root / "image"
    mixed_root = root / "mixed_image"
    wrench_root = root / "wrench"
    by_object: Dict[int, List[Sample]] = {}
    skipped: List[str] = []
    for object_id in range(1, object_number + 1):
        object_dir = image_root / str(object_id)
        for image in sorted(object_dir.glob("*.png")) if object_dir.is_dir() else []:
            relative = image.relative_to(image_root)
            mixed_image = mixed_root / relative
            wrench = wrench_root / str(object_id) / f"{image.stem}_norm.npy"
            if mixed_image.is_file() and wrench.is_file():
                by_object.setdefault(object_id, []).append(
                    Sample(object_id, image, mixed_image, wrench)
                )
            else:
                missing = []
                if not mixed_image.is_file():
                    missing.append("mixed_image")
                if not wrench.is_file():
                    missing.append("_norm.npy")
                skipped.append(f"{relative.as_posix()} (missing: {', '.join(missing)})")
    print(f"Objects with complete samples: {len(by_object)}")
    print(f"Invalid samples skipped: {len(skipped)}")
    for item in skipped:
        print(f"  - {item}")
    return by_object


def save(root: Path, name: str, samples: Sequence[Sample], field: str) -> None:
    values = np.array(
        [getattr(sample, field).relative_to(root).as_posix() for sample in samples]
    )
    np.save(str(root / name), values, allow_pickle=False)


def main() -> None:
    args = parse_args()
    root = args.dataset_root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Dataset directory does not exist: {root}")
    by_object = collect(root, args.object_number)
    object_ids = sorted(by_object)
    if not object_ids:
        raise SystemExit("No complete samples are available; no split files were written.")

    rng = random.Random(args.seed)
    if len(object_ids) >= 2:
        test_object_count = min(args.test_object_number, len(object_ids) - 1)
    else:
        test_object_count = 0
        print(
            "Warning: only one valid object is available, so both object sets cannot be nonempty."
        )
    test_objects = set(rng.sample(object_ids, test_object_count))
    train_samples = [sample for oid in object_ids if oid not in test_objects for sample in by_object[oid]]
    test_samples = [sample for oid in object_ids if oid in test_objects for sample in by_object[oid]]
    rng.shuffle(train_samples)
    rng.shuffle(test_samples)

    train_objects = {sample.object_id for sample in train_samples}
    observed_test_objects = {sample.object_id for sample in test_samples}
    if train_objects & observed_test_objects:
        raise RuntimeError("Object leakage detected between training and test splits")

    save(root, "train_images_object.npy", train_samples, "image")
    save(root, "test_images_object.npy", test_samples, "image")
    save(root, "train_mixed_images_object.npy", train_samples, "mixed_image")
    save(root, "test_mixed_images_object.npy", test_samples, "mixed_image")
    save(root, "train_wrench_object.npy", train_samples, "wrench")
    save(root, "test_wrench_object.npy", test_samples, "wrench")
    print(f"Random seed: {args.seed}")
    print(f"Test objects: {sorted(test_objects)}")
    print(f"Training samples: {len(train_samples)}; test samples: {len(test_samples)}")


if __name__ == "__main__":
    main()
