# 09 - Six-Axis Force Model Training

[Previous: Data processing](08_DATA_PROCESSING.md) | [Home](../README.md) | [Next: Force estimation](10_FORCE_ESTIMATION.md)

## Training contract

The model learns a normalized six-axis wrench from a tactile image. FT300 samples are
the physical labels used during training and validation. The input image size must
match the active reconstruction crop: `280 x 380`, height x width.

This repository excludes datasets and trained checkpoints. Training begins only after
the selected sensor dataset passes normalization and object-disjoint split checks.

## 1. Install and verify training dependencies

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
source .venv/bin/activate
python -m pip install -r requirements-training.txt
python -m pip install -r requirements-pytorch.txt \
  --index-url https://download.pytorch.org/whl/cpu

cd <LOCAL_PROJECT_ROOT>
python scripts/verify_installation.py --profile training
```

The CPU wheel command is an example. Select and record the appropriate CUDA wheel index
for the actual training computer when GPU acceleration is required.

## 2. Activate and inspect the selected sensor

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1 --require-data
python tools/check_dataset_integrity.py \
  --dataset-root Dataset_sensor_1 \
  --require-normalized \
  --check-splits
```

Review `configs/force_sensor_1.yaml` before activation, or edit it and activate again.
Important fields include:

- `model_choice` and `model_list`;
- `train_mode` and `test_object` (the final templates default to `test_object: true`);
- `mixed_image` and `image_type`;
- `data_dir` and `save_dir`;
- `img_size: [280, 380]`;
- batch size, epoch count, learning rate, and CUDA index;
- physical `wrench_min`, `wrench_max`, and output frame.

Use `split_train_test_by_object.py` as the primary index generator and retain
`test_object: true` for object-disjoint training and evaluation. The compatibility
split tool is also object-group safe.

## 3. ResNet18 smoke test

Set `model_choice: 0`, reduce `num_epoch` to one or two, and use a batch size suitable
for the available memory. Then reactivate and run:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
cd force_estimation
python train.py
```

A successful smoke test should load train/test indices, read images and normalized
six-vectors, perform forward/backward passes, write logs, and save a checkpoint without
path, shape, dtype, or memory errors. It does not establish model accuracy.

## 4. DenseNet169 full run

After the complete pipeline is proven, set `model_choice: 1`, restore the reviewed full
epoch count and hyperparameters, reactivate, and run `python train.py` from
`force_estimation/`.

Monitor TensorBoard using the log directory printed or created for that run:

```bash
tensorboard --logdir <SENSOR_MODEL_RUN_DIRECTORY>/log
```

Each newly created model directory also stores `inference_metadata.json` beside its
`epoch_*.pt` checkpoints. Schema version 1 records the sensor ID, input image size,
`wrench_min`, `wrench_max`, `wrench_frame`, axis order
`[Fx,Fy,Fz,Tx,Ty,Tz]`, axis units `[N,N,N,N*m,N*m,N*m]`, and the normalization
formula. Keep this file beside every copied checkpoint. It is part of the model artifact
because it records how normalized network output is converted to a physical wrench.

Record:

- sensor ID and dataset manifest;
- train/test object IDs and split seed;
- configuration snapshot and code commit;
- model type, pretrained setting, optimizer, learning rate, epochs, and batch size;
- Python, PyTorch, CUDA, GPU, and driver versions;
- best epoch, checkpoint hash, normalized loss, and physical per-axis errors;
- `inference_metadata.json` hash and the recorded sensor/image/range schema;
- any interrupted or excluded runs.

## 5. Evaluate before deployment

Use object-disjoint test data. Examine per-axis force and torque errors, bias, sign,
range coverage, worst cases, and qualitative contact diversity. A single aggregate loss
does not establish reliable six-axis prediction.

After selecting a checkpoint, update only the matching sensor's `weights` entry in its
persistent force template. The expected model directory and epoch file must exist under
that sensor's `saved_models_sensor_X/` directory. Activate the sensor again after the
template update.

## Sensor separation and reproducibility

- Never train Sensor 1 using Sensor 2 configuration or output directory.
- Do not reuse a checkpoint across sensors without explicitly evaluating and reporting
  that transfer experiment.
- Preserve the exact dataset manifest and checkpoint hash outside Git.
- Do not commit datasets, generated runs, or model weights to this source repository.
- Do not report hardware or model accuracy before the corresponding test evidence is
  recorded.
