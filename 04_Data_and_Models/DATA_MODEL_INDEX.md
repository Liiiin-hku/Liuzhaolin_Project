# Data and Model Asset Index

## Retained project evidence

- `02_Calibration_Data/CALIBRATION_FILE_MANIFEST.csv` inventories active Sensor 1 and Sensor 2 calibration evidence.
- `02_Calibration_Data/Documentation_Images/` contains the calibration board, indenter, depth-calibration process, and manual 63-point camera-calibration images.
- `03_Processed_Data/Shape_Reconstruction_Results/shape_reconstruction_result.png` records the retained Shape Reconstruction result.
- The authoritative calibration arrays and images remain in `02_Software/Final_Repository_Snapshot/custom_9dtact/shape_reconstruction/calibration/`.

## Implemented data workflow

The frozen code contains the complete software structure for:

1. independent Sensor 1 / Sensor 2 dataset roots;
2. synchronized tactile image, mixed image, and FT300 six-axis wrench collection;
3. finite-value and triplet-integrity checking;
4. object-disjoint train/test splitting;
5. wrench normalization and saved normalization metadata;
6. ResNet/DenseNet training;
7. model-associated inference metadata;
8. normalized and physical-unit inference output;
9. ROS prediction and optional FT300 comparison.

Main documentation and entry points are under:

- `02_Software/Final_Repository_Snapshot/docs/07_DATA_COLLECTION.md`
- `02_Software/Final_Repository_Snapshot/docs/08_DATA_PROCESSING.md`
- `02_Software/Final_Repository_Snapshot/docs/09_MODEL_TRAINING.md`
- `02_Software/Final_Repository_Snapshot/docs/10_FORCE_ESTIMATION.md`
- `02_Software/Final_Repository_Snapshot/custom_9dtact/data_collection/`
- `02_Software/Final_Repository_Snapshot/custom_9dtact/force_estimation/`

`DATA_PROTOCOL.md` defines the sample layout, axis order, label units, synchronization method, sensor isolation, collection controls, and integrity checks.

## Upstream reference boundary

Upstream 9DTact reference arrays, images, and examples remain in the immutable software `Original/` snapshot for format and implementation reference. Project-specific calibration evidence is separately identified above.
