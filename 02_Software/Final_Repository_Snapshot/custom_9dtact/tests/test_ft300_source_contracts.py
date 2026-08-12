"""Static offline contracts for the active FT300 and ROS workflow."""

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROS_PACKAGE = PROJECT_ROOT / "ros_ws" / "src" / "9dtact_ft300_ros"


class SourceContractTests(unittest.TestCase):
    def test_active_code_has_no_rokubimini_or_bota_driver_reference(self):
        active_roots = [
            PROJECT_ROOT / "data_collection",
            PROJECT_ROOT / "force_estimation",
            PROJECT_ROOT / "shape-force_ros",
            PROJECT_ROOT / "ros_ws",
        ]
        forbidden = ("rokubimini", "/bus0/ft_sensor0", "bota_driver")
        findings = []
        for root in active_roots:
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in {
                    ".py",
                    ".yaml",
                    ".launch",
                    ".xml",
                    ".txt",
                    ".md",
                }:
                    continue
                text = path.read_text(encoding="utf-8-sig").lower()
                for token in forbidden:
                    if token in text:
                        findings.append("{}: {}".format(path, token))
        self.assertEqual(findings, [])

    def test_all_owned_python_uses_python38_grammar(self):
        roots = [
            PROJECT_ROOT / "data_collection",
            PROJECT_ROOT / "data",
            PROJECT_ROOT / "force_estimation",
            PROJECT_ROOT / "shape-force_ros",
            PROJECT_ROOT / "tools",
            ROS_PACKAGE / "scripts",
        ]
        failures = []
        for root in roots:
            for path in root.rglob("*.py"):
                try:
                    ast.parse(
                        path.read_text(encoding="utf-8-sig"),
                        filename=str(path),
                        feature_version=8,
                    )
                except SyntaxError as exc:
                    failures.append("{}: {}".format(path, exc))
        self.assertEqual(failures, [])

    def test_catkin_package_and_exact_launch_set(self):
        package = ET.parse(str(ROS_PACKAGE / "package.xml")).getroot()
        self.assertEqual(package.findtext("name"), "nine_dtact_ft300_ros")
        expected = {
            "sensor1_shape.launch",
            "sensor2_shape.launch",
            "ft300_collection.launch",
            "force_estimation.launch",
            "shape_force_demo.launch",
            "compare_prediction_with_ft300.launch",
        }
        actual = {path.name for path in (ROS_PACKAGE / "launch").glob("*.launch")}
        self.assertEqual(actual, expected)
        for path in (ROS_PACKAGE / "launch").glob("*.launch"):
            ET.parse(str(path))

    def test_ros_prediction_source_sets_physical_header_and_normalized_topic(self):
        source = (
            PROJECT_ROOT / "shape-force_ros" / "_3_Force_Estimation_ros.py"
        ).read_text(encoding="utf-8")
        self.assertIn("self.estimator.denormalize(normalized)", source)
        self.assertIn("message.header.stamp", source)
        self.assertIn("message.header.frame_id", source)
        self.assertIn("Float64MultiArray", source)

    def test_legacy_collector_is_not_in_active_data_collection(self):
        self.assertFalse((PROJECT_ROOT / "data_collection" / "collect_data.py").exists())
        self.assertTrue(
            (
                PROJECT_ROOT
                / "legacy"
                / "bota"
                / "collect_data_bota_legacy.py"
            ).is_file()
        )

    def test_collector_debounce_updates_only_after_successful_atomic_save(self):
        source = (
            PROJECT_ROOT / "data_collection" / "collect_data_ft300.py"
        ).read_text(encoding="utf-8")
        self.assertIn("if self.save_sample(image, wrench):", source)
        self.assertIn("def save_sample(self, image: np.ndarray, wrench: np.ndarray) -> bool", source)

    def test_ft300_topic_checker_verifies_master_advertised_type(self):
        source = (
            PROJECT_ROOT / "tools" / "check_ft300_topic.py"
        ).read_text(encoding="utf-8")
        self.assertIn("rospy.get_published_topics", source)
        self.assertIn('expected_type = "geometry_msgs/WrenchStamped"', source)
        self.assertIn("ROS master query failed", source)

    def test_combined_demo_publishes_image_reference_and_representation(self):
        source = (
            PROJECT_ROOT / "shape-force_ros" / "_4_Shape_Force_ros.py"
        ).read_text(encoding="utf-8")
        self.assertIn("reference_publisher.publish(reference_message)", source)
        self.assertIn("image_publisher.publish(image_message)", source)
        self.assertIn("representation_publisher.publish(message)", source)


if __name__ == "__main__":
    unittest.main()
