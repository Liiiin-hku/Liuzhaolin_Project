"""Pure construction of the deformation representation used by 9DTact."""

from __future__ import annotations

import numpy as np


def make_mixed_image(reference_gray: np.ndarray, sample_gray: np.ndarray) -> np.ndarray:
    """Mirror ``Sensor.raw_image_2_representation`` training-image semantics.

    The upstream algorithm assigns ``float32_difference * 3`` directly into
    uint8 channels. Values above 255 therefore use NumPy's uint8 cast behavior;
    they are deliberately not clipped here because saved training data and live
    inference must use the same representation.
    """

    reference = np.asarray(reference_gray)
    sample = np.asarray(sample_gray)
    if reference.ndim != 2 or sample.ndim != 2 or reference.shape != sample.shape:
        raise ValueError("Reference and sample must be same-shape grayscale images")
    if reference.dtype != np.uint8 or sample.dtype != np.uint8:
        raise ValueError("Reference and sample grayscale images must use uint8")

    darker = reference.astype(np.float32) - sample.astype(np.float32)
    darker[darker < 0] = 0
    brighter = sample.astype(np.float32) - reference.astype(np.float32)
    brighter[brighter < 0] = 0
    mixed = np.zeros((reference.shape[0], reference.shape[1], 3), dtype=np.uint8)
    mixed[:, :, 0] = reference
    mixed[:, :, 1] = brighter * 3
    mixed[:, :, 2] = darker * 3
    return mixed
