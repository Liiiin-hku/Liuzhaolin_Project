# 9DTact + FT300 Custom Tactile Sensor Project

[Chinese README](README_CN.md) | [Version and validation status](VERSION_INFO.md)

This repository is the graduation-project delivery for two custom optical tactile
sensors derived from the 9DTact workflow. It brings together camera calibration,
3D surface reconstruction, synchronized FT300 data acquisition, dataset preparation,
six-axis force-model training, standalone tactile inference, and ROS 1 integration.

The repository is organized for a beginner to complete one sensor at a time. Sensor 1
and Sensor 2 keep separate calibration, dataset, configuration, and model paths. The
active sensor is selected explicitly before calibration, acquisition, reconstruction,
training, or inference.

> **Validation boundary:** repository structure and static checks can be verified on
> Windows. Camera mapping, depth response, FT300 acquisition, ROS nodes, trained-model
> accuracy, and combined hardware behavior still require Ubuntu 20.04 tests with the
> physical devices. No Windows result is presented as a hardware pass.

## Project scope

| Stage | Included implementation | Current evidence |
|---|---|---|
| Sensor selection | Isolated Sensor 1 and Sensor 2 templates and activation tool | Static file/configuration checks |
| Camera calibration | Automatic calibration plus a reviewed 7 x 9 manual-point workflow | Active arrays exist for both sensors; Sensor 2 has manual-point provenance |
| Depth-to-shape conversion | Active hybrid official depth LUT experiment | File integrity verified; physical accuracy remains unverified |
| Shape reconstruction | Standalone OpenCV/Open3D workflow and ROS wrapper | Requires Ubuntu camera test |
| FT300 acquisition | Synchronized tactile image and `WrenchStamped` label collection | Requires an external FT300 ROS driver and hardware test |
| Dataset processing | Integrity checks, normalization, and two object-disjoint split modes | Offline tools included |
| Force training | ResNet18 smoke-test path and DenseNet169 full-training path | Training code included; datasets and trained weights are excluded |
| Force inference | Standalone and ROS six-axis inference | Requires a sensor-specific checkpoint and Ubuntu test |
| ROS integration | Catkin package and six launch workflows | Static XML/Python checks only |

## Important calibration facts

- Each sensor resolves `row_index.npy`, `col_index.npy`, and `position_scale.npy`
  through a sensor-specific active path. The current three core arrays are
  byte-identical between those paths; they are not evidence of independently derived
  camera mappings.
- Both active sensors currently use the same official upstream depth lookup table:
  `Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`.
- The shared LUT SHA-256 is
  `19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`.
- This is an **experimental hybrid calibration**, not an independently measured,
  precise depth calibration of either custom sensor.
- Running `shape_reconstruction/_2_Sensor_Calibration.py` trains and replaces the
  active sensor's LUT. Doing so intentionally leaves the hybrid-LUT state. Back up
  the current LUT first; if the hybrid state is restored, rerun
  `python tools/verify_hybrid_calibration.py`.
- The latest Ubuntu archive records `camera_channel: 2` and a reconstruction crop of
  `[280, 380]` for both sensors. `/dev/videoX` numbering is host-dependent and must be
  checked on every Ubuntu computer. Force-model `img_size` is aligned to `[280, 380]`.

## Supported baseline

- Ubuntu 20.04 LTS
- Python 3.8
- ROS Noetic (ROS 1)
- OpenCV, NumPy, SciPy, Open3D, and PyYAML from the pinned core requirements
- PyTorch 2.0.1 and torchvision 0.15.2 for training and inference
- An external FT300 ROS driver that publishes `geometry_msgs/WrenchStamped`

The repository does not bundle an FT300 hardware driver and does not claim that a
particular vendor driver officially supports ROS Noetic. Confirm the driver and robot
controller combination in the target laboratory. The raw wrench topic is configurable;
the example default is `/robotiq_ft_wrench`.

## Beginner quick start

### 1. Install the core Ubuntu environment

```bash
cd <LOCAL_PROJECT_ROOT>
bash scripts/install_core_ubuntu20.sh
source custom_9dtact/.venv/bin/activate
python scripts/verify_installation.py --profile core
```

For ROS or training dependencies, continue with
[Ubuntu 20.04 installation](docs/01_INSTALLATION_UBUNTU20.md). Do not copy a virtual
environment from another computer.

### 2. Select and check one sensor

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
```

Use `--sensor-id 2` for Sensor 2. Activation copies the selected templates into the
active `shape_config.yaml` and `force_config.yaml` files and stores local runtime state
under `.runtime/`.

### 3. Confirm the camera device on Ubuntu

```bash
v4l2-ctl --list-devices
ls -l /dev/video*
```

If the correct device is not channel 2 on that host, edit the selected persistent
template in `custom_9dtact/configs/`, then activate the sensor again. Do not edit only
the generated active configuration.

### 4. Validate or rebuild camera calibration

Automatic workflow:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/shape_reconstruction
python _1_Camera_Calibration.py
```

