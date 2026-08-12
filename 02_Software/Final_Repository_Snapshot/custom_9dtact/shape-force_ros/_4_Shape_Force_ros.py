#!/usr/bin/env python3
"""Run the combined shape display and normalized force visualization in ROS 1."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import rospy
import yaml
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = Path(__file__).resolve().parent
for directory in (PROJECT_ROOT, SCRIPT_ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from sf_visualizer import Visualizer  # noqa: E402
from shape_reconstruction import Sensor  # noqa: E402


class NormalizedWrenchState:
    def __init__(self) -> None:
        self.values = np.array([0.5, 0.5, 1.0, 0.5, 0.5, 0.5], dtype=float)

    def callback(self, message: Float64MultiArray) -> None:
        values = np.asarray(message.data, dtype=float).reshape(-1)
        if values.shape != (6,) or not np.all(np.isfinite(values)):
            rospy.logerr_throttle(1.0, "Rejected invalid normalized prediction")
            return
        self.values = np.clip(values, 0.0, 1.0)


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
    rospy.init_node("nine_dtact_shape_force_demo")
    default = PROJECT_ROOT / "shape_reconstruction" / "shape_config.yaml"
    config_path = Path(str(rospy.get_param("~shape_config", str(default)))).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    config = load_config(config_path.resolve())
    representation_topic = str(
        rospy.get_param("~representation_topic", "/deformation_representation")
    )
    normalized_topic = str(
        rospy.get_param(
            "~predicted_normalized_topic", "/predicted_wrench_normalized"
        )
    )
    image_topic = str(rospy.get_param("~image_topic", "/rectify_crop_image"))
    reference_topic = str(
        rospy.get_param("~reference_image_topic", "/rectify_crop_ref_image")
    )
    contact_height_threshold = float(
        rospy.get_param("~contact_height_threshold", 0.1)
    )
    state = NormalizedWrenchState()
    rospy.Subscriber(normalized_topic, Float64MultiArray, state.callback, queue_size=1)
    representation_publisher = rospy.Publisher(
        representation_topic, Image, queue_size=1
    )
    image_publisher = rospy.Publisher(image_topic, Image, queue_size=1)
    reference_publisher = rospy.Publisher(
        reference_topic, Image, queue_size=1, latch=True
    )
    bridge = CvBridge()
    sensor = Sensor(config)
    reference_message = bridge.cv2_to_imgmsg(sensor.ref, encoding="bgr8")
    reference_message.header.stamp = rospy.Time.now()
    reference_message.header.frame_id = "tactile_camera"
    reference_publisher.publish(reference_message)
    visualizer = Visualizer(sensor.points)
    rate = rospy.Rate(60)

    try:
        while sensor.cap.isOpened() and not rospy.is_shutdown():
            image = sensor.get_rectify_crop_image()
            stamp = rospy.Time.now()
            image_message = bridge.cv2_to_imgmsg(image, encoding="bgr8")
            image_message.header.stamp = stamp
            image_message.header.frame_id = "tactile_camera"
            image_publisher.publish(image_message)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imshow("RawImage_GRAY", gray)
            height_map = sensor.raw_image_2_height_map(gray)
            depth_map = sensor.height_map_2_depth_map(height_map)
            cv2.imshow("DepthMap", depth_map)
            expanded = sensor.expand_image(height_map)
            representation, visualization = sensor.raw_image_2_representation(gray)
            cv2.imshow("Representation", visualization)

            if float(np.max(expanded)) > contact_height_threshold:
                message = bridge.cv2_to_imgmsg(representation, encoding="passthrough")
                message.header.stamp = stamp
                message.header.frame_id = "tactile_sensor"
                representation_publisher.publish(message)
            else:
                state.values = np.array(
                    [0.5, 0.5, 1.0, 0.5, 0.5, 0.5], dtype=float
                )
            if cv2.waitKey(1) & 0xFF == ord("q"):
                rospy.signal_shutdown("User requested shutdown")
                break
            if not visualizer.vis.poll_events():
                break
            points, gradients = sensor.height_map_2_point_cloud_gradients(expanded)
            visualizer.update(points, gradients, np.copy(state.values))
            rate.sleep()
    finally:
        if hasattr(sensor, "close"):
            sensor.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
