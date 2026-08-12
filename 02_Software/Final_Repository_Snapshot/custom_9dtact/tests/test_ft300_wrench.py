"""Offline tests for physical six-axis FT300 wrench utilities."""

import sys
import tempfile
import unittest
import warnings
import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from force_estimation.wrench import (  # noqa: E402
    WrenchConfigurationError,
    denormalize_wrench,
    inference_metadata,
    load_dataset_normalization_metadata,
    load_inference_metadata,
    normalize_wrench,
    normalized_distance,
    process_wrench,
    rotation_matrix,
    transform_wrench,
    vector6,
    wrench_limits,
    write_inference_metadata,
)


class WrenchUtilityTests(unittest.TestCase):
    def setUp(self):
        self.minimum = np.array([-3.0, -3.0, -12.0, -0.2, -0.2, -0.05])
        self.maximum = np.array([3.0, 3.0, 0.0, 0.2, 0.2, 0.05])

    def force_config(self):
        return {
            "sensor_id": 1,
            "img_size": [280, 380],
            "wrench_frame": "tactile_sensor",
            "wrench_min": self.minimum.tolist(),
            "wrench_max": self.maximum.tolist(),
        }

    def test_vector_rejects_wrong_shape_and_nonfinite_values(self):
        with self.assertRaises(WrenchConfigurationError):
            vector6([1.0, 2.0])
        with self.assertRaises(WrenchConfigurationError):
            vector6([0.0, 0.0, np.nan, 0.0, 0.0, 0.0])

    def test_configured_limits_do_not_warn(self):
        config = {
            "wrench_min": self.minimum.tolist(),
            "wrench_max": self.maximum.tolist(),
        }
        with warnings.catch_warnings(record=True) as caught:
            low, high = wrench_limits(config)
        self.assertEqual(caught, [])
        np.testing.assert_array_equal(low, self.minimum)
        np.testing.assert_array_equal(high, self.maximum)

    def test_legacy_limit_fallback_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            wrench_limits({})
        self.assertTrue(any("legacy 9DTact defaults" in str(item.message) for item in caught))

    def test_normalize_denormalize_round_trip(self):
        physical = np.array([1.5, -1.5, -6.0, 0.1, -0.1, 0.0])
        normalized = normalize_wrench(physical, self.minimum, self.maximum)
        recovered = denormalize_wrench(normalized, self.minimum, self.maximum)
        np.testing.assert_allclose(recovered, physical, atol=1e-12)

    def test_bias_axis_sign_and_identity_transform(self):
        raw = np.array([2.0, 3.0, 4.0, 0.4, 0.5, 0.6])
        bias = np.array([1.0, 1.0, 1.0, 0.1, 0.1, 0.1])
        signs = np.array([1.0, -1.0, -1.0, 1.0, -1.0, 1.0])
        result = process_wrench(raw, bias=bias, axis_signs=signs)
        np.testing.assert_allclose(result, (raw - bias) * signs)

    def test_rotation_and_lever_arm_torque(self):
        rotation = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        source = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        transformed = transform_wrench(
            source, rotation=rotation, translation=[1.0, 0.0, 0.0]
        )
        np.testing.assert_allclose(transformed[:3], [0.0, 1.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(transformed[3:], [0.0, 0.0, 1.0], atol=1e-12)

    def test_invalid_rotation_is_rejected(self):
        with self.assertRaises(WrenchConfigurationError):
            rotation_matrix(np.ones(9))

    def test_distance_is_dimensionless_and_zero_for_equal_values(self):
        value = np.array([0.0, 0.0, -6.0, 0.0, 0.0, 0.0])
        self.assertEqual(
            normalized_distance(value, value, self.minimum, self.maximum), 0.0
        )

    def test_model_metadata_round_trip_and_exact_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path = write_inference_metadata(directory, self.force_config())
            self.assertTrue(path.is_file())
            loaded = load_inference_metadata(directory, self.force_config())
            expected = inference_metadata(self.force_config())
            for key, value in expected.items():
                self.assertEqual(loaded[key], value)
            self.assertIsNone(loaded["dataset_normalization_metadata"])

    def test_model_metadata_rejects_range_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_inference_metadata(directory, self.force_config())
            changed = self.force_config()
            changed["wrench_min"] = [-4.0, -3.0, -12.0, -0.2, -0.2, -0.05]
            with self.assertRaises(WrenchConfigurationError):
                load_inference_metadata(directory, changed)

    def test_legacy_model_metadata_fallback_is_never_silent(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                metadata = load_inference_metadata(directory, self.force_config())
            self.assertEqual(metadata["sensor_id"], 1)
            self.assertTrue(any("Legacy checkpoint" in str(item.message) for item in caught))
            with self.assertRaises(WrenchConfigurationError):
                load_inference_metadata(
                    directory, self.force_config(), allow_legacy_fallback=False
                )

    def test_dataset_normalization_metadata_matches_and_is_snapshotted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "Dataset_sensor_1"
            directory.mkdir()
            metadata = {
                "schema_version": 2,
                "dataset_root": r"C:\\old\\Dataset_sensor_1",
                "sensor_id": 1,
                "img_size": [280, 380],
                "axis_order": ["Fx", "Fy", "Fz", "Tx", "Ty", "Tz"],
                "units": {"force": "N", "torque": "N*m"},
                "wrench_min": self.minimum.tolist(),
                "wrench_max": self.maximum.tolist(),
            }
            (directory / "wrench_normalization_parameters.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            loaded = load_dataset_normalization_metadata(
                directory, self.force_config()
            )
            model_directory = Path(temporary) / "model"
            path = write_inference_metadata(
                model_directory, self.force_config(), dataset_metadata=loaded
            )
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["dataset_normalization_metadata"]["sensor_id"], 1)
            self.assertNotIn(
                "dataset_root", saved["dataset_normalization_metadata"]
            )

    def test_dataset_normalization_metadata_rejects_config_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "Dataset_sensor_1"
            directory.mkdir()
            metadata = {
                "sensor_id": 1,
                "img_size": [280, 380],
                "wrench_min": self.minimum.tolist(),
                "wrench_max": self.maximum.tolist(),
            }
            metadata["wrench_max"][0] = 4.0
            (directory / "wrench_normalization_parameters.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            with self.assertRaises(WrenchConfigurationError):
                load_dataset_normalization_metadata(directory, self.force_config())

    def test_legacy_dataset_metadata_fallback_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "Dataset_sensor_1"
            directory.mkdir()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                loaded = load_dataset_normalization_metadata(
                    directory, self.force_config()
                )
            self.assertIsNone(loaded)
            self.assertTrue(any("Legacy dataset" in str(item.message) for item in caught))


if __name__ == "__main__":
    unittest.main()
