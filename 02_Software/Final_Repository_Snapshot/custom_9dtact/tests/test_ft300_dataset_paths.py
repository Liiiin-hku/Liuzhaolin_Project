"""Offline tests for portable dataset split paths and object separation."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.path_utils import resolve_dataset_entry  # noqa: E402
from data_collection.representation import make_mixed_image  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


split_random = load_module(
    "ft300_split_random", PROJECT_ROOT / "data_collection" / "split_train_test.py"
)
split_object = load_module(
    "ft300_split_object",
    PROJECT_ROOT / "data_collection" / "split_train_test_by_object.py",
)
integrity = load_module(
    "ft300_dataset_integrity", PROJECT_ROOT / "tools" / "check_dataset_integrity.py"
)


class DatasetPathTests(unittest.TestCase):
    def make_dataset(self, root):
        for object_id in (1, 2, 3):
            for directory in ("image", "mixed_image", "wrench"):
                (root / directory / str(object_id)).mkdir(parents=True, exist_ok=True)
            for sample_id in (1, 2):
                (root / "image" / str(object_id) / (str(sample_id) + ".png")).write_bytes(
                    b"png"
                )
                (
                    root / "mixed_image" / str(object_id) / (str(sample_id) + ".png")
                ).write_bytes(b"png")
                np.save(
                    str(root / "wrench" / str(object_id) / (str(sample_id) + ".npy")),
                    np.array([0.0, 0.0, -1.0, 0.0, 0.0, 0.0]),
                    allow_pickle=False,
                )
                np.save(
                    str(
                        root
                        / "wrench"
                        / str(object_id)
                        / (str(sample_id) + "_norm.npy")
                    ),
                    np.array([0.5, 0.5, 0.9, 0.5, 0.5, 0.5]),
                    allow_pickle=False,
                )

    def test_random_split_saves_only_dataset_relative_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.make_dataset(root)
            samples = split_random.find_samples(root)
            split_random.save_paths(root, "paths.npy", samples, "image")
            values = np.load(str(root / "paths.npy"), allow_pickle=False)
            self.assertTrue(all(not Path(str(value)).is_absolute() for value in values))
            self.assertTrue(all(str(value).startswith("image/") for value in values))

    def test_standard_split_keeps_each_object_in_only_one_set(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.make_dataset(root)
            samples = split_random.find_samples(root)
            train, test, train_objects, test_objects = split_random.split_by_object(
                samples, test_ratio=0.34, test_object_number=None, seed=7
            )
            self.assertFalse(train_objects & test_objects)
            self.assertEqual(
                {sample.object_id for sample in train}, train_objects
            )
            self.assertEqual({sample.object_id for sample in test}, test_objects)
            self.assertEqual(len(train) + len(test), len(samples))
            split_random.save_safe_split_indexes(root, train, test)
            for stem in (
                "train_images",
                "test_images",
                "train_mixed_images",
                "test_mixed_images",
                "train_wrench",
                "test_wrench",
            ):
                standard = np.load(str(root / (stem + ".npy")), allow_pickle=False)
                object_alias = np.load(
                    str(root / (stem + "_object.npy")), allow_pickle=False
                )
                np.testing.assert_array_equal(standard, object_alias)
            errors = []
            integrity.check_split_files(root, errors)
            self.assertEqual(errors, [])

    def test_object_split_has_disjoint_object_sets_and_relative_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.make_dataset(root)
            by_object = split_object.collect(root, 3)
            train = by_object[1] + by_object[2]
            test = by_object[3]
            self.assertFalse(
                {item.object_id for item in train} & {item.object_id for item in test}
            )
            split_object.save(root, "train_images_object.npy", train, "image")
            split_object.save(root, "test_images_object.npy", test, "image")
            split_object.save(
                root, "train_mixed_images_object.npy", train, "mixed_image"
            )
            split_object.save(
                root, "test_mixed_images_object.npy", test, "mixed_image"
            )
            split_object.save(root, "train_wrench_object.npy", train, "wrench")
            split_object.save(root, "test_wrench_object.npy", test, "wrench")
            errors = []
            integrity.check_split_files(root, errors)
            self.assertEqual(errors, [])

    def test_legacy_windows_path_relocates_to_moved_dataset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "Dataset_sensor_1"
            root.mkdir()
            legacy = r"C:\\old\\Dataset_sensor_1\\image\\2\\4.png"
            resolved = resolve_dataset_entry(root, legacy)
            self.assertEqual(resolved, root / "image" / "2" / "4.png")

    def test_collector_representation_preserves_sensor_uint8_semantics(self):
        reference = np.array([[0, 100, 255]], dtype=np.uint8)
        sample = np.array([[100, 0, 0]], dtype=np.uint8)
        mixed = make_mixed_image(reference, sample)
        np.testing.assert_array_equal(mixed[:, :, 0], reference)
        np.testing.assert_array_equal(mixed[:, :, 1], [[44, 0, 0]])
        np.testing.assert_array_equal(mixed[:, :, 2], [[0, 44, 253]])

    def test_normalization_metadata_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "Dataset_sensor_1"
            root.mkdir()
            metadata = {
                "dataset_root": str(root),
                "sensor_id": 1,
                "img_size": [280, 380],
                "axis_order": ["Fx", "Fy", "Fz", "Tx", "Ty", "Tz"],
                "units": {"force": "N", "torque": "N*m"},
                "wrench_min": [-3, -3, -12, -0.2, -0.2, -0.05],
                "wrench_max": [3, 3, 0, 0.2, 0.2, 0.05],
            }
            import json

            path = root / "wrench_normalization_parameters.json"
            path.write_text(json.dumps(metadata), encoding="utf-8")
            errors = []
            integrity.check_normalization_parameters(root, errors)
            self.assertEqual(errors, [])
            metadata["sensor_id"] = 2
            path.write_text(json.dumps(metadata), encoding="utf-8")
            errors = []
            integrity.check_normalization_parameters(root, errors)
            self.assertTrue(any("sensor_id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
