# 08 - Dataset Processing

[Previous: Data collection](07_DATA_COLLECTION.md) | [Home](../README.md) | [Next: Model training](09_MODEL_TRAINING.md)

## Processing order

For one sensor at a time:

1. create an external backup;
2. run integrity checks on raw triplets;
3. run wrench normalization in dry-run mode;
4. review configured physical ranges and the report;
5. apply cleaning and normalization only to the intended backup copy or approved
   working dataset;
6. create an object-disjoint train/test split;
7. rerun integrity checks including split indices;
8. freeze a manifest for the training run.

## 1. Check raw dataset integrity

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_dataset_integrity.py \
  --dataset-root Dataset_sensor_1 \
  --json-report <DATASET_REPORT_JSON>
```

Review missing companions, unreadable arrays, image dimensions, non-finite labels, and
object IDs. Correct acquisition/provenance errors before normalization.

## 2. Review wrench ranges

Activate the sensor so the active force configuration matches the dataset:

```bash
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1 --require-data
```

The six-vector ranges in `configs/force_sensor_1.yaml` are physical limits in
`Fx, Fy, Fz, Tx, Ty, Tz` order. Force uses newtons; torque uses newton-metres. Confirm
that the zero, sign convention, transform, and experimental safe range are correct
before using those values to reject samples.

## 3. Dry-run normalization

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/data_collection
python wrench_normalization.py \
  --dataset-root ../Dataset_sensor_1 \
  --object-num <MAX_OBJECT_ID> \
  --force-config ../configs/force_sensor_1.yaml \
  --dry-run
```

The dry run writes a processing report but does not modify sample triplets. Review:

- valid, incomplete/unreadable, and out-of-range counts;
- files that would be removed;
- normalized files that would be generated;
- the selected configuration and ranges.

## 4. Apply only after backup and review

```bash
python wrench_normalization.py \
  --dataset-root ../Dataset_sensor_1 \
  --object-num <MAX_OBJECT_ID> \
  --force-config ../configs/force_sensor_1.yaml \
  --apply
```

`--apply` can delete incomplete/out-of-range triplets, renumber valid samples within an
object, and rewrite normalized labels. Preserve the dry-run report and external backup.
Never apply the command to the other sensor's dataset by mistake.

## 5. Create an object-disjoint split

Both final split tools separate complete object groups so frames from one physical
object do not appear in both training and test sets. The primary/default generator for
the force templates is `split_train_test_by_object.py`:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/data_collection
python split_train_test_by_object.py \
  --dataset-root ../Dataset_sensor_1 \
  --object-number <TOTAL_OBJECT_COUNT> \
  --test-object-number <TEST_OBJECT_COUNT> \
  --seed 42
```

The compatibility generator also performs a randomized object-level split:

```bash
python split_train_test.py \
  --dataset-root ../Dataset_sensor_1 \
  --test-ratio 0.2 \
  --seed 42
```

Record the generator, seed, and test object IDs. Do not present adjacent-frame leakage
as a valid generalization result.

## 6. Final integrity check

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_dataset_integrity.py \
  --dataset-root Dataset_sensor_1 \
  --require-normalized \
  --check-splits \
  --json-report <FINAL_DATASET_REPORT_JSON>
```

Confirm that training and test object sets are disjoint and that all indexed paths are
portable relative paths inside the selected dataset. Repeat the full procedure for
Sensor 2 with Sensor 2 paths and configuration.

## Optional portable training bundle

Create a per-sensor bundle outside the repository:

```bash
cd <LOCAL_PROJECT_ROOT>
python scripts/create_training_bundle.py \
  --sensor-id 1 \
  --output <EXTERNAL_OUTPUT>/training_bundle_sensor_1.zip
```

The tool validates structure and adds a SHA-256 manifest. It does not run training and
does not include the other sensor's data.
