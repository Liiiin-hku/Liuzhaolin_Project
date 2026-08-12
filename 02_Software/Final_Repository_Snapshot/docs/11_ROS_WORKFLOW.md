# 11 - ROS Noetic Workflow

[Previous: Force estimation](10_FORCE_ESTIMATION.md) | [Home](../README.md) | [Next: Troubleshooting](12_TROUBLESHOOTING.md)

## Package identity

Catkin source directory:

`custom_9dtact/ros_ws/src/9dtact_ft300_ros`

Declared ROS package name used by `roslaunch` and `rospack`:

`nine_dtact_ft300_ros`

The different directory and package spellings are intentional. Use the declared package
name in commands.

## Build and source

```bash
source /opt/ros/noetic/setup.bash
source <LOCAL_PROJECT_ROOT>/custom_9dtact/.venv/bin/activate
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/ros_ws
catkin_make
source devel/setup.bash
rospack find nine_dtact_ft300_ros
```

Run the first three `source` commands in every new terminal. If the package runner
cannot locate the repository, set `NINE_DTACT_PROJECT_ROOT` to the absolute
`<LOCAL_PROJECT_ROOT>/custom_9dtact` path in that terminal.

## General startup order

1. Connect only the intended tactile camera and verify `/dev/videoX`.
2. Activate and statically check the selected sensor from `custom_9dtact/`.
3. Start `roscore` in Terminal 1.
4. If the workflow needs FT300, start the external FT300 driver in Terminal 2.
5. Validate the FT300 topic before acquisition or comparison.
6. Start one project launch file in a sourced terminal.
7. Check node, topic, type, frame, rate, and timestamp before applying contact.
8. Stop in the reverse order described at the end of this document.

The launch files accept repository-relative configuration paths. A camera override of
`-1` uses the channel in the shape configuration; a non-negative value temporarily
overrides it for that launch.

## Six launch workflows

### 1. Sensor 1 shape reconstruction

```bash
roslaunch nine_dtact_ft300_ros sensor1_shape.launch
```

Optional arguments include `shape_config`, `camera_channel`, `image_topic`, and
`reference_image_topic`.

### 2. Sensor 2 shape reconstruction

```bash
roslaunch nine_dtact_ft300_ros sensor2_shape.launch
```

This launch defaults to `configs/shape_sensor_2.yaml`. Stop the Sensor 1 launch before
starting it.

### 3. FT300-labelled acquisition

Start and validate the external driver first. Sensor 1 example:

```bash
roslaunch nine_dtact_ft300_ros ft300_collection.launch \
  sensor_id:=1 \
  shape_config:=configs/shape_sensor_1.yaml \
  wrench_topic:=/robotiq_ft_wrench \
  dataset_root:=Dataset_sensor_1 \
  object_id:=1
```

For Sensor 2, change `sensor_id`, `shape_config`, and `dataset_root` together. Other
declared arguments include `camera_channel`, image/reference topics, `headless`, and
`auto_start`.

### 4. Tactile force inference

Requires a configured checkpoint:

```bash
roslaunch nine_dtact_ft300_ros force_estimation.launch \
  shape_config:=configs/shape_sensor_1.yaml \
  force_config:=configs/force_sensor_1.yaml
```

Declared arguments include camera channel, `start_sensor`, representation topic,
physical predicted-wrench topic, and normalized predicted-wrench topic.

### 5. Combined shape and force display

Requires a configured checkpoint:

```bash
roslaunch nine_dtact_ft300_ros shape_force_demo.launch \
  shape_config:=configs/shape_sensor_1.yaml \
  force_config:=configs/force_sensor_1.yaml
```

The demo publishes the tactile representation to the force estimator and combines the
normalized prediction with the shape view. Use the physical predicted-wrench topic for
quantitative evaluation.

### 6. Prediction versus FT300 comparison

Start and validate the external FT300 driver first, and configure a trained checkpoint:

```bash
roslaunch nine_dtact_ft300_ros compare_prediction_with_ft300.launch \
  shape_config:=configs/shape_sensor_1.yaml \
  force_config:=configs/force_sensor_1.yaml \
  ft300_wrench_topic:=/robotiq_ft_wrench
```

The comparison synchronizes physical predicted and FT300 wrench messages, applies the
configured FT300 transform, publishes `/wrench_error`, and writes a CSV under local
`.runtime/ft300_comparison/` unless `csv_path` is supplied. Review
`config/ft300.yaml` before using its signs, rotation, translation, thresholds, or ranges.

## Topic checklist

Typical project topics include:

| Topic | Type | Role |
|---|---|---|
| `/rectify_crop_image` | `sensor_msgs/Image` | Rectified tactile image |
| `/rectify_crop_ref_image` | `sensor_msgs/Image` | Reference image |
| `/deformation_representation` | `sensor_msgs/Image` | Network input representation |
| `/robotiq_ft_wrench` | `geometry_msgs/WrenchStamped` | External FT300 input example |
| `/predicted_wrench` | `geometry_msgs/WrenchStamped` | Physical tactile prediction |
| `/predicted_wrench_normalized` | `std_msgs/Float64MultiArray` | Normalized network output |
| `/wrench_error` | `geometry_msgs/WrenchStamped` | Prediction-minus-reference error |

Check resolved names after launch:

```bash
rosnode list
rostopic list
rostopic info /predicted_wrench
rostopic hz /predicted_wrench
```

## Shutdown order

1. Pause acquisition if it is recording.
2. Stop the project launch with Ctrl+C and wait for node shutdown.
3. Stop the external FT300 driver.
4. Stop any separate tactile publisher.
5. Stop `roscore` last.
6. Verify written datasets or comparison CSVs and copy them to backup storage.
7. Confirm the camera device is released before starting another sensor.

Never run the Sensor 1 and Sensor 2 camera launch workflows simultaneously when the
project is configured for one active camera.
