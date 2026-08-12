# 10 - Six-Axis Force Estimation

[Previous: Model training](09_MODEL_TRAINING.md) | [Home](../README.md) | [Next: ROS workflow](11_ROS_WORKFLOW.md)

## Inference boundary

After supervised training, the tactile network predicts
`Fx, Fy, Fz, Tx, Ty, Tz` from the optical tactile image representation. The selected
checkpoint, sensor configuration, camera calibration, and image crop are required.

FT300 input is not required for normal neural inference. It is required when collecting
new ground-truth labels or comparing predictions with a physical reference.

## 1. Configure a sensor-specific checkpoint

In the selected persistent force template, set the matching model choice and weight
identifier. The configuration uses an entry containing a model-directory suffix and an
epoch. The resolved file must exist under the same sensor's model directory as:

```text
saved_models_sensor_X/<MODEL_TYPE><RUN_SUFFIX>/epoch_<EPOCH>.pt
```

Also confirm:

- `img_size` is `[280, 380]`;
- `wrench_min` and `wrench_max` match the label normalization used for training;
- `wrench_frame` identifies the tactile prediction frame;
- the dataset, configuration, model run, and checkpoint all belong to the same sensor;
- model-directory `inference_metadata.json` records the same `sensor_id`, `img_size`,
  `wrench_min`, `wrench_max`, axis order, and units as the intended deployment;
- the checkpoint hash and training report have been recorded.

Reactivate after editing the persistent template:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
```

`Estimator` requires exact agreement between schema-version-1 metadata and the active
configuration before loading a new checkpoint. A legacy checkpoint without
`inference_metadata.json` can use the current force YAML as an explicit fallback and
emits a `RuntimeWarning` that the original ranges must be verified before predictions
are treated as N/N*m. Set `allow_legacy_metadata_fallback: false` in the force
configuration to make missing metadata fatal. Even when fallback is enabled, manually
verify sensor identity, image size, wrench ranges, frame, axis order, and units before
reporting physical values.

## 2. Run standalone tactile inference

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/force_estimation
python _1_Force_Estimation.py
```

The standalone visualizer uses the current camera and active shape/force configuration.
Press `q` in the OpenCV window or close the visualizer to stop. The legacy graphical
force display consumes normalized model output; the `Estimator.predict_force()` API
and ROS predicted-wrench topic convert the output back to physical units using the
configured wrench ranges.

Do not interpret a plausible animation as an accuracy result. Compare recorded
predictions against held-out FT300 labels in physical units.

## 3. Run ROS inference

After building and sourcing the catkin workspace:

```bash
roslaunch nine_dtact_ft300_ros force_estimation.launch \
  shape_config:=configs/shape_sensor_1.yaml \
  force_config:=configs/force_sensor_1.yaml
```

The launch starts a tactile image/representation publisher by default and publishes:

- physical prediction: `/predicted_wrench`, `geometry_msgs/WrenchStamped`;
- normalized prediction: `/predicted_wrench_normalized`,
  `std_msgs/Float64MultiArray`.

Use `start_sensor:=false` only when a compatible representation publisher is already
running on the configured `representation_topic`.

For Sensor 2, use both Sensor 2 configuration paths. Do not change only one of them.

## 4. Validate output

Check interface and frame:

```bash
rostopic type /predicted_wrench
rostopic hz /predicted_wrench
rostopic echo -n 1 /predicted_wrench
```

Then compare against held-out FT300 data or use the dedicated comparison launch. Record
per-axis bias, mean absolute error, range-dependent error, sign, latency, and failure
cases. Use synchronized physical-unit values and a reviewed coordinate transform.

## Common inference errors

| Error | Check |
|---|---|
| Weights are not configured | Set the sensor template's run suffix and epoch |
| Checkpoint file is missing | Confirm exact model directory and `epoch_N.pt` |
| Inference metadata mismatch | Use the matching sensor model or correct the deployment configuration |
| Legacy-checkpoint warning | Manually verify ranges, axis order, units, sensor ID, and image size |
| Image-size mismatch | Align shape crop and force `img_size` to `[280, 380]` |
| Output sign is implausible | Check training-label frame/sign and FT300 comparison transform |
| Predictions saturate | Check configured ranges, normalization, data coverage, and model fit |
| Sensor 2 uses Sensor 1 model | Stop, correct both config paths, reactivate, and retest |
| Low frame rate | Check camera rate, CPU/GPU load, display overhead, and ROS topic queues |

Model inference is complete only when the selected checkpoint runs reproducibly and its
physical-unit performance is documented on object-disjoint test data and, where
appropriate, synchronized FT300 measurements.
