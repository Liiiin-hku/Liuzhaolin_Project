"""Offline provenance and interaction-contract checks for the Ubuntu tool."""

import ast
import hashlib
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "shape_reconstruction"
    / "manual_camera_calibration_v2.py"
)
UBUNTU_EXPORT_SHA256 = "0511f4688f6cc5b9e9d721596af9660d736dbc4c6d1e73869ab5df7d861bcf75"


class ManualCameraCalibrationV2ContractTests(unittest.TestCase):
    def test_exact_ubuntu_export_provenance(self):
        self.assertTrue(SCRIPT.is_file())
        self.assertEqual(hashlib.sha256(SCRIPT.read_bytes()).hexdigest(), UBUNTU_EXPORT_SHA256)

    def test_python_38_syntax_and_required_workflow(self):
        text = SCRIPT.read_text(encoding="utf-8-sig")
        ast.parse(text, filename=str(SCRIPT), feature_version=8)
        for required in (
            "--capture",
            "--resume",
            "--no-snap",
            "POINT_COUNT = ROWS * COLS",
            'ord("u")',
            'ord("a")',
            'ord("s")',
            "backup_old_outputs",
            'np.save(output_dir / "row_index.npy"',
            'np.save(output_dir / "col_index.npy"',
            'np.save(output_dir / "position_scale.npy"',
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
