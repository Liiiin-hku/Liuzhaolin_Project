#!/usr/bin/env python3
"""Split complete 9DTact samples without leaking objects across sets."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np


@dataclass(frozen=True)
class Sample:
    object_id: str
    image: Path
    mixed_image: Path
    wrench: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split complete 9DTact samples into disjoint train/test objects"
    )
    parser.add_argument("--dataset-root", type=Path, default=Path("../Dataset"))
    parser.add_argument("--test-ratio", type=float, default=0.2)
    count = parser.add_mutually_exclusive_group()
    count.add_argument(
        "--test-object-number",
        type=int,
        help="Exact number of complete objects assigned to the test set",
    )
    count.add_argument(
        "--test-number",
        type=int,
        help="Deprecated alias for --test-object-number (counts objects, not samples)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 0 < args.test_ratio < 1:
        parser.error("--test-ratio must be between 0 and 1")
    requested = (
        args.test_object_number
        if args.test_object_number is not None
        else args.test_number
    )
    if requested is not None and requested < 1:
        parser.error("The test-object count must be greater than 0")
    return args


def find_samples(root: Path) -> List[Sample]:
    image_root = root / "image"
    mixed_root = root / "mixed_image"
    wrench_root = root / "wrench"
    good: List[Sample] = []
    bad: List[str] = []
    for image in sorted(image_root.rglob("*.png")) if image_root.is_dir() else []:
        relative = image.relative_to(image_root)
        if len(relative.parts) < 2:
            bad.append(
                f"{relative.as_posix()} (expected image/<object_id>/<sample>.png)"
            )
            continue
        object_id = relative.parts[0]
        mixed_image = mixed_root / relative
        wrench = (wrench_root / relative).with_suffix("").with_name(relative.stem + "_norm.npy")
        missing = [
            label
            for label, path in (("image", image), ("mixed_image", mixed_image), ("_norm.npy", wrench))
            if not path.is_file()
        ]
        if missing:
            bad.append(f"{relative.as_posix()} (missing: {', '.join(missing)})")
        else:
            good.append(Sample(object_id, image, mixed_image, wrench))
    print(f"Images found: {len(good) + len(bad)}")
    print(f"Complete usable samples: {len(good)}")
    print(f"Invalid samples skipped: {len(bad)}")
    for item in bad:
        print(f"  - {item}")
    return good


def group_samples(samples: Sequence[Sample]) -> Dict[str, List[Sample]]:
    """Return complete samples grouped by the first path component/object ID."""
    grouped: Dict[str, List[Sample]] = {}
    for sample in samples:
        grouped.setdefault(sample.object_id, []).append(sample)
    return grouped


def split_by_object(
    samples: Sequence[Sample],
    test_ratio: float,
    test_object_number: Optional[int],
    seed: int,
) -> Tuple[List[Sample], List[Sample], Set[str], Set[str]]:
    """Split whole object groups and return samples plus disjoint object sets."""
    grouped = group_samples(samples)
    object_ids = sorted(grouped)
    if not object_ids:
        return [], [], set(), set()

    if test_object_number is None:
        requested = int(round(len(object_ids) * test_ratio))
    else:
        requested = test_object_number

    if len(object_ids) >= 2:
        test_count = min(max(requested, 1), len(object_ids) - 1)
    else:
        test_count = 0

    rng = random.Random(seed)
    test_objects = set(rng.sample(object_ids, test_count))
    train_objects = set(object_ids) - test_objects
    if train_objects & test_objects:
        raise RuntimeError("Object leakage detected between training and test splits")

    train_samples = [
        sample for object_id in object_ids if object_id in train_objects
        for sample in grouped[object_id]
    ]
    test_samples = [
        sample for object_id in object_ids if object_id in test_objects
        for sample in grouped[object_id]
    ]
    rng.shuffle(train_samples)
    rng.shuffle(test_samples)
    return train_samples, test_samples, train_objects, test_objects


def save_paths(root: Path, name: str, samples: Sequence[Sample], field: str) -> None:
    values = np.array(
        [getattr(sample, field).relative_to(root).as_posix() for sample in samples]
    )
    np.save(str(root / name), values, allow_pickle=False)


def save_safe_split_indexes(
    root: Path, train_samples: Sequence[Sample], test_samples: Sequence[Sample]
) -> None:
    """Write both loader naming families from the same object-disjoint split."""

    for suffix in ("", "_object"):
        save_paths(root, "train_images{}.npy".format(suffix), train_samples, "image")
        save_paths(root, "test_images{}.npy".format(suffix), test_samples, "image")
        save_paths(
            root,
            "train_mixed_images{}.npy".format(suffix),
            train_samples,
            "mixed_image",
        )
        save_paths(
            root,
            "test_mixed_images{}.npy".format(suffix),
            test_samples,
            "mixed_image",
        )
        save_paths(root, "train_wrench{}.npy".format(suffix), train_samples, "wrench")
        save_paths(root, "test_wrench{}.npy".format(suffix), test_samples, "wrench")


def main() -> None:
    args = parse_args()
    root = args.dataset_root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Dataset directory does not exist: {root}")

    samples = find_samples(root)
    if not samples:
        raise SystemExit(
            "No complete samples are available for splitting; no split files were written."
        )

    if args.test_number is not None:
        print(
            "Warning: --test-number is deprecated and is interpreted as an object "
            "count; use --test-object-number instead."
        )
    requested_objects = (
        args.test_object_number
        if args.test_object_number is not None
        else args.test_number
    )
    train_samples, test_samples, train_objects, test_objects = split_by_object(
        samples,
        test_ratio=args.test_ratio,
        test_object_number=requested_objects,
        seed=args.seed,
    )
    if len(train_objects | test_objects) == 1:
        print(
            "Warning: only one complete object is available, so both sets cannot be nonempty."
        )
    save_safe_split_indexes(root, train_samples, test_samples)

    print(f"Random seed: {args.seed}")
    print(f"Training objects: {sorted(train_objects)}")
    print(f"Test objects: {sorted(test_objects)}")
    print(f"Training samples: {len(train_samples)}")
    print(f"Test samples: {len(test_samples)}")
    print(f"Relative split paths saved to: {root}")


if __name__ == "__main__":
    main()
