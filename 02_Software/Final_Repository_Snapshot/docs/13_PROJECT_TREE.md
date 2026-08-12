# 13 - Project Tree and Artifact Policy

[Previous: Troubleshooting](12_TROUBLESHOOTING.md) | [Home](../README.md)

## Repository layout

```text
9DTact_FT300_Custom_Sensor_Project/
|-- README.md
|-- README_CN.md
|-- VERSION_INFO.md
|-- LICENSE
|-- NOTICE.md
|-- Original/                         # byte-preserved upstream reference
|-- docs/
|   |-- 00_PROJECT_OVERVIEW.md
|   |-- 01_INSTALLATION_UBUNTU20.md
|   |-- 02_SENSOR_CONFIGURATION.md
|   |-- 03_CAMERA_CALIBRATION.md
|   |-- 04_SENSOR_CALIBRATION.md
|   |-- 05_SHAPE_RECONSTRUCTION.md
|   |-- 06_FT300_SETUP.md
|   |-- 07_DATA_COLLECTION.md
|   |-- 08_DATA_PROCESSING.md
|   |-- 09_MODEL_TRAINING.md
|   |-- 10_FORCE_ESTIMATION.md
|   |-- 11_ROS_WORKFLOW.md
|   |-- 12_TROUBLESHOOTING.md
|   |-- 13_PROJECT_TREE.md
|   `-- ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md
|-- scripts/
|   |-- install_core_ubuntu20.sh
|   |-- verify_installation.py
|   |-- verify_submission.py
|   `-- create_training_bundle.py
`-- custom_9dtact/
    |-- configs/                      # persistent Sensor 1/2 templates
    |-- data/                         # PyTorch dataset loader
    |-- data_collection/              # FT300 collection and processing
    |-- force_estimation/             # training and standalone inference
    |-- legacy/bota/                  # archived non-active legacy collector
    |-- model/                         # ResNet/DenseNet definitions
    |-- ros_ws/src/9dtact_ft300_ros/  # ROS package source folder
    |   |-- config/
    |   |-- launch/
    |   `-- scripts/
    |-- shape-force_ros/              # repository ROS implementations
    |-- shape_reconstruction/
    |   |-- calibration/
    |   |   |-- sensor_1/
    |   |   `-- sensor_2/
    |   |-- manual_camera_calibration_v2.py
    |   |-- _1_Camera_Calibration.py
    |   |-- _2_Sensor_Calibration.py
    |   `-- _3_Shape_Reconstruction.py
    |-- tests/
    |-- tools/
    |-- environment.yml
    |-- pyproject.toml
    |-- requirements-core.txt
    |-- requirements-training.txt
    |-- requirements-pytorch.txt
    |-- requirements.txt
    `-- setup.py
```

The ROS source directory is `9dtact_ft300_ros`, while the package declared in
`package.xml` is `nine_dtact_ft300_ros`.

## Calibration tree

Each sensor-specific active path contains:

```text
shape_reconstruction/calibration/sensor_X/
|-- camera_calibration/
|   |-- row_index.npy
|   |-- col_index.npy
|   |-- position_scale.npy
|   `-- reference, preview, and provenance artifacts when available
`-- depth_calibration/
    |-- Pixel_to_Depth.npy
    `-- DEPTH_CALIBRATION_SOURCE.md
```

The three core active camera arrays currently have byte-identical contents between the
Sensor 1 and Sensor 2 paths. They remain stored in sensor-specific paths and must not be
described as independently derived. Sensor 2 has manual-point provenance artifacts;
Sensor 1 lacks independent manual-point source artifacts in this delivery.

## Local or generated directories

The following are created by installation or runtime operations and are excluded from
source control:

```text
custom_9dtact/.venv/
custom_9dtact/.runtime/
custom_9dtact/Dataset_sensor_1/
custom_9dtact/Dataset_sensor_2/
custom_9dtact/saved_models_sensor_1/
custom_9dtact/saved_models_sensor_2/
custom_9dtact/ros_ws/build/
custom_9dtact/ros_ws/devel/
training_bundle_sensor_*/
output/
tmp/
__pycache__/
```

Logs, `.tmp` files, `.pyc` files, model checkpoints, raw datasets, comparison CSVs,
and generated archives also remain outside the submission source history.

## Read-only upstream snapshot

`Original/` preserves upstream reference files used for comparison and LUT provenance.
Do not edit, translate, reformat, delete, or rename its contents. Custom work belongs in
`custom_9dtact/` or repository-level documentation.

## Artifact handling rules

- Back up calibration and datasets outside the repository before a modifying step.
- Preserve triplet consistency for image, mixed-image, and wrench files.
- Keep Sensor 1 and Sensor 2 data/model/configuration paths separate.
- Record hashes for calibration arrays, dataset manifests, and selected checkpoints.
- Do not commit generated model weights or datasets.
- Do not use a local absolute user path in committed files; use
  `<LOCAL_PROJECT_ROOT>` in instructions.
- Run the offline submission verifier before packaging.

## Final package check

From an extracted delivery copy:

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/verify_submission.py --strict-package
```

The strict package check rejects local environments, datasets, trained weights, caches,
logs, and other generated artifacts. It does not test camera or FT300 hardware.
