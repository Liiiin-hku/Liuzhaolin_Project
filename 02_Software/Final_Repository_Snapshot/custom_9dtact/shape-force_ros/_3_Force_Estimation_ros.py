#!/usr/bin/env python3
"""Publish physical 9DTact force predictions from deformation images in ROS 1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import ros_numpy
import rospy
import yaml
from geometry_msgs.msg import WrenchStamped
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from force_estimation import Estimator  # noqa: E402


def load_yaml(path: Path):
    if not path.is_file():
        raise FileNotFoundError(
            "Force configuration is missing: {}. Run tools/activate_sensor.py first.".format(
                path
            )
        )
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Force configuration must be a YAML mapping: {}".format(path))
    return config


class ForceROS:
    def __init__(self, config):
        self.estimator = Estimator(config)
        self.representation_topic = str(
            rospy.get_param("~representation_topic", "/deformation_representation")
        )
        self.predicted_topic = str(
            rospy.get_param("~predicted_wrench_topic", "/predicted_wrench")
        )
        self.normalized_topic = str(
            rospy.get_param(
                "~predicted_normalized_topic", "/predicted_wrench_normalized"
            )
        )
        self.publish_normalized = bool(rospy.get_param("~publish_normalized", True))
        self.wrench_frame = str(
            rospy.get_param("~wrench_frame", self.estimator.wrench_frame)
        ).strip()
        if not self.wrench_frame:
            raise ValueError("~wrench_frame must not be empty")

        self.predicted_wrench_pub = rospy.Publisher(
            self.predicted_topic, WrenchStamped, queue_size=1
        )
        self.normalized_pub = (
            rospy.Publisher(self.normalized_topic, Float64MultiArray, queue_size=1)
            if self.publish_normalized
            else None
        )
        self.representation_sub = rospy.Subscriber(
            self.representation_topic, Image, self.predict_callback, queue_size=1
        )

    @staticmethod
    def fill_wrench(message: WrenchStamped, values: np.ndarray) -> None:
        message.wrench.force.x = float(values[0])
        message.wrench.force.y = float(values[1])
        message.wrench.force.z = float(values[2])
        message.wrench.torque.x = float(values[3])
        message.wrench.torque.y = float(values[4])
        message.wrench.torque.z = float(values[5])

    def predict_callback(self, image_message: Image) -> None:
        try:
            representation = ros_numpy.numpify(image_message)
            normalized = self.estimator.predict_normalized(representation)
            physical = self.estimator.denormalize(normalized)
        except Exception as exc:
            rospy.logerr_throttle(1.0, "Force prediction failed: %s", exc)
            return
        message = WrenchStamped()
        message.header.stamp = (
            image_message.header.stamp
            if image_message.header.stamp != rospy.Time(0)
            else rospy.Time.now()
        )
        message.header.frame_id = self.wrench_frame
        self.fill_wrench(message, physical)
        self.predicted_wrench_pub.publish(message)
        if self.normalized_pub is not None:
            normalized_message = Float64MultiArray()
            normalized_message.data = [float(value) for value in normalized]
            self.normalized_pub.publish(normalized_message)

    def run(self) -> None:
        rospy.loginfo("Publishing physical predictions on %s", self.predicted_topic)
        rospy.spin()


def main() -> None:
    rospy.init_node("nine_dtact_force_estimation")
    default_config = PROJECT_ROOT / "force_estimation" / "force_config.yaml"
    config_path = Path(str(rospy.get_param("~force_config", str(default_config)))).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    force_ros = ForceROS(load_yaml(config_path.resolve()))
    force_ros.run()


if __name__ == "__main__":
    main()
