#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
9DTact 手动 7×9 Camera Calibration（V2，Python 3.8 兼容）

放置位置：
    custom_9dtact/shape_reconstruction/manual_camera_calibration_v2.py

常用命令：
    # 使用现有 ref.png 和 sample.png
    python manual_camera_calibration_v2.py

    # 重新拍摄 ref.png 和 sample.png
    python manual_camera_calibration_v2.py --capture

    # 恢复上一次未完成的点击
    python manual_camera_calibration_v2.py --resume

鼠标与键盘：
    左键：添加点
    右键 / U：撤销上一个点
    R：清空全部点
    A：开关局部自动吸附
    Enter：点满 63 个后进入预览
    预览阶段 S：确认并保存
    预览阶段 B：返回修改点
    Q / Esc：退出

点击顺序：
    从最上面一行开始，每行从左到右点击 9 个点；
    然后第二行从左到右，直到第七行，共 63 个点。
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import yaml
from scipy.interpolate import Rbf


Point = Tuple[int, int]  # (x, y)
ROWS = 7
COLS = 9
POINT_COUNT = ROWS * COLS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="9DTact 手动 7x9 Camera Calibration V2"
    )
    parser.add_argument(
        "--config",
        default="shape_config.yaml",
        help="活动配置文件，默认当前目录的 shape_config.yaml",
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="重新采集 ref.png 和 sample.png",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="恢复上一次未完成的点击点",
    )
    parser.add_argument(
        "--no-snap",
        action="store_true",
        help="启动时关闭局部自动吸附",
    )
    parser.add_argument(
        "--snap-radius",
        type=int,
        default=14,
        help="自动吸附搜索半径，默认 14 像素",
    )
    parser.add_argument(
        "--average-frames",
        type=int,
        default=15,
        help="重新拍摄时的平均帧数，默认 15",
    )
    return parser.parse_args()


def load_config(path: Path) -> Dict:
    if not path.is_file():
        raise SystemExit(
            "找不到 %s。\n"
            "请先进入 custom_9dtact/shape_reconstruction 再运行。"
            % path
        )

    try:
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SystemExit("读取配置失败：%s" % exc)

    rows = int(cfg["camera_calibration"]["row_points"])
    cols = int(cfg["camera_calibration"]["col_points"])
    if (rows, cols) != (ROWS, COLS):
        raise SystemExit(
            "本脚本要求 7×9 点阵，当前配置是 %d×%d。" % (rows, cols)
        )

    return cfg


def calibration_dir_from_config(cfg: Dict, cwd: Path) -> Path:
    sensor_id = int(cfg["sensor_id"])
    root = Path(str(cfg["calibration_root_dir"]))
    if not root.is_absolute():
        root = (cwd / root).resolve()

    subdir = str(
        cfg["camera_calibration"]["camera_calibration_dir"]
    ).lstrip("/\\")

    return root / ("sensor_%d" % sensor_id) / subdir


