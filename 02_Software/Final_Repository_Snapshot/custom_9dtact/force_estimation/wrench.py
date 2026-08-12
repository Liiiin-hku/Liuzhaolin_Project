"""Pure six-axis wrench validation, transformation, and scaling utilities.

The physical axis order is ``Fx, Fy, Fz, Tx, Ty, Tz``. Force values are in
newtons and torque values are in newton-metres whenever physical values are
handled. These helpers do not access ROS or hardware and are suitable for
offline tests.
"""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

import numpy as np


AXIS_NAMES = ("Fx", "Fy", "Fz", "Tx", "Ty", "Tz")
AXIS_UNITS = ("N", "N", "N", "N*m", "N*m", "N*m")
DEFAULT_WRENCH_MIN = np.array([-3.0, -3.0, -12.0, -0.2, -0.2, -0.05])
DEFAULT_WRENCH_MAX = np.array([3.0, 3.0, 0.0, 0.2, 0.2, 0.05])
INFERENCE_METADATA_FILENAME = "inference_metadata.json"
INFERENCE_METADATA_SCHEMA_VERSION = 1
DATASET_NORMALIZATION_FILENAME = "wrench_normalization_parameters.json"


class WrenchConfigurationError(ValueError):
    """Raised when a six-axis wrench configuration is inconsistent."""


def vector6(values: Sequence[float], name: str = "wrench") -> np.ndarray:
    """Return one finite float64 six-vector or raise a descriptive error."""

    result = np.asarray(values, dtype=np.float64).reshape(-1)
    if result.shape != (6,):
        raise WrenchConfigurationError(
            "{} must contain exactly 6 values; found {}".format(name, result.size)
        )
    if not np.all(np.isfinite(result)):
        raise WrenchConfigurationError("{} contains NaN or Inf".format(name))
    return result