Manual 7 x 9 workflow, with new reference/sample capture:

```bash
python manual_camera_calibration_v2.py --capture
```

Click 63 grid points in row-major order. Press `A` to toggle snapping, use right-click
or `U` to undo, press Enter to preview, and press lowercase `s` to save. The tool makes
a timestamped internal backup before replacing active camera arrays. See
[Camera calibration](docs/03_CAMERA_CALIBRATION.md) before applying new outputs.

### 5. Check the active hybrid depth LUT

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/verify_hybrid_calibration.py
```

The check proves file identity and array validity only. It does not prove the physical
depth response of either custom sensor.

### 6. Run standalone 3D shape reconstruction

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
cd shape_reconstruction
python _3_Shape_Reconstruction.py
```

Repeat in a fresh terminal with Sensor 2 selected. Record the no-contact surface,
light press, medium press, release recovery, and contact-location response separately.

### 7. Acquire FT300-labelled data

FT300 measurements are ground-truth labels for data collection, training, and
validation. Start the ROS master, camera/image publisher, and external FT300 driver
before starting the collector. Validate the wrench topic first:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_ft300_topic.py --topic /robotiq_ft_wrench
```

Then follow [FT300 setup](docs/06_FT300_SETUP.md) and
[data collection](docs/07_DATA_COLLECTION.md). Stop recording before stopping the
collector, then stop the camera and FT300 driver, and stop `roscore` last.

### 8. Prepare, train, and evaluate

Keep the two sensor datasets separate. Validate a dataset before training:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_dataset_integrity.py \
  --dataset-root Dataset_sensor_1 \
  --require-normalized \
  --check-splits
```

Run a short ResNet18 pipeline test before a long DenseNet169 run. Trained tactile
inference uses camera images and the selected neural-network checkpoint; FT300 is not
required during normal inference. FT300 remains necessary when collecting new labels
or comparing predictions against physical ground truth.

### 9. Run in ROS

The catkin package is located at
`custom_9dtact/ros_ws/src/9dtact_ft300_ros`. Its six launch entry points are:

- `sensor1_shape.launch`
- `sensor2_shape.launch`
- `ft300_collection.launch`
- `force_estimation.launch`
- `shape_force_demo.launch`
- `compare_prediction_with_ft300.launch`

Build, source, and use the launch file that matches the intended stage. Review the
actual launch-file arguments before starting hardware. See
[ROS workflow](docs/11_ROS_WORKFLOW.md).

## Documentation map

1. [Project overview](docs/00_PROJECT_OVERVIEW.md)
2. [Ubuntu 20.04 installation](docs/01_INSTALLATION_UBUNTU20.md)
3. [Sensor configuration](docs/02_SENSOR_CONFIGURATION.md)
4. [Camera calibration](docs/03_CAMERA_CALIBRATION.md)
5. [Sensor/depth calibration](docs/04_SENSOR_CALIBRATION.md)
6. [Shape reconstruction](docs/05_SHAPE_RECONSTRUCTION.md)
7. [FT300 setup](docs/06_FT300_SETUP.md)
8. [Data collection](docs/07_DATA_COLLECTION.md)
9. [Data processing](docs/08_DATA_PROCESSING.md)
10. [Model training](docs/09_MODEL_TRAINING.md)
11. [Force estimation](docs/10_FORCE_ESTIMATION.md)
12. [ROS workflow](docs/11_ROS_WORKFLOW.md)
13. [Troubleshooting](docs/12_TROUBLESHOOTING.md)
14. [Project tree](docs/13_PROJECT_TREE.md)
15. [Hybrid depth-LUT experiment record](docs/ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md)

## Repository protection and excluded artifacts

- Treat `Original/` as a byte-preserved, read-only upstream snapshot.
- Work in `custom_9dtact/` and repository-level documentation only.
- Datasets, trained weights, local runtime state, caches, logs, temporary outputs,
  and generated training bundles are intentionally excluded from Git.
- Do not exchange calibration files, datasets, or model paths between Sensor 1 and
  Sensor 2.
- Back up active calibration and data before every hardware experiment.

## Citation and license

The custom work is distributed under the repository [LICENSE](LICENSE). Upstream
attribution and third-party notices are recorded in [NOTICE.md](NOTICE.md). When this
project is used in academic work, cite the upstream 9DTact project and the relevant
hardware/software sources described there.
