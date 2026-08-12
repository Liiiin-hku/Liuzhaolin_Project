#!/usr/bin/env python3
"""Render shape reconstruction from ROS images without opening a second camera."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import ros_numpy
import rospy
import yaml
from sensor_msgs.msg import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from shape_reconstruction import Sensor  # noqa: E402
from shape_visualizer import Visualizer  # noqa: E402


class ShapeROS:
    def __init__(self, config):
        reference_topic = str(
            rospy.get_param("~reference_image_topic", "/rectify_crop_ref_image")
        )
        image_topic = str(rospy.get_param("~image_topic", "/rectify_crop_image"))
        startup_timeout = float(rospy.get_param("~startup_timeout", 15.0))
        try:
            reference_message = rospy.wait_for_message(
                reference_topic, Image, timeout=startup_timeout
            )
        except rospy.ROSException as exc:
            raise RuntimeError("Reference-image wait failed: {}".format(exc))
        reference = ros_numpy.numpify(reference_message)
        rospy.loginfo("Received reference image from %s", reference_topic)
        # The sensor publisher owns the tactile camera. This subscriber-only node
        # must not open the same camera a second time.
        self.sensor = Sensor(config, ref=reference, open_camera=False)
        self.visualizer = Visualizer(self.sensor.points)
        self.height_map = self.map(cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY))
        self.image_subscriber = rospy.Subscriber(
            image_topic, Image, self.reconstruction, queue_size=1
        )

    def map(self, gray_image):
        height_map = self.sensor.raw_image_2_height_map(gray_image)
        return self.sensor.expand_image(height_map)

    def reconstruction(self, image_message):
        image = ros_numpy.numpify(image_message)
        self.height_map = self.map(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))

    def run(self):
        rate = rospy.Rate(60)
        while not rospy.is_shutdown():
            if not self.visualizer.vis.poll_events():
                break
            points, gradients = self.sensor.height_map_2_point_cloud_gradients(
                self.height_map
            )
            self.visualizer.update(points, gradients)
            rate.sleep()


def load_config(path: Path):
    if not path.is_file():
        raise FileNotFoundError(
            "Shape configuration is missing: {}. Run tools/activate_sensor.py first.".format(
                path
            )
        )
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Shape configuration must be a YAML mapping")
    return config


def main():
    rospy.init_node("nine_dtact_shape_reconstruction")
    default = PROJECT_ROOT / "shape_reconstruction" / "shape_config.yaml"
    config_path = Path(str(rospy.get_param("~shape_config", str(default)))).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    node = ShapeROS(load_config(config_path.resolve()))
    node.run()


if __name__ == "__main__":
    main()