def open_camera(cfg: Dict) -> cv2.VideoCapture:
    camera_cfg = cfg["camera_setting"]
    channel = int(camera_cfg["camera_channel"])
    width = int(camera_cfg["resolution"][0])
    height = int(camera_cfg["resolution"][1])
    fps = float(camera_cfg["fps"])

    cap = cv2.VideoCapture(channel, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError("无法打开 /dev/video%d。" % channel)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = float(cap.get(cv2.CAP_PROP_FPS))

    print(
        "相机：/dev/video%d，实际视频流：%d×%d，%.2f FPS"
        % (channel, actual_width, actual_height, actual_fps)
    )

    if actual_width != width or actual_height != height:
        cap.release()
        raise RuntimeError(
            "实际分辨率 %d×%d 与配置 %d×%d 不一致。"
            % (actual_width, actual_height, width, height)
        )

    return cap


def capture_average(
    cap: cv2.VideoCapture,
    window_name: str,
    instruction: str,
    average_frames: int,
) -> np.ndarray:
    print(instruction)
    print("在图像窗口按 y 采集；按 q 退出。")

    last_frame: Optional[np.ndarray] = None

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("相机读取失败或 USB 断开。")

        last_frame = frame
        display = frame.copy()
        cv2.rectangle(display, (0, 0), (display.shape[1], 32), (0, 0, 0), -1)
        cv2.putText(
            display,
            "Press Y to capture; Q to quit",
            (8, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.imshow(window_name, display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            raise SystemExit("用户退出。")
        if key == ord("y"):
            break

    time.sleep(0.25)
    accumulator = np.zeros_like(last_frame, dtype=np.float64)
    collected = 0

    for _ in range(max(1, int(average_frames))):
        ok, frame = cap.read()
        if ok and frame is not None:
            accumulator += frame.astype(np.float64)
            collected += 1

    cv2.destroyWindow(window_name)

    if collected == 0:
        raise RuntimeError("没有采集到有效平均图像。")

    return np.clip(accumulator / collected, 0, 255).astype(np.uint8)


def capture_images(
    cfg: Dict,
    output_dir: Path,
    average_frames: int,
) -> Tuple[np.ndarray, np.ndarray]:
    cap = open_camera(cfg)

    try:
        ref = capture_average(
            cap,
            "Reference",
            "保持胶面完全无接触，稳定后按 y。",
            average_frames,
        )
        cv2.imwrite(str(output_dir / "ref.png"), ref)
        print("已保存：", output_dir / "ref.png")

        sample = capture_average(
            cap,
            "Calibration Board",
            "将 7×9 标定板均匀压在胶面中央；63 点都可见后按 y。",
            average_frames,
        )
        cv2.imwrite(str(output_dir / "sample.png"), sample)
        print("已保存：", output_dir / "sample.png")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return ref, sample


def load_images(output_dir: Path) -> Tuple[np.ndarray, np.ndarray]:
    ref = cv2.imread(str(output_dir / "ref.png"), cv2.IMREAD_COLOR)
    sample = cv2.imread(str(output_dir / "sample.png"), cv2.IMREAD_COLOR)

    if ref is None or sample is None:
        raise SystemExit(
            "找不到 ref.png 或 sample.png。\n"
            "请运行：python manual_camera_calibration_v2.py --capture"
        )

    if ref.shape != sample.shape:
        raise SystemExit("ref.png 和 sample.png 尺寸不一致。")

    return ref, sample


def make_snap_image(ref: np.ndarray, sample: np.ndarray) -> np.ndarray:
    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    sample_gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(ref_gray, sample_gray)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(diff)


def snap_point(
    click_x: int,
    click_y: int,
    snap_image: np.ndarray,
    radius: int,
) -> Point:
    height, width = snap_image.shape[:2]

    x0 = max(0, click_x - radius)
    x1 = min(width, click_x + radius + 1)
    y0 = max(0, click_y - radius)
    y1 = min(height, click_y + radius + 1)

    patch = snap_image[y0:y1, x0:x1].astype(np.float64)
    if patch.size == 0 or float(patch.max()) < 5.0:
        return int(click_x), int(click_y)

    maximum = float(patch.max())
    threshold = max(5.0, maximum * 0.55)
    weights = np.clip(patch - threshold, 0.0, None)

    if float(weights.sum()) <= 1e-9:
        local_y, local_x = np.unravel_index(
            int(np.argmax(patch)),
            patch.shape,
        )
        return int(x0 + local_x), int(y0 + local_y)

    grid_y, grid_x = np.indices(weights.shape)
    x = x0 + float((grid_x * weights).sum() / weights.sum())
    y = y0 + float((grid_y * weights).sum() / weights.sum())

    return int(round(x)), int(round(y))


def save_checkpoint(output_dir: Path, points: Sequence[Point]) -> None:
    np.save(
        output_dir / "manual_points_checkpoint.npy",
        np.asarray(points, dtype=np.float64),
    )


def load_resume_points(output_dir: Path) -> List[Point]:
    for name in ("manual_points_checkpoint.npy", "manual_points.npy"):
        path = output_dir / name
        if not path.is_file():
            continue

        try:
            array = np.load(str(path))
        except Exception as exc:
            print("无法读取 %s：%s" % (path, exc))
            continue

        if array.ndim != 2 or array.shape[1] != 2:
            continue

        result: List[Point] = []
        for x, y in array[:POINT_COUNT]:
            result.append((int(round(float(x))), int(round(float(y)))))

        print("已从 %s 恢复 %d 个点。" % (path, len(result)))
        return result

    print("没有找到可恢复点，从 0 开始。")
    return []


def draw_click_canvas(
    sample: np.ndarray,
    points: Sequence[Point],
    snap_enabled: bool,
) -> np.ndarray:
    height, width = sample.shape[:2]
    canvas = np.zeros((height + 42, width, 3), dtype=np.uint8)
    canvas[:height] = sample

    # 横向连线。
    for row in range(ROWS):
        start = row * COLS
        end = min(start + COLS, len(points))
        for index in range(start, max(start, end - 1)):
            if index + 1 < len(points):
                cv2.line(
                    canvas,
                    points[index],
                    points[index + 1],
                    (255, 0, 0),
                    1,
                )

    # 纵向连线。
    for index in range(len(points)):
        if index >= COLS:
            cv2.line(
                canvas,
                points[index - COLS],
                points[index],
                (0, 255, 255),
                1,
            )

    for index, (x, y) in enumerate(points, start=1):
        cv2.circle(canvas, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(
            canvas,
            str(index),
            (x + 5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.36,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    status_y = height
    cv2.rectangle(
        canvas,
        (0, status_y),
        (width, height + 42),
        (0, 0, 0),
        -1,
    )
    text = (
        "%d/63 | Left:add Right/U:undo R:reset A:snap(%s) Enter:preview Q:quit"
        % (len(points), "ON" if snap_enabled else "OFF")
    )
    cv2.putText(
        canvas,
        text,
        (7, height + 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    return canvas


def make_magnifier(
    sample: np.ndarray,
    cursor: Optional[Point],
    next_index: int,
) -> np.ndarray:
    source_size = 31
    scale = 6
    output_size = source_size * scale

    if cursor is None:
        image = np.zeros((output_size, output_size, 3), dtype=np.uint8)
        cv2.putText(
            image,
            "Move mouse",
            (25, output_size // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        return image

    x, y = cursor
    half = source_size // 2
    height, width = sample.shape[:2]

    x0 = max(0, x - half)
    x1 = min(width, x + half + 1)
    y0 = max(0, y - half)
    y1 = min(height, y + half + 1)

    crop = sample[y0:y1, x0:x1]
    top = max(0, half - y)
    bottom = max(0, y + half + 1 - height)
    left = max(0, half - x)
    right = max(0, x + half + 1 - width)

    crop = cv2.copyMakeBorder(
        crop,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )
    crop = cv2.resize(
        crop,
        (output_size, output_size),
        interpolation=cv2.INTER_NEAREST,
    )

    center = output_size // 2
    cv2.line(crop, (center, 0), (center, output_size - 1), (0, 255, 255), 1)
    cv2.line(crop, (0, center), (output_size - 1, center), (0, 255, 255), 1)
    cv2.putText(
        crop,
        "Next: %d" % next_index,
        (5, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )

    return crop


def validate_points(
    points: Sequence[Point],
    image_shape: Tuple[int, int],
    crop_height: int,
    crop_width: int,
) -> Tuple[bool, List[str], Dict[str, float]]:
    errors: List[str] = []

    if len(points) != POINT_COUNT:
        return False, ["必须正好点击 63 个点。"], {}

    array = np.asarray(points, dtype=np.float64).reshape(ROWS, COLS, 2)

    for row in range(ROWS):
        if np.any(np.diff(array[row, :, 0]) <= 0):
            errors.append("第 %d 行没有严格从左到右点击。" % (row + 1))

    row_mean_y = array[:, :, 1].mean(axis=1)
    if np.any(np.diff(row_mean_y) <= 0):
        errors.append("7 行没有严格按从上到下的顺序点击。")

    horizontal: List[float] = []
    vertical: List[float] = []

    for row in range(ROWS):
        for col in range(COLS - 1):
            horizontal.append(
                float(np.linalg.norm(array[row, col + 1] - array[row, col]))
            )

    for row in range(ROWS - 1):
        for col in range(COLS):
            vertical.append(
                float(np.linalg.norm(array[row + 1, col] - array[row, col]))
            )

    horizontal_np = np.asarray(horizontal)
    vertical_np = np.asarray(vertical)

    if float(horizontal_np.min()) < 3.0:
        errors.append("存在横向重复点击或距离过近的点。")
    if float(vertical_np.min()) < 3.0:
        errors.append("存在纵向重复点击或距离过近的点。")

    center_x, center_y = array[3, 4]
    height, width = image_shape

    if center_x - crop_width / 2 < 0 or center_x + crop_width / 2 > width:
        errors.append("中心点导致横向裁剪超出图像，请重新居中。")
    if center_y - crop_height / 2 < 0 or center_y + crop_height / 2 > height:
        errors.append("中心点导致纵向裁剪超出图像，请重新居中。")

    stats = {
        "horizontal_median_px": float(np.median(horizontal_np)),
        "vertical_median_px": float(np.median(vertical_np)),
        "horizontal_cv": float(
            np.std(horizontal_np) / max(np.mean(horizontal_np), 1e-9)
        ),
        "vertical_cv": float(
            np.std(vertical_np) / max(np.mean(vertical_np), 1e-9)
        ),
        "center_x": float(center_x),
        "center_y": float(center_y),
    }

    return len(errors) == 0, errors, stats


def generate_maps(
    points_xy: Sequence[Point],
    image_shape: Tuple[int, int],
    grid_distance_mm: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    points = np.asarray(points_xy, dtype=np.float64)
    all_point = np.column_stack([points[:, 1], points[:, 0]])  # [row, col]

    center_index = POINT_COUNT // 2
    distance_average = 0.0
    for offset in (-COLS, -1, 1, COLS):
        distance_average += float(
            np.linalg.norm(
                all_point[center_index]
                - all_point[center_index + offset]
            )
        )
    distance_average /= 4.0

    if not np.isfinite(distance_average) or distance_average <= 0:
        raise RuntimeError("中心相邻点距离计算失败。")

    # 与原项目兼容：第三项实际为 mm / pixel。
    mm_per_pixel = float(grid_distance_mm / distance_average)
    position_scale = np.asarray(
        [
            all_point[center_index, 0],
            all_point[center_index, 1],
            mm_per_pixel,
        ],
        dtype=np.float64,
    )

    ideal = np.zeros_like(all_point, dtype=np.float64)
    for row in range(ROWS):
        for col in range(COLS):
            index = row * COLS + col
            ideal[index] = (
                all_point[center_index]
                + distance_average
                * np.asarray([row - 3, col - 4], dtype=np.float64)
            )

    interp_row = Rbf(
        ideal[:, 0], ideal[:, 1], all_point[:, 0], function="cubic"
    )
    interp_col = Rbf(
        ideal[:, 0], ideal[:, 1], all_point[:, 1], function="cubic"
    )

    height, width = image_shape
    col_mesh, row_mesh = np.meshgrid(np.arange(width), np.arange(height))

    row_index = interp_row(row_mesh, col_mesh).astype(np.int32)
    col_index = interp_col(row_mesh, col_mesh).astype(np.int32)

    invalid = (
        (row_index < 0)
        | (row_index >= height)
        | (col_index < 0)
        | (col_index >= width)
    )
    invalid_ratio = float(np.mean(invalid))

    row_index[invalid] = 0
    col_index[invalid] = 0

    return row_index, col_index, position_scale, invalid_ratio


def draw_grid(sample: np.ndarray, points: Sequence[Point]) -> np.ndarray:
    drawing = sample.copy()

    for row in range(ROWS):
        for col in range(COLS - 1):
            index = row * COLS + col
            cv2.line(drawing, points[index], points[index + 1], (0, 0, 0), 2)

    for col in range(COLS):
        for row in range(ROWS - 1):
            first = row * COLS + col
            second = (row + 1) * COLS + col
            cv2.line(drawing, points[first], points[second], (0, 0, 0), 2)

    special_indexes = {22, 30, 31, 32, 40}
    for index, point in enumerate(points):
        special = index in special_indexes
        cv2.circle(
            drawing,
            point,
            9 if special else 5,
            (255, 0, 0) if special else (0, 0, 0),
            -1,
        )

    return drawing


def crop_image(
    image: np.ndarray,
    position_scale: np.ndarray,
    crop_height: int,
    crop_width: int,
) -> np.ndarray:
    center_y = int(round(float(position_scale[0])))
    center_x = int(round(float(position_scale[1])))

    y0 = center_y - crop_height // 2
    x0 = center_x - crop_width // 2
    return image[y0:y0 + crop_height, x0:x0 + crop_width]


def add_preview_label(image: np.ndarray, label: str) -> np.ndarray:
    output = image.copy()
    cv2.rectangle(output, (0, 0), (output.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(
        output,
        label,
        (8, 23),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return output


def backup_old_outputs(output_dir: Path) -> Optional[Path]:
    protected = {"ref.png", "sample.png"}
    old_files = [
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.name not in protected
    ]

    if not old_files:
        return None

    backup_dir = output_dir / (
        "manual_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    backup_dir.mkdir(parents=True, exist_ok=True)

    for path in old_files:
        shutil.move(str(path), str(backup_dir / path.name))

    return backup_dir


def save_outputs(
    cfg: Dict,
    output_dir: Path,
    ref: np.ndarray,
    sample: np.ndarray,
    points: Sequence[Point],
    row_index: np.ndarray,
    col_index: np.ndarray,
    position_scale: np.ndarray,
    invalid_ratio: float,
    stats: Dict[str, float],
) -> None:
    backup_dir = backup_old_outputs(output_dir)
    if backup_dir is not None:
        print("旧标定输出已备份到：", backup_dir)

    np.save(output_dir / "row_index.npy", row_index)
    np.save(output_dir / "col_index.npy", col_index)
    np.save(output_dir / "position_scale.npy", position_scale)
    np.save(
        output_dir / "manual_points.npy",
        np.asarray(points, dtype=np.float64),
    )

    with (output_dir / "manual_points.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["index", "row", "col", "x", "y"])
        for index, (x, y) in enumerate(points, start=1):
            writer.writerow(
                [index, (index - 1) // COLS + 1, (index - 1) % COLS + 1, x, y]
            )

    sample_drawing = draw_grid(sample, points)
    sample_new = sample[row_index, col_index]
    sample_drawing_new = sample_drawing[row_index, col_index]

    crop_height = int(cfg["camera_calibration"]["crop_size"][0])
    crop_width = int(cfg["camera_calibration"]["crop_size"][1])

    sample_new_crop = crop_image(
        sample_new, position_scale, crop_height, crop_width
    )
    sample_drawing_new_crop = crop_image(
        sample_drawing_new, position_scale, crop_height, crop_width
    )

    cv2.imwrite(
        str(output_dir / "ref_GRAY.png"),
        cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY),
    )
    cv2.imwrite(
        str(output_dir / "sample_GRAY.png"),
        cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY),
    )
    cv2.imwrite(str(output_dir / "sample_drawing.png"), sample_drawing)
    cv2.imwrite(str(output_dir / "sample_new.png"), sample_new)
    cv2.imwrite(str(output_dir / "sample_new_crop.png"), sample_new_crop)
    cv2.imwrite(
        str(output_dir / "sample_drawing_new.png"),
        sample_drawing_new,
    )
    cv2.imwrite(
        str(output_dir / "sample_drawing_new_crop.png"),
        sample_drawing_new_crop,
    )
    cv2.imwrite(
        str(output_dir / "sample_drawing_manual.png"),
        sample_drawing,
    )
    cv2.imwrite(
        str(output_dir / "sample_drawing_new_crop_manual.png"),
        sample_drawing_new_crop,
    )

    report = {
        "method": "manual_7x9_rbf_v2",
        "sensor_id": int(cfg["sensor_id"]),
        "camera_channel": int(cfg["camera_setting"]["camera_channel"]),
        "image_width": int(sample.shape[1]),
        "image_height": int(sample.shape[0]),
        "grid_rows": ROWS,
        "grid_cols": COLS,
        "grid_distance_mm": float(
            cfg["camera_calibration"]["grid_distance"]
        ),
        "center_row": float(position_scale[0]),
        "center_col": float(position_scale[1]),
        "mm_per_pixel": float(position_scale[2]),
        "invalid_map_ratio": float(invalid_ratio),
        "statistics": stats,
    }
    (output_dir / "manual_calibration_report.yaml").write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    checkpoint = output_dir / "manual_points_checkpoint.npy"
    if checkpoint.exists():
        checkpoint.unlink()


def main() -> None:
    args = parse_args()
    cwd = Path.cwd()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = cwd / config_path

    cfg = load_config(config_path)
    output_dir = calibration_dir_from_config(cfg, cwd)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.capture:
        ref, sample = capture_images(
            cfg, output_dir, args.average_frames
        )
    else:
        ref, sample = load_images(output_dir)

    snap_image = make_snap_image(ref, sample)
    cv2.imwrite(
        str(output_dir / "manual_snap_difference.png"),
        snap_image,
    )

    points = load_resume_points(output_dir) if args.resume else []
    state = {
        "cursor": None,
        "snap_enabled": not args.no_snap,
    }
    snap_radius = max(2, int(args.snap_radius))

    sample_height, sample_width = sample.shape[:2]
    main_window = "Manual 7x9 Calibration V2"
    zoom_window = "Magnifier"

    cv2.namedWindow(main_window, cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow(zoom_window, cv2.WINDOW_AUTOSIZE)

    def mouse_callback(
        event: int,
        x: int,
        y: int,
        flags: int,
        userdata: object,
    ) -> None:
        del flags, userdata

        if y < sample_height:
            state["cursor"] = (int(x), int(y))

        if event == cv2.EVENT_LBUTTONDOWN:
            if y >= sample_height:
                return
            if len(points) >= POINT_COUNT:
                print("已有 63 个点，请按 Enter 预览。")
                return

            selected = (
                snap_point(int(x), int(y), snap_image, snap_radius)
                if state["snap_enabled"]
                else (int(x), int(y))
            )
            points.append(selected)
            save_checkpoint(output_dir, points)

            index = len(points)
            print(
                "点 %d/63（第 %d 行，第 %d 列）：%s"
                % (
                    index,
                    (index - 1) // COLS + 1,
                    (index - 1) % COLS + 1,
                    selected,
                )
            )

        elif event == cv2.EVENT_RBUTTONDOWN and points:
            removed = points.pop()
            save_checkpoint(output_dir, points)
            print("已撤销：", removed)

    cv2.setMouseCallback(main_window, mouse_callback)

    print("")
    print("按顺序点击：第一行从左到右 9 点，然后第二行，直到第七行。")
    print("左键添加；右键/U 撤销；R 清空；A 开关吸附；Enter 预览；Q 退出。")
    print("吸附开启时，只需点击圆点中心附近。")

    crop_height = int(cfg["camera_calibration"]["crop_size"][0])
    crop_width = int(cfg["camera_calibration"]["crop_size"][1])

    while True:
        while True:
            canvas = draw_click_canvas(
                sample, points, bool(state["snap_enabled"])
            )
            magnifier = make_magnifier(
                sample,
                state["cursor"],
                min(len(points) + 1, POINT_COUNT),
            )
            cv2.imshow(main_window, canvas)
            cv2.imshow(zoom_window, magnifier)

            key = cv2.waitKey(20) & 0xFF

            if key in (ord("q"), 27):
                cv2.destroyAllWindows()
                raise SystemExit("退出；最终标定结果未保存。")

            if key == ord("u") and points:
                removed = points.pop()
                save_checkpoint(output_dir, points)
                print("已撤销：", removed)

            elif key == ord("r"):
                points.clear()
                save_checkpoint(output_dir, points)
                print("已清空全部点。")

            elif key == ord("a"):
                state["snap_enabled"] = not state["snap_enabled"]
                print(
                    "自动吸附：%s"
                    % ("开启" if state["snap_enabled"] else "关闭")
                )

            elif key in (10, 13):
                valid, errors, stats = validate_points(
                    points,
                    sample.shape[:2],
                    crop_height,
                    crop_width,
                )
                if not valid:
                    print("不能进入预览：")
                    for error in errors:
                        print("  -", error)
                    continue
                break

        print("点击顺序检查通过，正在计算 RBF 映射……")

        row_index, col_index, position_scale, invalid_ratio = generate_maps(
            points,
            sample.shape[:2],
            float(cfg["camera_calibration"]["grid_distance"]),
        )

        raw_grid = draw_grid(sample, points)
        rectified_grid = raw_grid[row_index, col_index]
        rectified_grid_crop = crop_image(
            rectified_grid,
            position_scale,
            crop_height,
            crop_width,
        )

        raw_preview = add_preview_label(
            raw_grid, "RAW GRID | S:save B:back Q:quit"
        )
        rectified_preview = add_preview_label(
            rectified_grid_crop,
            "RECTIFIED CROP | S:save B:back Q:quit",
        )

        raw_window = "Preview Raw Grid"
        rectified_window = "Preview Rectified Crop"
        cv2.namedWindow(raw_window, cv2.WINDOW_AUTOSIZE)
        cv2.namedWindow(rectified_window, cv2.WINDOW_AUTOSIZE)

        print("")
        print(
            "中心：[row=%.2f, col=%.2f]，mm/pixel=%.8f"
            % (
                position_scale[0],
                position_scale[1],
                position_scale[2],
            )
        )
        print("映射边界外像素比例：%.2f%%" % (invalid_ratio * 100.0))
        print("检查无交叉乱线、裁剪完整。按 S 保存；B 返回；Q 退出。")

        action = ""
        while not action:
            cv2.imshow(raw_window, raw_preview)
            cv2.imshow(rectified_window, rectified_preview)
            key = cv2.waitKey(20) & 0xFF

            if key == ord("s"):
                action = "save"
            elif key == ord("b"):
                action = "back"
            elif key in (ord("q"), 27):
                action = "quit"

        cv2.destroyWindow(raw_window)
        cv2.destroyWindow(rectified_window)

        if action == "back":
            print("已返回点击界面，可用 U 或右键撤销。")
            continue

        if action == "quit":
            cv2.destroyAllWindows()
            raise SystemExit("退出；最终标定结果未保存。")

        save_outputs(
            cfg,
            output_dir,
            ref,
            sample,
            points,
            row_index,
            col_index,
            position_scale,
            invalid_ratio,
            stats,
        )
        cv2.destroyAllWindows()

        print("")
        print("手动 Camera Calibration 已成功完成。")
        print("输出目录：", output_dir)
        print("已生成：row_index.npy、col_index.npy、position_scale.npy")
        print("下一步回到 custom_9dtact 根目录运行：")
        print(
            "python tools/check_sensor_setup.py --sensor-id %d"
            % int(cfg["sensor_id"])
        )
        break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        print("\n用户中断。")
        sys.exit(130)
