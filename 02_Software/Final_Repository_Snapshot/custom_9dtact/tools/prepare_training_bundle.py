#!/usr/bin/env python3
"""Create a portable training bundle for one 9DTact sensor."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GITHUB_ROOT = PROJECT_ROOT.parent
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".git", ".idea"}
EXCLUDED_SUFFIXES = {".log", ".tmp", ".pyc", ".pyo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a GPU training bundle for a specified sensor"
    )
    parser.add_argument("--sensor-id", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def ignore_entries(_directory: str, names: List[str]) -> Iterable[str]:
    return [
        name
        for name in names
        if name in EXCLUDED_NAMES or Path(name).suffix.lower() in EXCLUDED_SUFFIXES
    ]


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"Missing directory: {source}")
    shutil.copytree(source, destination, ignore=ignore_entries)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def write_counts(bundle_root: Path, sensor_id: int) -> None:
    dataset = bundle_root / f"Dataset_sensor_{sensor_id}"
    counts = {
        "image PNG": len(list((dataset / "image").rglob("*.png"))),
        "mixed_image PNG": len(list((dataset / "mixed_image").rglob("*.png"))),
        "Raw wrench NPY": len(
            [
                path
                for path in (dataset / "wrench").rglob("*.npy")
                if not path.name.endswith("_norm.npy")
            ]
        ),
        "Normalized wrench NPY": len(list((dataset / "wrench").rglob("*_norm.npy"))),
    }
    lines = [f"# Sensor {sensor_id} Data File Counts", ""]
    lines.extend(f"- {name}: {count}" for name, count in counts.items())
    lines.append("")
    with (bundle_root / "DATA_COUNTS.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write("\n".join(lines))


def write_training_guide(bundle_root: Path, sensor_id: int) -> None:
    guide = f"""# Sensor {sensor_id} GPU Training Guide

This training bundle contains only the Sensor {sensor_id} dataset and Force configuration.
It does not contain the other sensor's dataset. See
[docs/01_INSTALLATION_UBUNTU20.md](docs/01_INSTALLATION_UBUNTU20.md) for the
complete environment guide.

1. Recreate a Python 3.8 environment on the target computer. Do not copy a Conda or venv
   directory from another computer.
2. Install `requirements.txt`, then install `requirements-pytorch.txt` from the
   CPU or CUDA package index selected for the target computer.
3. The selected template is already copied to `force_estimation/force_config.yaml`.
   Review the dataset, output, model, and wrench-range settings before training.
4. From this bundle root, run `python -m compileall -q .` and then
   `cd force_estimation && python train.py`.
5. Set `model_choice` to `0` and run ResNet18 for one or two epochs as a pipeline
   smoke test before starting a long run.
6. After the pipeline works correctly, set `model_choice` to `1` for full DenseNet169
   training.
7. After training, record the selected model's directory suffix and epoch in the
   corresponding template. Do not place the model in the other sensor's model directory.
