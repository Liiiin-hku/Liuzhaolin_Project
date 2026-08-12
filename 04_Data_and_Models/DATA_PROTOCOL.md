# Data Collection Protocol

## Label definition and system boundary

During supervised collection, a custom 9DTact sensor supplies rectified tactile images and the Robotiq FT300 supplies six physical labels: `Fx, Fy, Fz, Tx, Ty, Tz`. Forces use newtons and torques use newton-metres after the documented frame/sign transform. After training, tactile-only inference must not require FT300 input; FT300 remains the ground-truth source for collection and optional validation.

## Sensor isolation

- Sensor 1 dataset root: `Dataset_sensor_1/`
- Sensor 2 dataset root: `Dataset_sensor_2/`
- Never mix sensors, calibration files, normalization metadata, or checkpoints.
- Object IDs are experimental groups; one physical object must not appear in both training and test sets.

## Synchronized sample contract

The collector uses ROS `ApproximateTimeSynchronizer` on the rectified image and a configurable `geometry_msgs/WrenchStamped` topic. Each accepted sample is committed as an atomic triplet:

```text
Dataset_sensor_X/
|-- image/<OBJECT_ID>/<INDEX>.png
|-- mixed_image/<OBJECT_ID>/<INDEX>.png
|-- wrench/<OBJECT_ID>/<INDEX>.npy
`-- acquisition_sessions/<SESSION>.json
```

The wrench label must be a finite six-vector ordered `[Fx, Fy, Fz, Tx, Ty, Tz]`. A common object ID and index identify one sample; never rename one triplet member independently.

## Session record

For every collection session, record the Sensor ID, object/trial ID, calibration and configuration hashes, camera device/settings, FT300 driver/topic/frame/rate, axis/sign/rigid transform, torque origin, unloaded-zero statistics, wrench ranges, synchronization tolerance, save thresholds, operator, host, environment, and observations.

## Collection controls

- Space: start/pause recording
- `n`: next object ID
- `z`: unloaded software zero
- `q`: exit
- Headless services: private `set_recording`, `zero`, and `next_object`

## Checks

Before collection: activate one sensor, verify crop/configuration, inspect the rectified image, check FT300 type/rate/stamp/frame/finite values, and zero only while unloaded. After collection: run `02_Software/Final_Repository_Snapshot/custom_9dtact/tools/check_dataset_integrity.py`, inspect matched triplets, back up the dataset, save normalization metadata, and create object-disjoint splits.

The operational procedures are in `02_Software/Final_Repository_Snapshot/docs/07_DATA_COLLECTION.md` and `02_Software/Final_Repository_Snapshot/docs/08_DATA_PROCESSING.md`.

## Data scope

The project data contract contains tactile images of contact objects and six-axis wrench labels rather than identified human-subject data. Upstream format assets remain separately identified inside the immutable `Original/` snapshot.