def wrench_limits(config: Optional[Mapping[str, Any]] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Load validated physical limits from a force configuration mapping."""

    config = config or {}
    missing = [name for name in ("wrench_min", "wrench_max") if name not in config]
    if missing:
        warnings.warn(
            "Force configuration is missing {}; using legacy 9DTact defaults".format(
                ", ".join(missing)
            ),
            RuntimeWarning,
        )
    minimum = vector6(config.get("wrench_min", DEFAULT_WRENCH_MIN), "wrench_min")
    maximum = vector6(config.get("wrench_max", DEFAULT_WRENCH_MAX), "wrench_max")
    if np.any(maximum <= minimum):
        raise WrenchConfigurationError(
            "Every wrench_max component must be greater than wrench_min"
        )
    return minimum, maximum


def inference_metadata(config: Mapping[str, Any]) -> Mapping[str, Any]:
    """Build validated model-side metadata for physical wrench inference."""

    minimum, maximum = wrench_limits(config)
    try:
        sensor_id = int(config["sensor_id"])
    except (KeyError, TypeError, ValueError):
        raise WrenchConfigurationError("sensor_id must be an integer in force config")
    if sensor_id not in (1, 2):
        raise WrenchConfigurationError("sensor_id must be 1 or 2")

    image_size = np.asarray(config.get("img_size", []), dtype=np.float64).reshape(-1)
    if (
        image_size.shape != (2,)
        or not np.all(np.isfinite(image_size))
        or np.any(image_size <= 0)
        or not np.all(image_size == np.floor(image_size))
    ):
        raise WrenchConfigurationError(
            "img_size must contain exactly two positive integer values"
        )
    wrench_frame = str(config.get("wrench_frame", "")).strip()
    if not wrench_frame:
        raise WrenchConfigurationError("wrench_frame must not be empty")

    return {
        "schema_version": INFERENCE_METADATA_SCHEMA_VERSION,
        "sensor_id": sensor_id,
        "img_size": [int(value) for value in image_size],
        "axis_order": list(AXIS_NAMES),
        "axis_units": list(AXIS_UNITS),
        "wrench_min": minimum.tolist(),
        "wrench_max": maximum.tolist(),
        "wrench_frame": wrench_frame,
        "normalization": "(physical - wrench_min) / (wrench_max - wrench_min)",
    }


def validate_inference_metadata(
    metadata: Mapping[str, Any], config: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Validate model metadata and require an exact config/metadata contract."""

    if not isinstance(metadata, Mapping):
        raise WrenchConfigurationError("Inference metadata must be a JSON object")
    expected = inference_metadata(config)
    if metadata.get("schema_version") != INFERENCE_METADATA_SCHEMA_VERSION:
        raise WrenchConfigurationError(
            "Unsupported inference metadata schema_version: {}".format(
                metadata.get("schema_version")
            )
        )
    if list(metadata.get("axis_order", [])) != list(AXIS_NAMES):
        raise WrenchConfigurationError("Inference metadata axis_order is invalid")
    if list(metadata.get("axis_units", [])) != list(AXIS_UNITS):
        raise WrenchConfigurationError("Inference metadata axis_units are invalid")

    metadata_min = vector6(metadata.get("wrench_min", []), "metadata wrench_min")
    metadata_max = vector6(metadata.get("wrench_max", []), "metadata wrench_max")
    if np.any(metadata_max <= metadata_min):
        raise WrenchConfigurationError("Inference metadata wrench spans must be positive")

    scalar_fields = ("sensor_id", "img_size", "wrench_frame")
    for field in scalar_fields:
        if metadata.get(field) != expected[field]:
            raise WrenchConfigurationError(
                "Model inference metadata {}={} does not match force config {}".format(
                    field, metadata.get(field), expected[field]
                )
            )
    if not np.array_equal(metadata_min, np.asarray(expected["wrench_min"])):
        raise WrenchConfigurationError(
            "Model inference metadata wrench_min does not match force config"
        )
    if not np.array_equal(metadata_max, np.asarray(expected["wrench_max"])):
        raise WrenchConfigurationError(
            "Model inference metadata wrench_max does not match force config"
        )
    return dict(metadata)


def write_inference_metadata(
    model_directory: Path,
    config: Mapping[str, Any],
    dataset_metadata: Optional[Mapping[str, Any]] = None,
) -> Path:
    """Atomically write the physical-unit contract beside model checkpoints."""

    directory = Path(model_directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / INFERENCE_METADATA_FILENAME
    temporary = destination.with_name("." + destination.name + ".tmp")
    payload = dict(inference_metadata(config))
    if dataset_metadata is None:
        payload["dataset_normalization_metadata"] = None
    else:
        # Snapshot only the portable physical-unit contract, not host-specific paths.
        portable_fields = (
            "schema_version",
            "sensor_id",
            "img_size",
            "axis_order",
            "units",
            "wrench_min",
            "wrench_max",
            "normalization",
            "created_utc",
            "completed_utc",
        )
        payload["dataset_normalization_metadata"] = {
            key: dataset_metadata[key]
            for key in portable_fields
            if key in dataset_metadata
        }
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(str(temporary), str(destination))
    return destination


def load_inference_metadata(
    model_directory: Path,
    config: Mapping[str, Any],
    allow_legacy_fallback: bool = True,
) -> Mapping[str, Any]:
    """Load/validate model metadata, with a loud legacy-checkpoint fallback."""

    path = Path(model_directory) / INFERENCE_METADATA_FILENAME
    if not path.is_file():
        if not allow_legacy_fallback:
            raise WrenchConfigurationError(
                "Legacy checkpoint has no {}; set allow_legacy_metadata_fallback: true "
                "only after verifying its training ranges".format(
                    INFERENCE_METADATA_FILENAME
                )
            )
        warnings.warn(
            "Legacy checkpoint has no {}; using the current force YAML as an "
            "explicit fallback. Verify its original wrench ranges before treating "
            "predictions as N/N*m.".format(INFERENCE_METADATA_FILENAME),
            RuntimeWarning,
        )
        return inference_metadata(config)
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WrenchConfigurationError(
            "Unreadable model inference metadata {}: {}".format(path, exc)
        )
    return validate_inference_metadata(metadata, config)


def _portable_basename(value: Any) -> str:
    normalized = str(value).replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1]


def validate_dataset_normalization_metadata(
    metadata: Mapping[str, Any],
    dataset_directory: Path,
    config: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate dataset normalization provenance against the active force config."""

    if not isinstance(metadata, Mapping):
        raise WrenchConfigurationError(
            "Dataset normalization metadata must be a JSON object"
        )
    expected = inference_metadata(config)
    metadata_min = vector6(metadata.get("wrench_min", []), "dataset wrench_min")
    metadata_max = vector6(metadata.get("wrench_max", []), "dataset wrench_max")
    if np.any(metadata_max <= metadata_min):
        raise WrenchConfigurationError("Dataset normalization spans must be positive")
    if not np.array_equal(metadata_min, np.asarray(expected["wrench_min"])):
        raise WrenchConfigurationError(
            "Dataset normalization wrench_min does not match force config"
        )
    if not np.array_equal(metadata_max, np.asarray(expected["wrench_max"])):
        raise WrenchConfigurationError(
            "Dataset normalization wrench_max does not match force config"
        )

    if "axis_order" in metadata and list(metadata["axis_order"]) != list(AXIS_NAMES):
        raise WrenchConfigurationError("Dataset normalization axis_order is invalid")
    if "units" in metadata and metadata["units"] != {
        "force": "N",
        "torque": "N*m",
    }:
        raise WrenchConfigurationError("Dataset normalization units are invalid")
    for field in ("sensor_id", "img_size"):
        if field in metadata and metadata[field] != expected[field]:
            raise WrenchConfigurationError(
                "Dataset normalization {}={} does not match force config {}".format(
                    field, metadata[field], expected[field]
                )
            )
    if "dataset_root" in metadata:
        recorded_name = _portable_basename(metadata["dataset_root"])
        current_name = Path(dataset_directory).resolve().name
        if recorded_name != current_name:
            raise WrenchConfigurationError(
                "Dataset normalization metadata names dataset '{}' but active dataset is '{}'".format(
                    recorded_name, current_name
                )
            )
    return dict(metadata)


def load_dataset_normalization_metadata(
    dataset_directory: Path,
    config: Mapping[str, Any],
    allow_legacy_fallback: bool = True,
) -> Optional[Mapping[str, Any]]:
    """Load dataset normalization metadata, warning for explicit legacy fallback."""

    directory = Path(dataset_directory).expanduser().resolve()
    path = directory / DATASET_NORMALIZATION_FILENAME
    if not path.is_file():
        if not allow_legacy_fallback:
            raise WrenchConfigurationError(
                "Dataset has no {}; run wrench_normalization.py --apply or enable "
                "the verified legacy fallback".format(DATASET_NORMALIZATION_FILENAME)
            )
        warnings.warn(
            "Legacy dataset has no {}; using current force YAML ranges as an "
            "explicit fallback. Normalize the dataset again before final training.".format(
                DATASET_NORMALIZATION_FILENAME
            ),
            RuntimeWarning,
        )
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WrenchConfigurationError(
            "Unreadable dataset normalization metadata {}: {}".format(path, exc)
        )
    return validate_dataset_normalization_metadata(metadata, directory, config)


def normalize_wrench(
    values: Sequence[float],
    minimum: Sequence[float],
    maximum: Sequence[float],
    clip: bool = False,
) -> np.ndarray:
    """Map a physical six-vector to the configured component-wise unit range."""

    wrench = vector6(values)
    low = vector6(minimum, "wrench_min")
    high = vector6(maximum, "wrench_max")
    span = high - low
    if np.any(span <= 0):
        raise WrenchConfigurationError("Wrench normalization spans must be positive")
    normalized = (wrench - low) / span
    return np.clip(normalized, 0.0, 1.0) if clip else normalized


def denormalize_wrench(
    values: Sequence[float], minimum: Sequence[float], maximum: Sequence[float]
) -> np.ndarray:
    """Map a normalized six-vector back to physical newtons and newton-metres."""

    normalized = vector6(values, "normalized wrench")
    low = vector6(minimum, "wrench_min")
    high = vector6(maximum, "wrench_max")
    if np.any(high <= low):
        raise WrenchConfigurationError("Wrench normalization spans must be positive")
    return normalized * (high - low) + low


def rotation_matrix(values: Optional[Sequence[float]] = None) -> np.ndarray:
    """Return a proper 3x3 rotation matrix, using identity when omitted."""

    if values is None:
        return np.eye(3, dtype=np.float64)
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.size != 9:
        raise WrenchConfigurationError("rotation must contain exactly 9 values")
    matrix = matrix.reshape(3, 3)
    if not np.all(np.isfinite(matrix)):
        raise WrenchConfigurationError("rotation contains NaN or Inf")
    if not np.allclose(matrix.T.dot(matrix), np.eye(3), atol=1e-6):
        raise WrenchConfigurationError("rotation must be orthonormal")
    if not np.isclose(np.linalg.det(matrix), 1.0, atol=1e-6):
        raise WrenchConfigurationError("rotation must have determinant +1")
    return matrix


def transform_wrench(
    values: Sequence[float],
    rotation: Optional[Sequence[float]] = None,
    translation: Optional[Sequence[float]] = None,
) -> np.ndarray:
    """Apply a rigid frame transform to a physical wrench.

    ``rotation`` maps source-frame vectors into the target frame. ``translation``
    is the vector in metres from the target origin to the source origin,
    expressed in the target frame. The target torque is ``R*T + p x (R*F)``.
    """

    wrench = vector6(values)
    matrix = rotation_matrix(rotation)
    offset = np.zeros(3, dtype=np.float64)
    if translation is not None:
        offset = np.asarray(translation, dtype=np.float64).reshape(-1)
        if offset.shape != (3,) or not np.all(np.isfinite(offset)):
            raise WrenchConfigurationError(
                "translation must contain exactly 3 finite values"
            )
    force = matrix.dot(wrench[:3])
    torque = matrix.dot(wrench[3:]) + np.cross(offset, force)
    return np.concatenate((force, torque))


def process_wrench(
    raw_values: Sequence[float],
    bias: Optional[Sequence[float]] = None,
    axis_signs: Optional[Sequence[float]] = None,
    rotation: Optional[Sequence[float]] = None,
    translation: Optional[Sequence[float]] = None,
) -> np.ndarray:
    """Subtract bias, transform frames, and apply configured component signs."""

    raw = vector6(raw_values, "raw wrench")
    zero = np.zeros(6, dtype=np.float64) if bias is None else vector6(bias, "bias")
    transformed = transform_wrench(raw - zero, rotation, translation)
    signs = np.ones(6, dtype=np.float64)
    if axis_signs is not None:
        signs = vector6(axis_signs, "axis_signs")
        if not np.all(np.isin(signs, (-1.0, 1.0))):
            raise WrenchConfigurationError("axis_signs values must be -1 or 1")
    return transformed * signs


def normalized_distance(
    first: Sequence[float],
    second: Sequence[float],
    minimum: Sequence[float],
    maximum: Sequence[float],
) -> float:
    """Return a dimensionless distance without mixing N and N*m magnitudes."""

    first_norm = normalize_wrench(first, minimum, maximum)
    second_norm = normalize_wrench(second, minimum, maximum)
    return float(np.linalg.norm(first_norm - second_norm))
