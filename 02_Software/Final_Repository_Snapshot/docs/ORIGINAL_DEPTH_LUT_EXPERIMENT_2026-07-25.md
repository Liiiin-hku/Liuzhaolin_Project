# Official Depth-LUT Hybrid Calibration Experiment

[Home](../README.md) | [Sensor calibration guide](04_SENSOR_CALIBRATION.md) | [Shape validation](05_SHAPE_RECONSTRUCTION.md)

## Background

The two custom tactile-sensor paths already contained active camera-mapping and depth
files. The custom depth response was considered insufficiently sensitive for a light
press, so this controlled experiment copied one selected upstream 9DTact
`Pixel_to_Depth.npy` into both custom active depth paths while leaving the camera paths
untouched.

The purpose is to compare physical response on real hardware. A matching file hash and
a successful static check do not show that light-press response improved, that shape
reconstruction passed, or that the resulting depth estimate is accurate.

## How the upstream source was selected

Two filename candidates exist under the protected `Original/` snapshot:

| Candidate | Bytes | Shape | SHA-256 |
|---|---:|---:|---|
| `Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy` | 616 | `(61,)` | `19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF` |
| `Original/shape_reconstruction/calibration/sensor_2/depth_calibration/Pixel_to_Depth.npy` | 568 | `(55,)` | `D84DE22E2ACB5E77BCC1D12F28BD42812FBD93BDEAB43C27314C0A951A82181B` |

`Original/shape_reconstruction/shape_config.yaml` declares `sensor_id: 1`, points its
calibration root to `../shape_reconstruction/calibration`, and names
`/depth_calibration/Pixel_to_Depth.npy`. Therefore the configuration resolves the
upstream runtime LUT to the Sensor 1 candidate. The experiment uses that file rather
than selecting a candidate by timestamp or size.

Selected-source numerical record:

- shape: `(61,)`;
- minimum: `-0.9467841221106313`;
- maximum: `1.9151455666508503`;
- all values finite;
- maximum greater than zero;
- SHA-256:
  `19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`.

`Original/` remains byte-preserved and read-only.

## Changed active files

Replacement date recorded by the original experiment: 2026-07-26.

Only these active binary files were replaced:

1. `custom_9dtact/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`
2. `custom_9dtact/shape_reconstruction/calibration/sensor_2/depth_calibration/Pixel_to_Depth.npy`

Both target files are expected to have the selected-source SHA-256 above.

No upstream camera array, camera directory, reference/sample image, crop setting,
camera channel, reconstruction algorithm, sensor gray-to-depth logic, neural network,
loss function, or training algorithm was copied as part of this experiment.

## Camera-path protection and provenance

The active camera files remain under sensor-specific paths:

```text
custom_9dtact/shape_reconstruction/calibration/sensor_1/camera_calibration/
custom_9dtact/shape_reconstruction/calibration/sensor_2/camera_calibration/
```

Each contains `row_index.npy`, `col_index.npy`, and `position_scale.npy`. The current
core arrays in the two paths are byte-identical. This experiment did not change them,
but byte identity does not establish that the two devices were independently mapped.
Sensor 2 includes manual-point provenance artifacts; Sensor 1 lacks independent
manual-point source artifacts in this delivery.

The experiment's protection condition is that each sensor-specific path remains
unchanged across the LUT replacement. It does not require or imply distinct camera
array contents.

## Experimental status and risks

The resulting arrangement is:

- Sensor 1 sensor-specific active camera path plus the selected upstream Sensor 1 LUT;
- Sensor 2 sensor-specific active camera path plus the same selected upstream Sensor 1
  LUT.

This is an experimental hybrid calibration and must not be reported as an independent,
precise depth calibration of either custom sensor.

Principal risks include:

- mismatch in elastomer, optics, illumination, geometry, or camera response;
- offset, curvature, or noise in the no-contact surface;
- incorrect height scale, sign, saturation, or discontinuity;
- unchanged or worse light-press visibility;
- different physical behavior between the custom sensors despite an identical LUT;
- misleading conclusions if camera mapping, reference capture, and LUT response are not
  evaluated separately.

## Static verification

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/verify_hybrid_calibration.py
```

The verifier checks source resolution, hashes, NumPy loading, finiteness, and required
array shapes. It does not open a camera, run Shape Reconstruction, access FT300, or
start ROS.

## Ubuntu 20.04 hardware validation

Test one sensor at a time.

### Sensor 1

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
conda activate 9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
cd shape_reconstruction
python _3_Shape_Reconstruction.py
```

### Sensor 2

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
conda activate 9dtact
python tools/activate_sensor.py --sensor-id 2
python tools/check_sensor_setup.py --sensor-id 2
cd shape_reconstruction
python _3_Shape_Reconstruction.py
```

For each sensor, record:

- no-contact surface flatness and noise;
- light-press visibility;
- continuity of height under a medium press;
- recovery after release;
- correctness of contact location;
- repeatability across positions and repeated contacts.

Only evidence from both physical sensors can support retaining the hybrid arrangement.

## Leaving the hybrid state intentionally

After selecting a sensor, running:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/shape_reconstruction
python _2_Sensor_Calibration.py
```

trains and replaces that active sensor's `Pixel_to_Depth.npy`. This intentionally exits
the official hybrid-LUT state. Back up the active LUT before running it and record the
new file's provenance and hash.

## Rollback

Before the original replacement, the custom LUTs were intended to be stored outside
the repository as:

- `Sensor1_Pixel_to_Depth_custom_before_original_lut.npy`;
- `Sensor2_Pixel_to_Depth_custom_before_original_lut.npy`.

Restore only the backup belonging to the same sensor:

```bash
cp <PROJECT_EXTERNAL_BACKUP_DIR>/Sensor1_Pixel_to_Depth_custom_before_original_lut.npy \
  <LOCAL_PROJECT_ROOT>/custom_9dtact/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy

cp <PROJECT_EXTERNAL_BACKUP_DIR>/Sensor2_Pixel_to_Depth_custom_before_original_lut.npy \
  <LOCAL_PROJECT_ROOT>/custom_9dtact/shape_reconstruction/calibration/sensor_2/depth_calibration/Pixel_to_Depth.npy
```

Calculate hashes, run each sensor's setup check, and repeat the physical shape test.
Do not change camera arrays during LUT rollback.

To restore the official hybrid experiment instead, copy the selected upstream Sensor 1
LUT to both active depth paths and rerun `tools/verify_hybrid_calibration.py`. A passing
result confirms the file state only; physical revalidation is still required.
