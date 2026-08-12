# 07 - FT300-Labelled Data Collection

[Previous: FT300 setup](06_FT300_SETUP.md) | [Home](../README.md) | [Next: Data processing](08_DATA_PROCESSING.md)

## Output contract

The collector synchronizes a rectified tactile image with an external FT300
`WrenchStamped` sample using ROS message timestamps. For each object ID it writes a
matched triplet:

```text
Dataset_sensor_X/
|-- image/<OBJECT_ID>/<INDEX>.png
|-- mixed_image/<OBJECT_ID>/<INDEX>.png
|-- wrench/<OBJECT_ID>/<INDEX>.npy
`-- acquisition_sessions/<SESSION>.json
```

The raw wrench array has six finite physical values in the configured tactile frame.
Files with a common object ID and index form one sample. Do not rename one member of a
triplet independently.

## Before each session

- back up the existing `Dataset_sensor_X/` directory;
- activate the correct sensor and pass its setup check;
- validate standalone shape/camera output;
- confirm `crop_size` and force `img_size` are both `280 x 380`;
- verify the external FT300 topic, timestamp, frame, sample rate, zero, and signs;
- review dataset root, object ID, wrench ranges, transform, synchronization tolerance,
  and save thresholds in the launch file;
- place the system in a safe, unloaded state.

## Startup order

1. Start `roscore`.
2. Start the tactile sensor/image publisher.
3. Start the external FT300 driver.
4. Run `tools/check_ft300_topic.py` and correct any message error.
5. Start the FT300 collector with `ft300_collection.launch`.
6. Verify the displayed sensor ID, object ID, wrench, and saved-sample count.
7. Zero only while unloaded.
8. Start recording and apply the planned contacts.

Build and source the workspace first:

```bash
source /opt/ros/noetic/setup.bash
source <LOCAL_PROJECT_ROOT>/custom_9dtact/.venv/bin/activate
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/ros_ws
catkin_make
source devel/setup.bash
```

Start the collector with the declared arguments. Sensor 1 example:

```bash
roslaunch nine_dtact_ft300_ros ft300_collection.launch \
  sensor_id:=1 \
  shape_config:=configs/shape_sensor_1.yaml \
  wrench_topic:=/robotiq_ft_wrench \
  dataset_root:=Dataset_sensor_1 \
  object_id:=1
```

Open `src/9dtact_ft300_ros/launch/ft300_collection.launch` and review every `<arg>`
declaration before changing the example. For Sensor 2, change the sensor ID, shape
configuration, and dataset root together.

## Interactive collector controls

| Key | Action |
|---|---|
| Space | Start or pause recording |
| `n` | Move to the next object ID |
| `z` | Compute a software zero while unloaded |
| `q` | Stop the collector |

In headless mode, use the collector's private `set_recording`, `zero`, and `next_object`
services instead of keyboard controls. Discover the resolved service names with
`rosservice list` after launch.

## Collection design

Use object IDs as experimental groups. Include representative contact locations,
directions, and load levels without exceeding the configured safe range. Avoid long
runs that contain only adjacent frames from one nearly static press.

For every session, preserve:

- sensor and object identity;
- configuration and calibration hashes;
- camera device/channel and capture settings;
- FT300 topic, frame, rate, transform, sign, zero statistics, and wrench ranges;
- synchronization and save thresholds;
- operator, date, host, environmental notes, and anomalies.

## Stop and inspect

1. Press Space to pause.
2. Wait for the saved count to stop changing.
3. Press `q` to stop the collector.
4. Stop image and FT300 publishers, then `roscore`.
5. Back up the dataset before processing.
6. Run an integrity check:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_dataset_integrity.py \
  --dataset-root Dataset_sensor_1
```

Inspect several matched image/wrench triplets manually. Confirm that all images are
readable, shape is `280 x 380`, labels are finite six-vectors, and session metadata
matches the intended sensor and transform.

Do not collect Sensor 2 into `Dataset_sensor_1` or continue an object ID under a
different physical object. Correct dataset provenance is part of the experiment, not a
later formatting task.
