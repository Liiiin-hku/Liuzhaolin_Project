# Version and Validation Information

## Delivery identity

- Delivery name: 9DTact + FT300 Custom Tactile Sensor Graduation Project
- Documentation date: 2026-08-11
- Source baseline commit: `0b8d18ac47ef4eb7bf116efac63c2eee5e83aded`
- Delivery branch: `submission/final-sensor-code`
- Target platform: Ubuntu 20.04 LTS
- Python baseline: 3.8
- ROS baseline: ROS Noetic

The source baseline identifies the repository state from which the final submission was
assembled. Final delivery changes on the branch are intentionally newer than that
baseline.

## Active sensor configuration facts

| Item | Sensor 1 | Sensor 2 |
|---|---:|---:|
| Archived Ubuntu camera channel | `2` | `2` |
| Camera resolution | `640 x 480` | `640 x 480` |
| Reconstruction crop, height x width | `280 x 380` | `280 x 380` |
| Force-model image size, height x width | `280 x 380` | `280 x 380` |
| Dataset directory | `Dataset_sensor_1` | `Dataset_sensor_2` |
| Model directory | `saved_models_sensor_1` | `saved_models_sensor_2` |

The camera channel records the latest exported Ubuntu configuration, not a portable
device identity. `/dev/videoX` enumeration can change after reconnecting hardware or
moving the repository to another host.

## Hybrid depth-LUT state

Both active custom sensors use this upstream source LUT:

`Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`

- Array shape: `(61,)`
- Minimum: `-0.9467841221106313`
- Maximum: `1.9151455666508503`
- SHA-256: `19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`

Each sensor retains a sensor-specific active camera path. The current three core camera
arrays are byte-identical between those paths and must not be described as independently
derived. File identity and numerical validity are statically checkable, but the shared
upstream LUT has not been proven to be a precise physical depth calibration for either
custom sensor. Both sensors require separate Ubuntu hardware reconstruction tests.

Running `_2_Sensor_Calibration.py` for an active sensor replaces its
`Pixel_to_Depth.npy` and intentionally exits this hybrid state. Preserve a backup before
that operation. If the official hybrid LUT is restored later, run
`python tools/verify_hybrid_calibration.py` again.

## Camera-calibration provenance

- Sensor 1 active camera arrays are present, but this delivery does not contain
  independent manual-point source artifacts that reproduce their origin.
- Sensor 2 active camera arrays are accompanied by manual-point provenance artifacts.
- Neither statement replaces physical validation of rectification quality on the
  corresponding device.

## Included software layers

- Per-sensor configuration activation and static setup checks
- Automatic and manual camera-calibration workflows
- Hybrid-depth-LUT verification
- Standalone 3D shape reconstruction
- FT300 `WrenchStamped` topic validation and synchronized data collection
- Wrench normalization, dataset integrity checks, and split tools
- ResNet/DenseNet training and six-axis tactile inference
- Per-model `inference_metadata.json` (schema version 1) for sensor identity, input
  size, wrench ranges, frame, axis order, units, and normalization; legacy checkpoints
  require a warned manual-verification fallback that can be disabled in configuration
- ROS Noetic catkin package with six launch workflows
- Offline installation and submission verification scripts

Datasets, trained weights, camera devices, the FT300 hardware driver, ROS installation,
and system-specific virtual environments are not bundled.

## Validation matrix

| Check | Status | Meaning |
|---|---|---|
| Repository structure | Static check available | Required paths can be inspected offline |
| Python 3.8 syntax | Static check available | Source parses against the Python 3.8 grammar |
| YAML and ROS XML | Static check available | Configuration and launch syntax can be parsed |
| Calibration array shapes/finiteness | Static check available | Files are readable and structurally valid |
| Hybrid LUT hash equality | Static check available | Both active LUT files match the selected upstream source |
| Camera acquisition | Pending Ubuntu hardware test | Correct `/dev/videoX`, exposure, focus, and stream must be verified |
| Camera rectification | Pending per-sensor test | Grid geometry and crop must be visually checked |
| Shape reconstruction | Pending per-sensor test | No-contact, press, release, and location response must be recorded |
| FT300 topic and transform | Pending hardware test | Rate, timestamp, frame, sign, zero, and units must be checked |
| Data collection | Pending hardware test | Image/wrench synchronization and saved samples must be checked |
| Training and inference | Pending target-computer test | Requires real datasets, checkpoints, and selected CPU/CUDA stack |
| ROS combined workflow | Pending Ubuntu hardware test | Nodes and topics must be tested together |

## Protected upstream snapshot

`Original/` is a read-only reference snapshot. The final workflow does not edit its
contents. When an external baseline manifest is available, run:

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/verify_submission.py --original-baseline <ORIGINAL_BASELINE_CSV>
```

## Reproducibility commands

Core environment check:

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/verify_installation.py --profile core
```

Offline repository check:

```bash
python scripts/verify_submission.py
```

Hybrid LUT check:

```bash
cd custom_9dtact
python tools/verify_hybrid_calibration.py
```

These commands do not start a camera, ROS master, FT300 device, CUDA workload,
Shape Reconstruction, training, or inference unless a later document explicitly tells
the user to start that stage.
