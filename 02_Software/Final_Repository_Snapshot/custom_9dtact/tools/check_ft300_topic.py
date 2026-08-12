#!/usr/bin/env python3
"""Check an external FT300 WrenchStamped topic without collecting a dataset."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from force_estimation.wrench import vector6  # noqa: E402


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="/robotiq_ft_wrench")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-age", type=float, default=0.5)
    parser.add_argument("--expected-frame", default="")
    parser.add_argument("--min-rate", type=float, default=10.0)
    args = parser.parse_args(argv)
    if args.samples < 2:
        parser.error("--samples must be at least 2")
    if args.timeout <= 0 or args.max_age <= 0 or args.min_rate <= 0:
        parser.error("timeout, max-age, and min-rate must be greater than 0")
    return args


def main() -> int:
    try:
        import rospy
        from geometry_msgs.msg import WrenchStamped
    except ImportError as exc:
        print("ROS 1 Python dependencies are missing: {}".format(exc), file=sys.stderr)
        return 2

    args = parse_args(rospy.myargv(argv=sys.argv)[1:])
    try:
        rospy.init_node("check_ft300_topic", anonymous=True)
    except Exception as exc:
        print(
            "ROS node initialization failed; verify ROS_MASTER_URI and roscore: {}".format(
                exc
            ),
            file=sys.stderr,
        )
        return 2
    try:
        resolved_topic = rospy.resolve_name(args.topic)
        published_topics = dict(rospy.get_published_topics(namespace="/"))
    except Exception as exc:
        print(
            "ROS master query failed; verify roscore and network connectivity: {}".format(
                exc
            ),
            file=sys.stderr,
        )
        return 2
    advertised_type = published_topics.get(resolved_topic)
    if advertised_type is None:
        print(
            "Requested FT300 topic is not advertised: {}".format(resolved_topic),
            file=sys.stderr,
        )
        return 1
    expected_type = "geometry_msgs/WrenchStamped"
    if advertised_type != expected_type:
        print(
            "FT300 topic {} advertises {}, expected {}".format(
                resolved_topic, advertised_type, expected_type
            ),
            file=sys.stderr,
        )
        return 1
    values = []
    stamps = []
    frames = set()
    started = time.monotonic()
    for index in range(args.samples):
        remaining = args.timeout - (time.monotonic() - started)
        if remaining <= 0:
            print("Timed out after receiving {} samples".format(index), file=sys.stderr)
            return 1
        try:
            message = rospy.wait_for_message(
                resolved_topic, WrenchStamped, timeout=remaining
            )
        except Exception as exc:
            print("FT300 topic wait failed: {}".format(exc), file=sys.stderr)
            return 1
        try:
            wrench = vector6(
                [
                    message.wrench.force.x,
                    message.wrench.force.y,
                    message.wrench.force.z,
                    message.wrench.torque.x,
                    message.wrench.torque.y,
                    message.wrench.torque.z,
                ]
            )
        except ValueError as exc:
            print("Invalid wrench sample: {}".format(exc), file=sys.stderr)
            return 1
        if message.header.stamp == rospy.Time(0):
            print("WrenchStamped header.stamp is zero", file=sys.stderr)
            return 1
        age = (rospy.Time.now() - message.header.stamp).to_sec()
        if age < -0.1 or age > args.max_age:
            print("Stale wrench sample age: {:.6f} seconds".format(age), file=sys.stderr)
            return 1
        frame = str(message.header.frame_id or "").strip()
        if not frame:
            print("WrenchStamped header.frame_id is empty", file=sys.stderr)
            return 1
        if args.expected_frame and frame != args.expected_frame:
            print(
                "Frame '{}' does not match expected '{}'".format(
                    frame, args.expected_frame
                ),
                file=sys.stderr,
            )
            return 1
        values.append(wrench)
        stamps.append(message.header.stamp.to_sec())
        frames.add(frame)

    stamp_span = max(stamps) - min(stamps)
    rate = (len(stamps) - 1) / stamp_span if stamp_span > 0 else 0.0
    if len(frames) != 1:
        print("Multiple FT300 frames observed: {}".format(sorted(frames)), file=sys.stderr)
        return 1
    if rate < args.min_rate:
        print(
            "Observed rate {:.3f} Hz is below {:.3f} Hz".format(rate, args.min_rate),
            file=sys.stderr,
        )
        return 1
    array = np.vstack(values)
    print("FT300 topic static/runtime check: PASSED")
    print("Topic: {}".format(resolved_topic))
    print("Message type: geometry_msgs/WrenchStamped")
    print("Frame: {}".format(next(iter(frames))))
    print("Samples: {}".format(len(values)))
    print("Observed header rate: {:.3f} Hz".format(rate))
    print("Mean [Fx,Fy,Fz,Tx,Ty,Tz]: {}".format(np.mean(array, axis=0)))
    print("Std  [Fx,Fy,Fz,Tx,Ty,Tz]: {}".format(np.std(array, axis=0)))
    print("This check does not establish FT300 calibration accuracy or mounting correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
