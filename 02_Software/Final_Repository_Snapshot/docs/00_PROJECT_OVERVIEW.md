# 00 - Project Overview

[Home](../README.md) | [Next: Ubuntu installation](01_INSTALLATION_UBUNTU20.md)

## Purpose

This project implements a complete experimental workflow for two custom 9DTact-style
optical tactile sensors and an FT300 six-axis force/torque reference sensor. It keeps
the two tactile devices isolated while providing a common, repeatable sequence from
camera setup to 3D shape reconstruction and learned force estimation.

The intended execution platform is Ubuntu 20.04 with Python 3.8 and ROS Noetic. A
Windows computer can inspect, package, and run offline static checks, but it is not the
hardware-validation platform.

## End-to-end workflow

1. Install the core Python environment and ROS dependencies.
2. Identify the tactile camera device on the current Ubuntu host.
3. Select Sensor 1 or Sensor 2 and run its static setup check.
4. Validate or rebuild that sensor's camera calibration.
5. Decide whether to retain the hybrid official depth LUT or create a new sensor LUT.
6. Validate standalone 3D shape reconstruction on the physical sensor.
7. Start an external FT300 driver and verify its `WrenchStamped` topic.
8. Collect synchronized tactile images and FT300 wrench labels.
9. Check, normalize, and split the per-sensor dataset.
10. Run a short ResNet18 training smoke test, then a full DenseNet169 experiment.
11. Evaluate tactile-only force inference with a sensor-specific checkpoint.
12. Build and use the ROS package for acquisition, reconstruction, inference, or
    prediction-versus-FT300 comparison.

Do not skip directly to training or ROS inference. Each stage depends on evidence from
the previous stage.

## Sensor isolation

| Resource | Sensor 1 | Sensor 2 |
|---|---|---|
| Shape template | `custom_9dtact/configs/shape_sensor_1.yaml` | `custom_9dtact/configs/shape_sensor_2.yaml` |
| Force template | `custom_9dtact/configs/force_sensor_1.yaml` | `custom_9dtact/configs/force_sensor_2.yaml` |
| Calibration | `.../calibration/sensor_1/` | `.../calibration/sensor_2/` |
| Dataset | `custom_9dtact/Dataset_sensor_1/` | `custom_9dtact/Dataset_sensor_2/` |
| Models | `custom_9dtact/saved_models_sensor_1/` | `custom_9dtact/saved_models_sensor_2/` |

Only one sensor is active at a time. `tools/activate_sensor.py` copies the selected
templates to the active configuration paths and records a local marker under
`.runtime/`. It does not copy calibration arrays between sensors.

## Roles of the two sensing systems

### 9DTact-style optical tactile sensor

The camera observes elastomer deformation. Camera calibration maps the raw image to a
rectified physical grid. A depth LUT converts intensity change to a depth estimate for
3D reconstruction. A neural model can also regress six-axis force/torque from tactile
images after supervised training.

### FT300

The FT300 provides physical ground-truth wrench labels during data acquisition and a
reference during validation. It is not an input to normal trained tactile inference.
The repository expects an external ROS driver to publish
`geometry_msgs/WrenchStamped`; the driver itself is not bundled.

## Current calibration evidence

- Active camera-calibration arrays exist for both sensors.
- Sensor 2 includes manual-point provenance artifacts.
- Sensor 1 active arrays do not include independent source artifacts that reproduce
  their manual point selection.
- Both active depth LUTs match the selected upstream Sensor 1 LUT by SHA-256.
- This shared LUT is an experimental hybrid configuration. It has not been shown to be
  an independently accurate depth calibration for either custom sensor.

## Dimensions and device mapping

- Raw camera resolution: `640 x 480` pixels.
- Reconstruction crop: `280 x 380` pixels, height x width, for both sensors.
- Force-model `img_size`: `280 x 380`, aligned to the crop.
- Latest archived camera channel: `2` for both sensor templates.
- `/dev/videoX` numbering: host-specific; check it before each setup or reconnection.

## What is and is not shipped

Included:

- Source code, configurations, calibration arrays, documentation, ROS package, and
  offline validation tools.

Excluded:

- Raw datasets, trained model weights, local runtime state, caches, logs, generated
  bundles, virtual environments, and the external FT300 hardware driver.

## Completion criteria

The graduation-project software package is structurally complete when the offline
submission verifier passes. The experimental system is hardware-validated only after
both sensors separately pass camera, shape, acquisition, training/inference, and ROS
tests on Ubuntu. Record all settings, model checkpoints, topic names, coordinate
transforms, and test results rather than replacing pending evidence with assumptions.
