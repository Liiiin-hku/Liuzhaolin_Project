# 02 - Sensor Configuration

[Previous: Installation](01_INSTALLATION_UBUNTU20.md) | [Home](../README.md) | [Next: Camera calibration](03_CAMERA_CALIBRATION.md)

## Configuration model

Each sensor has two persistent templates:

```text
custom_9dtact/configs/
|-- shape_sensor_1.yaml
|-- shape_sensor_2.yaml
|-- force_sensor_1.yaml
`-- force_sensor_2.yaml
```

Activation copies one sensor's templates to these generated active files:

```text
custom_9dtact/shape_reconstruction/shape_config.yaml
custom_9dtact/force_estimation/force_config.yaml
```

Edit the persistent template, not only the active copy. Re-activate after every
template change so both active files and the `.runtime/active_sensor.txt` marker agree.

## 1. Identify the camera on this host

Connect only the intended tactile camera while mapping devices:

```bash
v4l2-ctl --list-devices
ls -l /dev/video*
```

If necessary, inspect formats without starting the project:

```bash
v4l2-ctl --device=/dev/video2 --list-formats-ext
```

The latest Ubuntu archive records `camera_channel: 2` for both sensors. This is a
historical host mapping, not a permanent camera identity. USB order, capture cards,
and reconnects can change `/dev/videoX` numbering.

Update the selected template if needed:

```yaml
camera_setting:
  camera_channel: 2
  resolution:
    - 640
    - 480
  fps: 30
```

Record how the physical device was identified. A stable udev rule can be used by an
experienced system administrator, but the numeric channel in this project must still
match the OpenCV device opened on that host.

## 2. Confirm geometry alignment

Both selected shape templates use:

```yaml
camera_calibration:
  crop_size:
    - 280
    - 380
```

The corresponding force templates must use:

```yaml
img_size:
  - 280
  - 380
```

The order is height, then width. The submission verifier rejects a mismatch between
`crop_size` and `img_size`.

## 3. Activate one sensor

Sensor 1:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
```

Sensor 2:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 2
python tools/check_sensor_setup.py --sensor-id 2
```

The activation tool backs up previous active configuration files under
`.runtime/config_backups/` and retains a bounded local history. `.runtime/` is not a
version-controlled source of truth.

Use the stricter data check before training:

```bash
python tools/check_sensor_setup.py --sensor-id 1 --require-data
```

## 4. Keep sensor resources isolated

Sensor 1 must use:

- `shape_reconstruction/calibration/sensor_1/`
- `Dataset_sensor_1/`
- `saved_models_sensor_1/`

Sensor 2 must use:

- `shape_reconstruction/calibration/sensor_2/`
- `Dataset_sensor_2/`
- `saved_models_sensor_2/`

Do not copy one sensor's camera arrays into the other sensor directory. Do not point a
force template at the other sensor's dataset or model directory. If a result appears
only after such a cross-copy, treat it as a configuration error rather than evidence.

## 5. Pre-run checklist

Before opening the camera or running ROS, confirm:

- the physical sensor ID is recorded;
- the matching templates are active;
- the current camera channel is verified on this Ubuntu host;
- crop size and force-model image size are both `280 x 380`;
- calibration paths point to the selected sensor;
- dataset and model paths point to the selected sensor;
- no second sensor process is still running;
- any calibration or data to be modified has an external backup.

Proceed to camera calibration only after this checklist passes.
