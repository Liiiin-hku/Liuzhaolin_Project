# Software Asset Index

## Frozen public authority

- Snapshot: `Final_Repository_Snapshot/`
- Repository: `https://github.com/Liiiin-hku/9DTact_FT300_Custom_Sensor_Project`
- Visibility: Public
- Default/frozen branch: `submission/final-sensor-code`
- Commit: `98ebb7da0010df27ef634f9868e557d77fa73ec5`
- Release tag: No release tag available
- Upstream `Original/`: 138 files with retained SHA-256 inventory

## Contribution structure

- `Original/`: immutable upstream 9DTact snapshot.
- `custom_9dtact/`: dual-sensor configuration, camera/sensor calibration, Shape Reconstruction, Robotiq FT300 collection, force estimation, tests, and ROS Noetic integration.
- `docs/`: numbered installation and full-workflow documentation.
- `scripts/`: installation, validation, and packaging tools.

## Environment

Ubuntu 20.04, Python 3.8, ROS Noetic, PyTorch 2.0.1, and torchvision 0.15.2 form the documented baseline. Core pip, PyTorch, Conda, and ROS dependencies are separated in the package files and installation guide.

## Main routes

| Workflow | Entry point inside `Final_Repository_Snapshot/` |
|---|---|
| Installation | `README.md`, `docs/01_INSTALLATION_UBUNTU20.md` |
| Sensor selection | `custom_9dtact/tools/activate_sensor.py` |
| Setup verification | `custom_9dtact/tools/check_sensor_setup.py` |
| Manual camera calibration | `custom_9dtact/shape_reconstruction/manual_camera_calibration_v2.py` |
| Sensor calibration | `custom_9dtact/shape_reconstruction/_2_Sensor_Calibration.py` |
| Shape Reconstruction | `custom_9dtact/shape_reconstruction/_3_Shape_Reconstruction.py` |
| FT300 topic check | `custom_9dtact/tools/check_ft300_topic.py` |
| Synchronized collection | `custom_9dtact/data_collection/collect_data_ft300.py` |
| Dataset integrity | `custom_9dtact/tools/check_dataset_integrity.py` |
| Model training | `custom_9dtact/force_estimation/train.py` |
| Tactile-only force inference | `custom_9dtact/force_estimation/_1_Force_Estimation.py` |
| ROS workspace | `custom_9dtact/ros_ws/` |
| Offline verification | `scripts/verify_submission.py` |

## Validation and attribution

The package passed the included static verification and offline unit tests. Real camera, FT300, ROS, and trained-model performance are evaluated only in their corresponding hardware/runtime environment.

The repository retains `LICENSE`, `NOTICE.md`, and `Original/LICENSE`. The upstream snapshot is clearly separated from the project-specific additions.
