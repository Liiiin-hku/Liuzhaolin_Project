#!/usr/bin/env python3
"""Publish rectified tactile images and deformation representations in ROS 1."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import rospy
import yaml
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shape_reconstruction import Sensor  # noqa: E402


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
    camera_override = int(rospy.get_param("~camera_channel", -1))
    if camera_override >= 0:
        config["camera_setting"]["camera_channel"] = camera_override
    return config


def main() -> None:
    rospy.init_node("nine_dtact_sensor")
    default = PROJECT_ROOT / "shape_reconstruction" / "shape_config.yaml"
    config_path = Path(str(rospy.get_param("~shape_config", str(default)))).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    config = load_config(config_path.resolve())
    sensor = Sensor(config)
    bridge = CvBridge()

    reference_topic = str(
        rospy.get_param("~reference_image_topic", "/rectify_crop_ref_image")
    )
    image_topic = str(rospy.get_param("~image_topic", "/rectify_crop_image"))
    representation_topic = str(
        rospy.get_param("~representation_topic", "/deformation_representation")
    )
    headless = bool(rospy.get_param("~headless", False))
    reference_publisher = rospy.Publisher(
        reference_topic, Image, queue_size=1, latch=True
    )
    image_publisher = rospy.Publisher(image_topic, Image, queue_size=1)
    representation_publisher = rospy.Publisher(
        representation_topic, Image, queue_size=1
    )

    reference_message = bridge.cv2_to_imgmsg(sensor.ref, encoding="bgr8")
    reference_message.header.stamp = rospy.Time.now()
    reference_message.header.frame_id = "tactile_camera"
    reference_publisher.publish(reference_message)

    fps = float(config.get("camera_setting", {}).get("fps", 30))
    rate = rospy.Rate(max(fps, 1.0))
    try:
        while not rospy.is_shutdown():
            image = sensor.get_rectify_crop_image()
            stamp = rospy.Time.now()
            if not headless:
                cv2.imshow("rectify_crop_image", image)
            image_message = bridge.cv2_to_imgmsg(image, encoding="bgr8")
            image_message.header.stamp = stamp
            image_message.header.frame_id = "tactile_camera"
            image_publisher.publish(image_message)

            representation, visualization = sensor.raw_image_2_representation(
                cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            )
            if not headless:
                cv2.imshow("mixed_visualization", visualization)
            representation_message = bridge.cv2_to_imgmsg(
                representation, encoding="passthrough"
            )
            representation_message.header.stamp = stamp
            representation_message.header.frame_id = "tactile_sensor"
            representation_publisher.publish(representation_message)
            if not headless and cv2.waitKey(1) & 0xFF == ord("q"):
                rospy.signal_shutdown("User requested shutdown")
                break
            rate.sleep()
    finally:
        if hasattr(sensor, "close"):
            sensor.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
