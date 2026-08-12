# 01 - Installation on Ubuntu 20.04

[Previous: Project overview](00_PROJECT_OVERVIEW.md) | [Home](../README.md) | [Next: Sensor configuration](02_SENSOR_CONFIGURATION.md)

## Baseline and dependency split

Use Ubuntu 20.04, Python 3.8, and ROS Noetic. Dependencies are intentionally divided:

| File or source | Purpose |
|---|---|
| `custom_9dtact/requirements-core.txt` | Camera calibration and shape reconstruction |
| `custom_9dtact/requirements-training.txt` | TensorBoard training support |
| `custom_9dtact/requirements-pytorch.txt` | PyTorch and torchvision versions |
| Ubuntu `apt` / ROS packages | `rospy`, messages, `cv_bridge`, `message_filters`, `ros_numpy`, catkin |
| External installation | FT300 ROS hardware driver |

`requirements.txt` is a convenience Python dependency entry point. For a controlled
installation, install the split files explicitly. Select a PyTorch CPU or CUDA wheel
source appropriate for the target computer; do not infer CUDA compatibility from this
repository.

## 1. Prepare Ubuntu and ROS Noetic

Install ROS Noetic using the official ROS 1 instructions for Ubuntu 20.04, then confirm:

```bash
source /opt/ros/noetic/setup.bash
rosversion -d
python3 --version
```

Expected results are `noetic` and Python 3.8.x. The bootstrap script checks these
conditions and stops on a mismatched distribution or Python version.

## 2. Run the core bootstrap

From the repository root:

```bash
cd <LOCAL_PROJECT_ROOT>
bash scripts/install_core_ubuntu20.sh
```

The script installs the core Ubuntu/ROS packages, creates
`custom_9dtact/.venv` with `--system-site-packages`, installs the pinned core Python
requirements, builds the catkin workspace, and runs dependency import checks. It does
not install an FT300 driver, open a camera, start ROS, run a CUDA workload, or test
hardware.

Activate the environment in each new terminal:

```bash
source /opt/ros/noetic/setup.bash
source <LOCAL_PROJECT_ROOT>/custom_9dtact/.venv/bin/activate
```

`--system-site-packages` is important because ROS Noetic Python modules are installed
by `apt` outside the virtual environment.

## 3. Verify core and ROS imports

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/verify_installation.py --profile core
python scripts/verify_installation.py --profile ros
```

These checks import dependencies and inspect required files. They do not contact
hardware or start a ROS master.

## 4. Add training dependencies when needed

Inside the activated virtual environment:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python -m pip install -r requirements-training.txt
```

Install PyTorch from a wheel index that matches the target computer. CPU example:

```bash
python -m pip install -r requirements-pytorch.txt \
  --index-url https://download.pytorch.org/whl/cpu
```

For CUDA, first record the GPU model, driver version, and the wheel index selected for
PyTorch 2.0.1. Then verify:

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/verify_installation.py --profile training
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

A `False` CUDA result is valid for a CPU installation. Do not start a long training run
until a one- or two-epoch ResNet18 smoke test succeeds.

## 5. Build or rebuild the catkin workspace

```bash
source /opt/ros/noetic/setup.bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/ros_ws
catkin_make
source devel/setup.bash
rospack find nine_dtact_ft300_ros
```

Repeat the `source devel/setup.bash` command in every terminal that launches this
package. Add it to a local shell profile only after the absolute workspace path is
stable.

## 6. Install the external FT300 driver

The repository does not contain a hardware driver. Select and install a driver that
works with the laboratory FT300/controller setup and that publishes
`geometry_msgs/WrenchStamped`. The project default topic is `/robotiq_ft_wrench`, but
the collector and launch files expose a configurable wrench-topic parameter.

After the driver is running, verify message type and samples:

```bash
rostopic type /robotiq_ft_wrench
rostopic hz /robotiq_ft_wrench
rostopic echo -n 1 /robotiq_ft_wrench

cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_ft300_topic.py --topic /robotiq_ft_wrench
```

Do not treat a package installation as proof that timestamps, frame, signs, units,
sample rate, zeroing, or hardware communication are correct.

## 7. Offline repository check

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/verify_submission.py
```

If an external `Original/` baseline manifest is available:

```bash
python scripts/verify_submission.py \
  --original-baseline <ORIGINAL_BASELINE_CSV>
```

## Common installation mistakes

- Using Python 3.12 instead of 3.8.
- Creating a virtual environment without `--system-site-packages`, which hides ROS
  Python packages.
- Installing a CUDA PyTorch wheel that does not match the driver.
- Copying a `.venv` or Conda environment between computers.
- Assuming the FT300 driver is included.
- Running a hardware program before sourcing both Noetic and the catkin workspace.
- Using a host-specific absolute path in configuration or documentation.

Continue with sensor selection only after core and ROS dependency checks pass.
