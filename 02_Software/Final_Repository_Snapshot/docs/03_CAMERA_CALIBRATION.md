# 03 - Camera Calibration

[Previous: Sensor configuration](02_SENSOR_CONFIGURATION.md) | [Home](../README.md) | [Next: Sensor calibration](04_SENSOR_CALIBRATION.md)

## Purpose and outputs

Camera calibration maps each raw `480 x 640` image to the sensor surface and defines
the physical crop. The active output directory for the selected sensor contains:

- `row_index.npy`, shape `(480, 640)`;
- `col_index.npy`, shape `(480, 640)`;
- `position_scale.npy`, shape `(3,)`;
- reference/sample images and optional manual-point provenance artifacts.

These files are sensor-specific. Never exchange them between Sensor 1 and Sensor 2.

## Provenance status in this delivery

- Sensor 2 includes manual-point provenance artifacts for its manual camera mapping.
- Sensor 1 active camera arrays are present, but independent source artifacts that
  reproduce their manual point selection are not present.

This distinction must remain visible in reports. An array passing shape and finiteness
checks does not by itself establish its point-selection history or physical quality.

## 1. Prepare the sensor

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
v4l2-ctl --list-devices
```

Use Sensor 2 commands for the second device. Confirm the camera channel, focus,
lighting, grid target, and that no other process owns the camera.

Back up the selected sensor's entire active `camera_calibration/` directory outside the
repository before replacing outputs.

## 2. Automatic workflow

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/shape_reconstruction
python _1_Camera_Calibration.py
```

Follow the program's image-capture and target-detection prompts. Review the produced
rectification and crop before accepting it. Automatic completion is not evidence of a
correct mapping if point detection is wrong.

## 3. Manual 7 x 9 workflow

The reviewed manual tool is:

`custom_9dtact/shape_reconstruction/manual_camera_calibration_v2.py`

Run it from the `shape_reconstruction` directory. To capture new averaged `ref.png`
and `sample.png` images before point selection:

```bash
python manual_camera_calibration_v2.py --capture
```

To use the existing images:

```bash
python manual_camera_calibration_v2.py
```

To resume an incomplete point-selection checkpoint:

```bash
python manual_camera_calibration_v2.py --resume
```

To start with local automatic snapping disabled:

```bash
python manual_camera_calibration_v2.py --no-snap
```

Optional capture and snapping controls are `--average-frames` and `--snap-radius`.
Use `python manual_camera_calibration_v2.py --help` for their current defaults.

### Point-selection order and controls

Click exactly 63 points in row-major order:

1. first row, left to right, 9 points;
2. second row, left to right, 9 points;
3. continue through the seventh row.

Controls:

| Input | Action |
|---|---|
| Left-click | Add the next point |
| Right-click or `U` | Undo the latest point |
| `R` | Clear all selected points |
| `A` | Toggle local snapping |
| Enter | Validate point order and open the preview |
| `B` in preview | Return to point selection |
| Lowercase `s` in preview | Save active outputs |
| `Q` or Escape | Exit without saving final outputs |

There is no implicit apply operation. The active arrays are replaced only when
lowercase `s` is pressed in the preview. Immediately before writing, the tool creates
a timestamped `manual_backup_YYYYMMDD_HHMMSS/` directory inside the active camera
calibration directory.

## 4. Preview and quality control

Before pressing lowercase `s`, inspect both preview windows:

- all horizontal and vertical grid lines are ordered and do not cross;
- the rectified crop contains the full useful contact area;
- border behavior does not fold or repeat image regions;
- the crop orientation matches the physical sensor orientation;
- the grid center and millimetres-per-pixel value are plausible;
- no obvious point is on the wrong dot or row;
- the reported outside-boundary mapping ratio is acceptable for the intended crop.

If any check fails, press `B`, undo points, and correct the map. Do not save merely
because the script generated an array.

## 5. Verify saved outputs

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_sensor_setup.py --sensor-id 1
python tools/verify_hybrid_calibration.py
```

The second command also loads the camera arrays and checks their required shapes. Then
run the physical shape test described in
[Shape reconstruction](05_SHAPE_RECONSTRUCTION.md). Keep preview images, point files,
sensor ID, date, camera channel, and operator notes with the experiment record.

## Rollback

Stop all programs using the camera. Restore all three arrays from the same timestamped
backup for the same sensor, then rerun the static checks and physical preview. Never
restore only one of the three arrays and never use the other sensor's backup.