"""
    with (bundle_root / "TRAIN_ON_GPU.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(guide)


def write_manifest(bundle_root: Path) -> None:
    manifest_path = bundle_root / "SHA256_MANIFEST.csv"
    files = sorted(
        (path for path in bundle_root.rglob("*") if path.is_file() and path != manifest_path),
        key=lambda path: path.relative_to(bundle_root).as_posix(),
    )
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "size", "sha256"])
        for path in files:
            writer.writerow(
                [path.relative_to(bundle_root).as_posix(), path.stat().st_size, sha256(path)]
            )


def validate_bundle(bundle_root: Path, sensor_id: int) -> None:
    """Run dependency-free structural and Python-syntax checks before packaging."""
    required = [
        bundle_root / f"Dataset_sensor_{sensor_id}",
        bundle_root / "data" / "dtact_dataset.py",
        bundle_root / "model" / "cnn.py",
        bundle_root / "force_estimation" / "train.py",
        bundle_root / "force_estimation" / "wrench.py",
        bundle_root / "force_estimation" / "force_config.yaml",
        bundle_root / "data_collection" / "split_train_test.py",
        bundle_root / "tools" / "check_dataset_integrity.py",
        bundle_root / "requirements-core.txt",
        bundle_root / "requirements-training.txt",
        bundle_root / "requirements-pytorch.txt",
    ]
    missing = [path.relative_to(bundle_root).as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Training bundle is incomplete: " + ", ".join(missing))

    syntax_errors = []
    for path in sorted(bundle_root.rglob("*.py")):
        try:
            ast.parse(
                path.read_text(encoding="utf-8-sig"),
                filename=str(path),
                feature_version=8,
            )
        except (SyntaxError, UnicodeError) as exc:
            syntax_errors.append(f"{path.relative_to(bundle_root).as_posix()}: {exc}")
    if syntax_errors:
        raise RuntimeError("Python syntax validation failed: " + "; ".join(syntax_errors))

    report = [
        "# Training Bundle Structural Validation",
        "",
        f"- Sensor ID: {sensor_id}",
        "- Required training modules: present",
        "- Selected force configuration: present",
        "- Python source syntax: passed",
        "- Model execution: requires the target PyTorch environment and is not claimed here",
        "- Hardware acquisition: not performed by this packaging tool",
        "",
    ]
    with (bundle_root / "BUNDLE_VALIDATION.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write("\n".join(report))


def build_bundle(destination: Path, sensor_id: int) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    copy_tree(
        PROJECT_ROOT / f"Dataset_sensor_{sensor_id}",
        destination / f"Dataset_sensor_{sensor_id}",
    )
    copy_tree(PROJECT_ROOT / "force_estimation", destination / "force_estimation")
    copy_tree(PROJECT_ROOT / "data", destination / "data")
    copy_tree(PROJECT_ROOT / "model", destination / "model")

    collection_dir = destination / "data_collection"
    collection_dir.mkdir()
    for name in (
        "split_train_test.py",
        "split_train_test_by_object.py",
        "wrench_normalization.py",
    ):
        shutil.copy2(PROJECT_ROOT / "data_collection" / name, collection_dir / name)

    configs_dir = destination / "configs"
    configs_dir.mkdir()
    template = PROJECT_ROOT / "configs" / f"force_sensor_{sensor_id}.yaml"
    shutil.copy2(template, configs_dir / template.name)
    shutil.copy2(template, destination / "force_estimation" / "force_config.yaml")

    for name in (
        "requirements.txt",
        "requirements-core.txt",
        "requirements-training.txt",
        "requirements-pytorch.txt",
        "setup.py",
        "pyproject.toml",
        "environment.yml",
    ):
        shutil.copy2(PROJECT_ROOT / name, destination / name)

    docs_dir = destination / "docs"
    docs_dir.mkdir()
    tools_dir = destination / "tools"
    tools_dir.mkdir()
    shutil.copy2(
        PROJECT_ROOT / "tools" / "check_dataset_integrity.py",
        tools_dir / "check_dataset_integrity.py",
    )

    for name in (
        "01_INSTALLATION_UBUNTU20.md",
        "08_DATA_PROCESSING.md",
        "09_MODEL_TRAINING.md",
    ):
        source = GITHUB_ROOT / "docs" / name
        if source.is_file():
            shutil.copy2(source, docs_dir / name)

    write_counts(destination, sensor_id)
    write_training_guide(destination, sensor_id)
    validate_bundle(destination, sensor_id)
    write_manifest(destination)


def main() -> None:
    args = parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        raise SystemExit(f"Output already exists; stopped to prevent overwrite: {output}")

    if is_inside(output, GITHUB_ROOT):
        print("Note: .gitignore excludes this training bundle; do not commit it to GitHub.")

    if output.suffix.lower() == ".zip":
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="9dtact_training_bundle_") as temp_dir:
            bundle = Path(temp_dir) / f"9DTact_training_sensor_{args.sensor_id}"
            build_bundle(bundle, args.sensor_id)
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(bundle.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(bundle.parent))
    else:
        build_bundle(output, args.sensor_id)

    print(f"Sensor {args.sensor_id} training bundle created: {output}")
    print("Source data was not modified; the SHA-256 manifest is inside the bundle.")


if __name__ == "__main__":
    main()
