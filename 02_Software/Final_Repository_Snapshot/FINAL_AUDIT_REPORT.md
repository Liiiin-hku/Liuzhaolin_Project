# Final Static Audit Report

## Release identity

- Project: **9DTact + FT300 Custom Sensor Project**
- Release branch: `submission/final-sensor-code`
- Protected Git baseline: `0b8d18ac47ef4eb7bf116efac63c2eee5e83aded` from `experiment/7.25-original-depth-lut`
- Ubuntu source archive used for hardware-facing settings: `7.25修改.zip`
- Review date: 2026-08-11
- Intended platform: Ubuntu 20.04, Python 3.8, and ROS Noetic

The interrupted local work was preserved outside the repository before this branch was created. Its complete status, working and cached diffs, untracked-file list, copied untracked files, and a local-only WIP commit are retained in `<EXTERNAL_WIP_BACKUP>`. That backup is not part of this submission.

## Scope completed

This release provides the repository structure and documented workflow for:

1. dependency installation and static environment verification;
2. independent Sensor 1 and Sensor 2 configuration selection;
3. camera calibration, including the Ubuntu-exported `manual_camera_calibration_v2.py` workflow;
4. sensor/depth calibration and 3D Shape Reconstruction;
5. Robotiq FT300 six-axis ground-truth acquisition through a configurable `geometry_msgs/WrenchStamped` topic;
6. synchronized tactile-image and FT300 collection;
7. object-disjoint dataset splitting, normalization, and integrity checks;
8. ResNet18 smoke training and DenseNet169 full training entry points;
9. normalized prediction and physical wrench prediction in N and N*m;
10. a ROS Noetic catkin package with sensor, shape, acquisition, force, combined-demo, and comparison launches.

The trained tactile model produces its prediction from a 9DTact image. The FT300 is used for labels during acquisition and as optional ground truth during comparison; it is not an inference dependency.

## Hardware configuration source and reconciliation

The latest Ubuntu export was used as the highest-priority source for active hardware-facing configuration. Both sensor templates retain:

- `camera_channel: 2`;
- image resolution `640 x 480`;
- camera crop `[280, 380]`.

The exported force templates still contained the earlier `[345, 460]` image size. The final force templates were reconciled to `[280, 380]`, so each sensor's Shape Reconstruction crop and force-training input size now agree. `/dev/videoX` numbering is host-specific and must be checked with `v4l2-ctl` before every hardware session.

## Calibration state and limitations

For both sensors, the active camera arrays passed the required shape checks:

| File | Shape | SHA-256 |
| --- | --- | --- |
| `row_index.npy` | `(480, 640)` | `f54090298f15e1e706256368d4b3e4308eecae751d241664b082fd61abf8c9aa` |
| `col_index.npy` | `(480, 640)` | `f3f22ccf78d15431d178ac6fabb66b44c5a390b3354fb8f485f2533f05737982` |
| `position_scale.npy` | `(3,)` | `15c95bf85f6da828832e20ee64da0d195427f11f96918b1795b6a3288326c118` |

The three core camera arrays are byte-identical between Sensor 1 and Sensor 2. Sensor 2 includes manual-point provenance; the supplied Ubuntu material does not contain an independent Sensor 1 point set or report and identifies its calibration as reused. This release preserves that evidence and does not claim independent camera-calibration provenance for Sensor 1.

The Ubuntu-exported `manual_camera_calibration_v2.py` was preserved byte-for-byte with SHA-256 `0511f4688f6cc5b9e9d721596af9660d736dbc4c6d1e73869ab5df7d861bcf75`. It supports capture or loaded images, 63 row-major points, snapping, undo, preview, save, and regeneration of the three camera arrays.

The experimental hybrid depth configuration remains active:

- official source: `Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`;
- source shape: `(61,)`;
- source range: `-0.9467841221106313` to `1.9151455666508503`;
- source and both target SHA-256 values: `19c9f3514dce402d8e710079757394b5445b74e7afbdd2459de43798676cb4ff`.

Each sensor retains its active camera-calibration directory while sharing this upstream depth LUT. This is an engineering experiment, not evidence of an independent and accurate depth calibration for either custom sensor.

## FT300 and legacy isolation

The supported collector is `custom_9dtact/data_collection/collect_data_ft300.py`. It accepts a parameterized external `WrenchStamped` topic, performs finite/freshness/frame checks, software zeroing, configurable axis signs and wrench transformation, approximate image/wrench synchronization, and atomic sensor-specific sample writes.

The upstream BOTA/Rokubi Mini collector was moved out of the active workflow to `custom_9dtact/legacy/bota/collect_data_bota_legacy.py`. A scan of operational code found zero active references to `rokubimini_msgs`, BOTA, MiniONE, `/bus0/ft_sensor0`, or `ft_sensor0`. The immutable `Original/` snapshot and the explicit legacy archive are excluded from that operational scan.

## ROS package

The catkin package is stored at `custom_9dtact/ros_ws/src/9dtact_ft300_ros` and declares the package name `nine_dtact_ft300_ros`. It contains exactly these six release launch files:

- `sensor1_shape.launch`
- `sensor2_shape.launch`
- `ft300_collection.launch`
- `force_estimation.launch`
- `shape_force_demo.launch`
- `compare_prediction_with_ft300.launch`

An external laboratory FT300 driver must first publish `geometry_msgs/WrenchStamped`; its topic is supplied as a launch argument. Physical predictions use `/predicted_wrench` with N and N*m, while optional normalized values use `/predicted_wrench_normalized` and are never labelled as physical units.

## Static verification evidence

The following checks passed on Windows without accessing hardware:

- 30/30 offline unit and source-contract tests;
- Python 3.8 grammar parsing: 85 Python files;
- `compileall`: exit code 0;
- YAML parsing: 9 files;
- ROS package/launch XML parsing: 7 files;
- installation verifier in static-only mode;
- hybrid calibration verifier for both sensors;
- Sensor 1 and Sensor 2 activation/setup static checks;
- sensor-specific configuration isolation;
- Shape Reconstruction crop and force-model image-size agreement at `[280, 380]`;
- six required camera-calibration NumPy shapes;
- both active depth LUT hashes equal the selected official source;
- active BOTA/Rokubi dependency scan: zero hits;
- local user-path scan: zero hits;
- protected `Original/` manifest: 138/138 files identical in path, size, and SHA-256;
- calibration NumPy files are not ignored by Git;
- no dataset, model, runtime, cache, log, or temporary artifact is tracked for delivery;
- `git diff --check` passed.

`SUBMISSION_MANIFEST.csv` records the relative path, byte size, and SHA-256 of every delivered file except the manifest itself, which is excluded to avoid a recursive self-hash.

## Tests deliberately not claimed

Windows static verification does not establish real hardware behavior. This audit did not start or validate:

- a camera or its current `/dev/videoX` assignment;
- ROS Master or an external Robotiq FT300 driver;
- FT300 rate, sign, frame transform, software zero, load accuracy, or synchronization under physical contact;
- CUDA execution;
- live 3D Shape Reconstruction;
- model training or checkpoint quality;
- real-time tactile-only physical wrench prediction;
- prediction-versus-FT300 accuracy.

The complete Ubuntu commands and acceptance checks are documented in `README.md` and `docs/01_INSTALLATION_UBUNTU20.md` through `docs/12_TROUBLESHOOTING.md`. The release should be considered for merge only after both sensors complete the documented Ubuntu hardware checks.
