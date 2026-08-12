#!/usr/bin/env python3
"""Collect synchronized 9DTact images and physical FT300 wrench labels in ROS 1."""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import rospy
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import WrenchStamped
from message_filters import ApproximateTimeSynchronizer, Subscriber
from sensor_msgs.msg import Image
from std_srvs.srv import SetBool, SetBoolResponse, Trigger, TriggerResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from force_estimation.wrench import (  # noqa: E402
    DEFAULT_WRENCH_MAX,
    DEFAULT_WRENCH_MIN,
    WrenchConfigurationError,
    normalized_distance,
    process_wrench,
    vector6,
)
from data_collection.representation import make_mixed_image  # noqa: E402


def utc_timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%fZ")


class FT300DataCollector:
    """Synchronize tactile images with an external FT300 WrenchStamped topic."""

    def __init__(self) -> None:
        rospy.init_node("nine_dtact_ft300_data_collector")

        self.sensor_id = int(rospy.get_param("~sensor_id", 1))
        if self.sensor_id not in (1, 2):
            raise ValueError("~sensor_id must be 1 or 2")

        self.image_topic = str(rospy.get_param("~image_topic", "/rectify_crop_image"))
        self.reference_image_topic = str(
            rospy.get_param("~reference_image_topic", "/rectify_crop_ref_image")
        )
        self.wrench_topic = str(rospy.get_param("~wrench_topic", "/robotiq_ft_wrench"))
        dataset_value = str(rospy.get_param("~dataset_root", "")).strip()
        if dataset_value:
            configured = Path(dataset_value).expanduser()
            self.dataset_root = (
                configured if configured.is_absolute() else PROJECT_ROOT / configured
            ).resolve()
        else:
            self.dataset_root = (PROJECT_ROOT / "Dataset_sensor_{}".format(self.sensor_id)).resolve()

        self.object_id = int(rospy.get_param("~object_id", 1))
        self.startup_timeout = float(rospy.get_param("~startup_timeout", 15.0))
        self.max_wrench_age = float(rospy.get_param("~max_wrench_age", 0.5))
        self.require_nonzero_stamp = bool(rospy.get_param("~require_nonzero_stamp", True))
        self.expected_wrench_frame = str(
            rospy.get_param("~expected_wrench_frame", "")
        ).strip()
        self.output_frame = str(
            rospy.get_param("~output_frame", "tactile_sensor")
        ).strip()
        if not self.output_frame:
            raise ValueError("~output_frame must not be empty")

        self.use_internal_zero = bool(rospy.get_param("~use_internal_zero", True))
        self.zero_samples = int(rospy.get_param("~zero_samples", 100))
        self.zero_std_max = vector6(
            rospy.get_param(
                "~zero_std_max", [0.05, 0.05, 0.05, 0.005, 0.005, 0.005]
            ),
            "~zero_std_max",
        )
        self.sync_slop = float(rospy.get_param("~sync_slop", 0.02))
        self.press_threshold = float(rospy.get_param("~press_threshold", -0.3))
        self.min_save_interval = float(rospy.get_param("~min_save_interval", 0.05))
        self.save_delta = float(rospy.get_param("~save_delta", 0.02))
        self.headless = bool(rospy.get_param("~headless", False))
        self.auto_start = bool(rospy.get_param("~auto_start", False))

        self.wrench_min = vector6(
            rospy.get_param("~wrench_min", DEFAULT_WRENCH_MIN.tolist()), "~wrench_min"
        )
        self.wrench_max = vector6(
            rospy.get_param("~wrench_max", DEFAULT_WRENCH_MAX.tolist()), "~wrench_max"
        )
        if np.any(self.wrench_max <= self.wrench_min):
            raise ValueError("Every ~wrench_max component must exceed ~wrench_min")

        fz_raw_press_sign = int(rospy.get_param("~fz_raw_press_sign", 1))
        if fz_raw_press_sign not in (-1, 1):
            raise ValueError("~fz_raw_press_sign must be 1 or -1")
        if rospy.has_param("~axis_signs"):
            self.axis_signs = vector6(rospy.get_param("~axis_signs"), "~axis_signs")
        else:
            self.axis_signs = np.ones(6, dtype=np.float64)
            self.axis_signs[2] = -float(fz_raw_press_sign)
        if not np.all(np.isin(self.axis_signs, (-1.0, 1.0))):
            raise ValueError("~axis_signs values must be -1 or 1")

        self.rotation = rospy.get_param(
            "~rotation", [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        )
        self.translation = rospy.get_param("~translation", [0.0, 0.0, 0.0])

        if self.object_id < 1 or self.zero_samples < 1:
            raise ValueError("~object_id and ~zero_samples must be greater than 0")
        for name, value in (
            ("~startup_timeout", self.startup_timeout),
            ("~max_wrench_age", self.max_wrench_age),
            ("~sync_slop", self.sync_slop),
            ("~min_save_interval", self.min_save_interval),
            ("~save_delta", self.save_delta),
        ):
            if not np.isfinite(value) or value <= 0:
                raise ValueError("{} must be finite and greater than 0".format(name))

        try:
            process_wrench(
                np.zeros(6),
                axis_signs=self.axis_signs,
                rotation=self.rotation,
                translation=self.translation,
            )
        except WrenchConfigurationError as exc:
            raise ValueError("Invalid FT300 transform configuration: {}".format(exc))

        self.bridge = CvBridge()
        self.lock = threading.RLock()
        self.recording = self.auto_start
        self.zeroing = False
        self.saved_total = 0
        self.last_saved_wrench: Optional[np.ndarray] = None
        self.last_save_time = rospy.Time(0)
        self.latest_image: Optional[np.ndarray] = None
        self.latest_wrench = np.zeros(6, dtype=np.float64)
        self.raw_zero = np.zeros(6, dtype=np.float64)
        self.last_wrench_frame = ""

        self._ensure_object_directories()
        self.next_index = self._next_index()
        self.reference_gray = self._load_reference_gray()
        if self.use_internal_zero:
            self.software_zero()
        else:
            rospy.logwarn(
                "Internal zeroing is disabled; the incoming FT300 topic must already be zeroed."
            )

        image_sub = Subscriber(self.image_topic, Image)
        wrench_sub = Subscriber(self.wrench_topic, WrenchStamped)
        self.synchronizer = ApproximateTimeSynchronizer(
            [image_sub, wrench_sub], queue_size=30, slop=self.sync_slop
        )
        self.synchronizer.registerCallback(self.synchronized_callback)

        self.recording_service = rospy.Service(
            "~set_recording", SetBool, self.set_recording_service
        )
        self.zero_service = rospy.Service("~zero", Trigger, self.zero_service_callback)
        self.next_object_service = rospy.Service(
            "~next_object", Trigger, self.next_object_service_callback
        )
        rospy.on_shutdown(cv2.destroyAllWindows)
        self._write_session_metadata()

        rospy.loginfo("Sensor %d FT300 collector started", self.sensor_id)
        rospy.loginfo("Dataset directory: %s", self.dataset_root)
        rospy.loginfo("Raw wrench topic: %s", self.wrench_topic)
        rospy.logwarn(
            "Software zeroing removes only the current offset; it does not replace "
            "proper FT300 installation, calibration, or frame verification."
        )

    @staticmethod
    def wrench_array(message: WrenchStamped) -> np.ndarray:
        wrench = message.wrench
        return vector6(
            [
                wrench.force.x,
                wrench.force.y,
                wrench.force.z,
                wrench.torque.x,
                wrench.torque.y,
                wrench.torque.z,
            ],
            "WrenchStamped",
        )

    def _validate_wrench_message(self, message: WrenchStamped) -> np.ndarray:
        values = self.wrench_array(message)
        stamp = message.header.stamp
        if self.require_nonzero_stamp and stamp == rospy.Time(0):
            raise ValueError("WrenchStamped header.stamp is zero")
        if stamp != rospy.Time(0):
            age = (rospy.Time.now() - stamp).to_sec()
            if age < -0.1 or age > self.max_wrench_age:
                raise ValueError("WrenchStamped age is {:.3f} seconds".format(age))
        frame = str(message.header.frame_id or "").strip()
        if self.expected_wrench_frame and frame != self.expected_wrench_frame:
            raise ValueError(
                "WrenchStamped frame '{}' does not match expected '{}'".format(
                    frame, self.expected_wrench_frame
                )
            )
        self.last_wrench_frame = frame
        return values

    def _wait_for_message(self, topic: str, message_type: Any) -> Any:
        try:
            return rospy.wait_for_message(topic, message_type, timeout=self.startup_timeout)
        except rospy.ROSException as exc:
            raise RuntimeError(
                "Timed out after {:.1f} seconds waiting for {}: {}".format(
                    self.startup_timeout, topic, exc
                )
            )

    def _load_reference_gray(self) -> np.ndarray:
        rospy.loginfo("Waiting for reference image: %s", self.reference_image_topic)
        message = self._wait_for_message(self.reference_image_topic, Image)
        try:
            image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
        except CvBridgeError as exc:
            raise RuntimeError("Reference-image conversion failed: {}".format(exc))
        if image is None or image.size == 0:
            raise RuntimeError("Reference image is empty")
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def software_zero(self) -> None:
        rospy.logwarn(
            "Keep the FT300 unloaded while %d fresh samples are collected for zeroing.",
            self.zero_samples,
        )
        with self.lock:
            if self.zeroing:
                raise RuntimeError("Software zeroing is already in progress")
            self.zeroing = True
        values: List[np.ndarray] = []
        try:
            maximum_attempts = max(self.zero_samples * 3, self.zero_samples + 10)
            for _ in range(maximum_attempts):
                message = self._wait_for_message(self.wrench_topic, WrenchStamped)
                try:
                    values.append(self._validate_wrench_message(message))
                except (ValueError, WrenchConfigurationError) as exc:
                    rospy.logwarn("Discarding invalid zero sample: %s", exc)
                    continue
                if len(values) >= self.zero_samples:
                    break
            if len(values) != self.zero_samples:
                raise RuntimeError(
                    "Collected only {} valid zero samples out of {} required".format(
                        len(values), self.zero_samples
                    )
                )
            sample_array = np.vstack(values)
            standard_deviation = np.std(sample_array, axis=0)
            if np.any(standard_deviation > self.zero_std_max):
                raise RuntimeError(
                    "FT300 was not stable during zeroing; std={} limit={}".format(
                        np.array2string(standard_deviation, precision=6),
                        np.array2string(self.zero_std_max, precision=6),
                    )
                )
            with self.lock:
                self.raw_zero = np.mean(sample_array, axis=0)
                self.last_saved_wrench = None
            rospy.loginfo(
                "Software zeroing complete: %s",
                np.array2string(self.raw_zero, precision=6),
            )
        finally:
            with self.lock:
                self.zeroing = False

    def processed_wrench(self, raw: np.ndarray) -> np.ndarray:
        return process_wrench(
            raw,
            bias=self.raw_zero,
            axis_signs=self.axis_signs,
            rotation=self.rotation,
            translation=self.translation,
        )

    def object_directories(self) -> Tuple[Path, Path, Path]:
        return (
            self.dataset_root / "image" / str(self.object_id),
            self.dataset_root / "mixed_image" / str(self.object_id),
            self.dataset_root / "wrench" / str(self.object_id),
        )

    def _ensure_object_directories(self) -> None:
        for directory in self.object_directories():
            directory.mkdir(parents=True, exist_ok=True)

    def _next_index(self) -> int:
        image_dir, _, _ = self.object_directories()
        indices = [
            int(path.stem)
            for path in image_dir.glob("*.png")
            if path.stem.isdigit()
        ]
        return max(indices, default=0) + 1

    def should_save(self, wrench: np.ndarray, stamp: rospy.Time) -> bool:
        if wrench[2] > self.press_threshold:
            return False
        if (stamp - self.last_save_time).to_sec() < self.min_save_interval:
            return False
        if self.last_saved_wrench is None:
            return True
        return (
            normalized_distance(
                wrench,
                self.last_saved_wrench,
                self.wrench_min,
                self.wrench_max,
            )
            >= self.save_delta
        )

    def synchronized_callback(
        self, image_message: Image, wrench_message: WrenchStamped
    ) -> None:
        with self.lock:
            if self.zeroing:
                return
        try:
            raw_wrench = self._validate_wrench_message(wrench_message)
            wrench = self.processed_wrench(raw_wrench)
            image = self.bridge.imgmsg_to_cv2(image_message, desired_encoding="bgr8")
        except (CvBridgeError, ValueError, WrenchConfigurationError) as exc:
            rospy.logerr_throttle(1.0, "Rejected synchronized sample: %s", exc)
            return
        if image is None or image.size == 0:
            rospy.logerr_throttle(1.0, "Rejected empty synchronized image")
            return
        stamp = image_message.header.stamp
        if stamp == rospy.Time(0):
            stamp = wrench_message.header.stamp
        if stamp == rospy.Time(0):
            stamp = rospy.Time.now()
        with self.lock:
            self.latest_image = image.copy()
            self.latest_wrench = wrench.copy()
            if self.recording and self.should_save(wrench, stamp):
                if self.save_sample(image, wrench):
                    self.last_saved_wrench = wrench.copy()
                    self.last_save_time = stamp

    def make_mixed_image(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if gray.shape != self.reference_gray.shape:
            raise ValueError(
                "Current image size {} does not match reference size {}".format(
                    gray.shape, self.reference_gray.shape
                )
            )
        return make_mixed_image(self.reference_gray, gray)

    @staticmethod
    def _temporary_path(final_path: Path, token: str) -> Path:
        return final_path.with_name(".{}.{}.tmp{}".format(final_path.stem, token, final_path.suffix))

    def _atomic_triplet(
        self,
        image_path: Path,
        image: np.ndarray,
        mixed_path: Path,
        mixed: np.ndarray,
        wrench_path: Path,
        wrench: np.ndarray,
    ) -> None:
        finals = (image_path, mixed_path, wrench_path)
        if any(path.exists() for path in finals):
            raise FileExistsError("Refusing to overwrite an existing sample triplet")
        token = uuid.uuid4().hex
        temporary = tuple(self._temporary_path(path, token) for path in finals)
        committed: List[Path] = []
        try:
            if not cv2.imwrite(str(temporary[0]), image):
                raise OSError("Failed to encode tactile image")
            if not cv2.imwrite(str(temporary[1]), mixed):
                raise OSError("Failed to encode mixed image")
            with temporary[2].open("wb") as handle:
                np.save(handle, wrench, allow_pickle=False)
                handle.flush()
                os.fsync(handle.fileno())
            for source, destination in zip(temporary, finals):
                os.replace(str(source), str(destination))
                committed.append(destination)
        except Exception:
            for path in temporary:
                if path.exists():
                    path.unlink()
            for path in committed:
                if path.exists():
                    path.unlink()
            raise

    def save_sample(self, image: np.ndarray, wrench: np.ndarray) -> bool:
        image_dir, mixed_dir, wrench_dir = self.object_directories()
        prefix = str(self.next_index)
        try:
            mixed = self.make_mixed_image(image)
            image_path = image_dir / (prefix + ".png")
            mixed_path = mixed_dir / (prefix + ".png")
            wrench_path = wrench_dir / (prefix + ".npy")
            self._atomic_triplet(
                image_path, image, mixed_path, mixed, wrench_path, wrench
            )
        except (OSError, ValueError, cv2.error) as exc:
            rospy.logerr("Atomic sample save failed: %s", exc)
            return False
        self.next_index += 1
        self.saved_total += 1
        rospy.loginfo("Saved Sensor %d sample: %s", self.sensor_id, image_path)
        return True

    def next_object(self) -> int:
        with self.lock:
            self.object_id += 1
            self._ensure_object_directories()
            self.next_index = self._next_index()
            self.last_saved_wrench = None
            object_id = self.object_id
        rospy.loginfo("Switched to object %d", object_id)
        return object_id

    def set_recording_service(self, request: Any) -> SetBoolResponse:
        with self.lock:
            self.recording = bool(request.data)
            self.last_saved_wrench = None
            state = self.recording
        return SetBoolResponse(success=True, message="recording={}".format(state))

    def zero_service_callback(self, _request: Any) -> TriggerResponse:
        with self.lock:
            was_recording = self.recording
            self.recording = False
        try:
            self.software_zero()
        except Exception as exc:
            return TriggerResponse(success=False, message=str(exc))
        finally:
            with self.lock:
                self.recording = was_recording
        return TriggerResponse(success=True, message="software zero complete")

    def next_object_service_callback(self, _request: Any) -> TriggerResponse:
        try:
            object_id = self.next_object()
        except Exception as exc:
            return TriggerResponse(success=False, message=str(exc))
        return TriggerResponse(success=True, message="object_id={}".format(object_id))

    def _write_session_metadata(self) -> None:
        directory = self.dataset_root / "acquisition_sessions"
        directory.mkdir(parents=True, exist_ok=True)
        metadata: Dict[str, Any] = {
            "schema_version": 1,
            "created_utc": utc_timestamp(),
            "sensor_id": self.sensor_id,
            "dataset_root": str(self.dataset_root),
            "image_topic": self.image_topic,
            "reference_image_topic": self.reference_image_topic,
            "wrench_topic": self.wrench_topic,
            "input_frame": self.last_wrench_frame,
            "expected_wrench_frame": self.expected_wrench_frame,
            "output_frame": self.output_frame,
            "units": {"force": "N", "torque": "N*m"},
            "use_internal_zero": self.use_internal_zero,
            "zero_samples": self.zero_samples,
            "raw_zero": self.raw_zero.tolist(),
            "zero_std_max": self.zero_std_max.tolist(),
            "axis_signs": self.axis_signs.tolist(),
            "rotation_row_major": list(self.rotation),
            "translation_m": list(self.translation),
            "wrench_min": self.wrench_min.tolist(),
            "wrench_max": self.wrench_max.tolist(),
            "press_threshold_fz_n": self.press_threshold,
            "save_delta_normalized": self.save_delta,
            "hardware_validation_claimed": False,
        }
        target = directory / ("session_" + utc_timestamp() + ".json")
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(str(temporary), str(target))

    def display_frame(self) -> np.ndarray:
        with self.lock:
            image = (
                self.latest_image.copy()
                if self.latest_image is not None
                else np.zeros((480, 640, 3), dtype=np.uint8)
            )
            wrench = self.latest_wrench.copy()
            recording = self.recording
            object_id = self.object_id
            saved_total = self.saved_total
        lines = [
            "Sensor ID: {}  Object: {}".format(self.sensor_id, object_id),
            "Saved: {}  Recording: {}".format(
                saved_total, "YES" if recording else "NO"
            ),
            "Fx {: .3f}  Fy {: .3f}  Fz {: .3f}".format(*wrench[:3]),
            "Tx {: .4f}  Ty {: .4f}  Tz {: .4f}".format(*wrench[3:]),
            "SPACE record/pause | n next | z zero | q quit",
        ]
        for index, line in enumerate(lines):
            cv2.putText(
                image,
                line,
                (12, 28 + 28 * index),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (0, 255, 0) if recording else (0, 220, 255),
                2,
                cv2.LINE_AA,
            )
        return image

    def run(self) -> None:
        if self.headless:
            rospy.loginfo(
                "Headless mode active; use private services set_recording, zero, and next_object."
            )
            rospy.spin()
            return
        rate = rospy.Rate(30)
        while not rospy.is_shutdown():
            cv2.imshow("9DTact FT300 Data Collection", self.display_frame())
            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):
                with self.lock:
                    self.recording = not self.recording
                    self.last_saved_wrench = None
                    state = self.recording
                rospy.loginfo("Recording state: %s", "started" if state else "paused")
            elif key == ord("n"):
                self.next_object()
            elif key == ord("z"):
                response = self.zero_service_callback(None)
                if not response.success:
                    rospy.logerr("Software zero failed: %s", response.message)
            elif key == ord("q"):
                rospy.signal_shutdown("User requested shutdown")
                break
            rate.sleep()


def main() -> None:
    collector = FT300DataCollector()
    collector.run()


if __name__ == "__main__":
    main()
