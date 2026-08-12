#!/usr/bin/env python3
"""Compare physical 9DTact predictions with synchronized FT300 measurements."""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import rospy
from geometry_msgs.msg import WrenchStamped
from message_filters import ApproximateTimeSynchronizer, Subscriber


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from force_estimation.wrench import process_wrench, vector6  # noqa: E402


def message_wrench(message: WrenchStamped) -> np.ndarray:
    return vector6(
        [
            message.wrench.force.x,
            message.wrench.force.y,
            message.wrench.force.z,
            message.wrench.torque.x,
            message.wrench.torque.y,
            message.wrench.torque.z,
        ],
        "WrenchStamped",
    )


def fill_wrench(message: WrenchStamped, values: np.ndarray) -> None:
    message.wrench.force.x = float(values[0])
    message.wrench.force.y = float(values[1])
    message.wrench.force.z = float(values[2])
    message.wrench.torque.x = float(values[3])
    message.wrench.torque.y = float(values[4])
    message.wrench.torque.z = float(values[5])


class WrenchComparisonNode:
    def __init__(self) -> None:
        self.predicted_topic = str(
            rospy.get_param("~predicted_wrench_topic", "/predicted_wrench")
        )
        self.ft300_topic = str(
            rospy.get_param("~ft300_wrench_topic", "/robotiq_ft_wrench")
        )
        self.error_topic = str(rospy.get_param("~error_topic", "/wrench_error"))
        self.output_frame = str(
            rospy.get_param("~output_frame", "tactile_sensor")
        ).strip()
        self.expected_prediction_frame = str(
            rospy.get_param("~expected_prediction_frame", self.output_frame)
        ).strip()
        self.expected_ft300_frame = str(
            rospy.get_param("~expected_ft300_frame", "")
        ).strip()
        self.bias = rospy.get_param("~ft300_bias", [0.0] * 6)
        if rospy.has_param("~ft300_axis_signs"):
            self.axis_signs = rospy.get_param("~ft300_axis_signs")
        elif rospy.has_param("~axis_signs"):
            self.axis_signs = rospy.get_param("~axis_signs")
        else:
            raw_press_sign = int(rospy.get_param("~fz_raw_press_sign", 1))
            if raw_press_sign not in (-1, 1):
                raise ValueError("~fz_raw_press_sign must be 1 or -1")
            self.axis_signs = [1.0, 1.0, -float(raw_press_sign), 1.0, 1.0, 1.0]
        self.rotation = rospy.get_param(
            "~ft300_rotation",
            rospy.get_param(
                "~rotation", [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
            ),
        )
        self.translation = rospy.get_param(
            "~ft300_translation", rospy.get_param("~translation", [0.0, 0.0, 0.0])
        )
        self.max_age = float(rospy.get_param("~max_age", 0.5))
        queue_size = int(rospy.get_param("~queue_size", 50))
        sync_slop = float(rospy.get_param("~sync_slop", 0.02))
        if not self.output_frame or self.max_age <= 0 or queue_size < 1 or sync_slop <= 0:
            raise ValueError("Invalid comparison frame, age, queue, or synchronization setting")

        # Validate the configured transform before subscribing.
        process_wrench(
            np.zeros(6),
            bias=self.bias,
            axis_signs=self.axis_signs,
            rotation=self.rotation,
            translation=self.translation,
        )

        default_csv = (
            PROJECT_ROOT
            / ".runtime"
            / "ft300_comparison"
            / ("comparison_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S") + ".csv")
        )
        self.csv_path = Path(
            str(rospy.get_param("~csv_path", str(default_csv)))
        ).expanduser().resolve()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_handle = self.csv_path.open("w", encoding="utf-8", newline="")
        self.writer = csv.writer(self.csv_handle, lineterminator="\n")
        self.writer.writerow(
            [
                "predicted_stamp",
                "ft300_stamp",
                "frame",
                "pred_Fx_N",
                "pred_Fy_N",
                "pred_Fz_N",
                "pred_Tx_Nm",
                "pred_Ty_Nm",
                "pred_Tz_Nm",
                "ft_Fx_N",
                "ft_Fy_N",
                "ft_Fz_N",
                "ft_Tx_Nm",
                "ft_Ty_Nm",
                "ft_Tz_Nm",
                "error_Fx_N",
                "error_Fy_N",
                "error_Fz_N",
                "error_Tx_Nm",
                "error_Ty_Nm",
                "error_Tz_Nm",
            ]
        )
        self.error_pub = rospy.Publisher(self.error_topic, WrenchStamped, queue_size=10)
        predicted_sub = Subscriber(self.predicted_topic, WrenchStamped)
        ft300_sub = Subscriber(self.ft300_topic, WrenchStamped)
        self.synchronizer = ApproximateTimeSynchronizer(
            [predicted_sub, ft300_sub], queue_size=queue_size, slop=sync_slop
        )
        self.synchronizer.registerCallback(self.compare)
        rospy.on_shutdown(self.close)
        self.sample_count = 0

    def _validate_header(
        self, message: WrenchStamped, expected_frame: str, label: str
    ) -> None:
        if message.header.stamp == rospy.Time(0):
            raise ValueError("{} header stamp is zero".format(label))
        age = (rospy.Time.now() - message.header.stamp).to_sec()
        if age < -0.1 or age > self.max_age:
            raise ValueError("{} age is {:.3f} seconds".format(label, age))
        frame = str(message.header.frame_id or "").strip()
        if not frame:
            raise ValueError("{} frame_id is empty".format(label))
        if expected_frame and frame != expected_frame:
            raise ValueError(
                "{} frame '{}' does not match '{}'".format(label, frame, expected_frame)
            )

    def compare(self, predicted_message: WrenchStamped, ft300_message: WrenchStamped) -> None:
        try:
            self._validate_header(
                predicted_message, self.expected_prediction_frame, "prediction"
            )
            self._validate_header(ft300_message, self.expected_ft300_frame, "FT300")
            predicted = message_wrench(predicted_message)
            measured = process_wrench(
                message_wrench(ft300_message),
                bias=self.bias,
                axis_signs=self.axis_signs,
                rotation=self.rotation,
                translation=self.translation,
            )
        except ValueError as exc:
            rospy.logerr_throttle(1.0, "Rejected wrench comparison pair: %s", exc)
            return
        error = predicted - measured
        error_message = WrenchStamped()
        error_message.header.stamp = predicted_message.header.stamp
        error_message.header.frame_id = self.output_frame
        fill_wrench(error_message, error)
        self.error_pub.publish(error_message)
        self.writer.writerow(
            [
                "{:.9f}".format(predicted_message.header.stamp.to_sec()),
                "{:.9f}".format(ft300_message.header.stamp.to_sec()),
                self.output_frame,
            ]
            + ["{:.10g}".format(value) for value in predicted]
            + ["{:.10g}".format(value) for value in measured]
            + ["{:.10g}".format(value) for value in error]
        )
        self.csv_handle.flush()
        self.sample_count += 1
        rospy.loginfo_throttle(
            2.0,
            "Compared %d synchronized physical wrench pairs; CSV=%s",
            self.sample_count,
            self.csv_path,
        )

    def close(self) -> None:
        if not self.csv_handle.closed:
            self.csv_handle.flush()
            self.csv_handle.close()

    def run(self) -> None:
        rospy.logwarn(
            "Comparison logging does not establish FT300 calibration or prediction accuracy."
        )
        rospy.spin()


def main() -> None:
    rospy.init_node("compare_prediction_with_ft300")
    node = WrenchComparisonNode()
    node.run()


if __name__ == "__main__":
    main()
