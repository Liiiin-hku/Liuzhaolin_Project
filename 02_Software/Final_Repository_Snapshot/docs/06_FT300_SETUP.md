# 06 - FT300 Setup and Topic Validation

[Previous: Shape reconstruction](05_SHAPE_RECONSTRUCTION.md) | [Home](../README.md) | [Next: Data collection](07_DATA_COLLECTION.md)

## Role and software boundary

The FT300 supplies physical six-axis labels in the order
`Fx, Fy, Fz, Tx, Ty, Tz`. Force components use newtons and torque components use
newton-metres. It is used for supervised data acquisition and prediction validation.
It is not required for normal tactile-only neural inference after a model is trained.

The repository does not bundle an FT300 hardware driver. Install an external driver
appropriate for the laboratory controller and require it to publish
`geometry_msgs/WrenchStamped`. The project default topic is `/robotiq_ft_wrench`, but
the input topic is configurable.

No claim is made that a particular external driver is officially supported on ROS
Noetic. Driver/controller compatibility must be established on the target system.

## Mechanical and coordinate preparation

Before starting software:

- mount the FT300 and tactile sensor rigidly;
- record the FT300 serial/device identity and mounting orientation;
- define the tactile output frame;
- record the rotation and translation from the raw wrench frame to the tactile frame;
- check cable strain and ensure the unloaded system is mechanically stable;
- establish emergency-stop and load-limit procedures for the connected equipment.

The code can apply axis signs, a 3 x 3 rotation, and translation-induced torque. These
parameters must be derived from the real mounting geometry, not chosen to make plots
look convenient.

## Startup order for FT300 validation

Terminal 1 - ROS master:

```bash
source /opt/ros/noetic/setup.bash
roscore
```

Terminal 2 - external FT300 driver:

```bash
source /opt/ros/noetic/setup.bash
<START_EXTERNAL_FT300_DRIVER>
```

Terminal 3 - inspect the published interface:

```bash
source /opt/ros/noetic/setup.bash
rostopic type /robotiq_ft_wrench
rostopic hz /robotiq_ft_wrench
rostopic echo -n 1 /robotiq_ft_wrench
```

The required message type is exactly `geometry_msgs/WrenchStamped`. The header needs a
non-zero, recent timestamp and a non-empty, stable frame ID.

Run the repository checker:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
source .venv/bin/activate
python tools/check_ft300_topic.py \
  --topic /robotiq_ft_wrench \
  --samples 100 \
  --min-rate 10
```

If a specific frame is required, add `--expected-frame <FT300_FRAME>`. The check tests
message freshness, frame consistency, finite values, and observed header rate. It does
not establish calibration accuracy or mounting correctness.

## Zeroing and sign checks

1. Remove all external contact and allow the mounted system to settle.
2. Record mean and standard deviation before zeroing.
3. Apply the project's software-zero operation only while the system is unloaded.
4. Apply a gentle, known-direction load along each axis and verify the expected sign.
5. Apply a known lever-arm load to check torque signs and the translation transform.
6. Repeat the unloaded measurement to check drift.

Software zeroing removes the measured offset for that session. It does not calibrate
scale, compensate an incorrect transform, repair cross-axis coupling, or prove the
sensor is mounted correctly.

## Wrench ranges

The per-sensor force templates contain `wrench_min` and `wrench_max`. These ranges define
label validation, normalization, and conversion of network outputs back to physical
units. Review them against the safe experimental envelope before collecting data.

Samples outside the configured range can be rejected during processing. Never widen a
range solely to hide an incorrect sign, zero, unit, or transform.

## Shutdown order

After topic validation or acquisition:

1. stop recording and allow pending writes to finish;
2. stop the collector or comparison node;
3. stop the tactile camera publisher;
4. stop the external FT300 driver;
5. stop `roscore` last;
6. verify dataset files and copy the session to backup storage.

Use Ctrl+C once per terminal and wait for clean shutdown output before closing it.
