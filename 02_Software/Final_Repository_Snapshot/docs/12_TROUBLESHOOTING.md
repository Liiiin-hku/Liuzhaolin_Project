# 12 - Troubleshooting

[Previous: ROS workflow](11_ROS_WORKFLOW.md) | [Home](../README.md) | [Next: Project tree](13_PROJECT_TREE.md)

## Start with evidence

Record the exact command, working directory, sensor ID, active configuration, complete
error text, and recent changes. Run the smallest applicable check before repeating a
hardware operation.

## Python or dependency errors

### Wrong Python version

```bash
python --version
```

Use Python 3.8 on Ubuntu 20.04. Recreate the environment rather than modifying a copied
or incompatible virtual environment.

### ROS imports are missing inside the virtual environment

Source Noetic and use a virtual environment created with system site packages:

```bash
source /opt/ros/noetic/setup.bash
source <LOCAL_PROJECT_ROOT>/custom_9dtact/.venv/bin/activate
python <LOCAL_PROJECT_ROOT>/scripts/verify_installation.py --profile ros
```

If the environment was created without `--system-site-packages`, remove only that local
environment after confirming its resolved path, then rerun the bootstrap script.

### PyTorch/CUDA mismatch

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
nvidia-smi
```

Install a wheel appropriate for the target driver. A CPU wheel is valid for functional
testing but will not provide CUDA acceleration.

## Camera errors

### Camera does not open

```bash
v4l2-ctl --list-devices
ls -l /dev/video*
fuser /dev/video2
```

Correct the selected persistent shape template and reactivate. The archived channel 2
value may differ on the current host.

### No GUI window

Check that the session has a graphical display, OpenCV GUI support, and a valid
`DISPLAY` environment. Remote/headless sessions need an appropriate ROS or file-output
workflow rather than an interactive OpenCV/Open3D program.

### Manual calibration point is wrong

Use right-click or `U` to undo. Press `A` to toggle snapping. After 63 row-major points,
press Enter to preview and `B` to return for corrections. Lowercase `s` is the explicit
save action. `--resume` reloads an incomplete checkpoint; `--no-snap` starts without
local snapping.

### Rectified grid crosses or crop is incomplete

Do not save the preview. Recheck row-major order, border points, orientation, and the
`280 x 380` crop. Restore all three camera arrays from one matching backup if a saved
mapping is worse.

## Depth and shape errors

### Hybrid verifier fails after sensor calibration

`_2_Sensor_Calibration.py` replaces the active LUT, so failure is expected when the
sensor intentionally leaves the official hybrid state. Preserve and label the new LUT.
If restoring the official hybrid experiment, restore both official active LUT copies
without changing camera arrays, then rerun the verifier.

### No-contact surface is noisy or curved

Check reference capture, lighting, focus, mounting, camera mapping, and LUT selection.
Compare backed-up configurations under controlled conditions. Structural array checks
do not diagnose physical depth error.

### Press location or sign is wrong

For location errors, inspect camera row/column mapping and crop. For height sign or
scale errors, inspect the active LUT and sensor response. Do not swap arrays between
sensors as a diagnostic shortcut.

## FT300 and acquisition errors

### Topic has the wrong type or is absent

The external driver must publish `geometry_msgs/WrenchStamped`:

```bash
rostopic type /robotiq_ft_wrench
rostopic echo -n 1 /robotiq_ft_wrench
```

Correct the configured topic or external driver. The repository does not start the
hardware driver.

### Topic checker reports stale or zero timestamps

Correct the publisher's header timestamps and ROS clock configuration. Increasing the
allowed age can hide a synchronization defect and should not be the first response.

### Empty or changing frame ID

Publish a stable physical frame and configure the expected frame. Document the
transform into the tactile frame.

### Zeroing fails or force signs look wrong

Remove contact, allow the system to settle, inspect standard deviation, and review
axis signs, rotation, and translation in `ft300.yaml`. Software zeroing removes offset;
it does not correct scale or geometry.

### Image/wrench pairs are missing

Check image and wrench topic rates, timestamps, `sync_slop`, freshness limits, and
collector logs. Preserve incomplete data until the cause is recorded, then process a
backup copy using the dry-run workflow.

## Dataset and training errors

### Integrity checker reports incomplete triplets

One or more matching image, mixed-image, or raw-wrench files are absent. Return to the
session log and backup. Run normalization dry-run before any destructive apply step.

### Object leakage is detected

Regenerate indices with `split_train_test_by_object.py`. The default force templates
use `test_object: true`; all frames belonging to one object must remain on one side of
the train/test boundary.

### Model cannot find weights

Confirm the selected sensor's `model_choice`, run suffix, epoch, and exact
`saved_models_sensor_X/.../epoch_N.pt` path. Reactivate after editing the persistent
template.

### Model image-size error

Confirm both selected configuration values are `[280, 380]` in height-width order and
that dataset images have the same dimensions.

## ROS errors

### Package is not found

```bash
source /opt/ros/noetic/setup.bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/ros_ws
catkin_make
source devel/setup.bash
rospack find nine_dtact_ft300_ros
```

The source folder is named `9dtact_ft300_ros`, but the declared ROS package is
`nine_dtact_ft300_ros`.

### Repository runner cannot locate custom_9dtact

Keep the catkin workspace inside this repository layout or set:

```bash
export NINE_DTACT_PROJECT_ROOT=<LOCAL_PROJECT_ROOT>/custom_9dtact
```

### Node starts but publishes nothing

Check `rosnode info`, `rostopic info`, publisher/subscriber topic names, the camera,
configuration path, and upstream node logs. Verify one stage at a time rather than
starting the combined launch first.

## Escalation record

If a problem remains, preserve:

- exact command and full terminal output;
- `git rev-parse HEAD`;
- sensor ID and configuration copies;
- dependency versions;
- topic names, types, frames, rates, and one sanitized sample;
- calibration and checkpoint hashes;
- a minimal reproduction that does not overwrite data.
