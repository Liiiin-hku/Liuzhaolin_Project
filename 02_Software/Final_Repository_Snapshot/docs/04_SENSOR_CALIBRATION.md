# 04 - Sensor and Depth Calibration

[Previous: Camera calibration](03_CAMERA_CALIBRATION.md) | [Home](../README.md) | [Next: Shape reconstruction](05_SHAPE_RECONSTRUCTION.md)

## Two different calibration layers

Camera calibration creates the geometric mapping arrays. Sensor/depth calibration
creates `Pixel_to_Depth.npy`, which maps image response to reconstructed depth. Passing
camera calibration does not prove the depth LUT is accurate, and a valid LUT file does
not prove the camera mapping is correct.

## Current experimental hybrid state

Both active sensors currently use a byte-identical copy of:

`Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`

Expected SHA-256:

`19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`

The source array has shape `(61,)`, minimum `-0.9467841221106313`, and maximum
`1.9151455666508503`. Sensor 1 and Sensor 2 retain sensor-specific active camera paths;
the current three core camera arrays are byte-identical between those paths.

This is an experimental hybrid depth-LUT configuration. It is useful for a controlled
response comparison, but it is not an independent, precise depth calibration of either
custom sensor. Optical material, illumination, camera response, elastomer geometry,
and contact mechanics can differ from the upstream device.

## Verify the hybrid state

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/verify_hybrid_calibration.py
```

The script confirms that:

- the selected upstream LUT is uniquely resolved from `Original/` configuration;
- both active LUT hashes match the selected source;
- all arrays load and contain finite values;
- camera-array and LUT shapes meet structural requirements.

It does not touch a camera and does not prove physical response or depth accuracy.

## Creating a new sensor-specific LUT

Only begin a new depth experiment after camera calibration has been accepted and the
current LUT is backed up outside the repository. Activate exactly one sensor:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
cd shape_reconstruction
python _2_Sensor_Calibration.py
```

`_2_Sensor_Calibration.py` trains and replaces the active sensor's
`Pixel_to_Depth.npy`. Therefore this command intentionally exits the official hybrid
LUT state for that sensor. Record the source images, ball radius, illumination,
configuration, date, operator, generated hash, and validation results.

Do not run `verify_hybrid_calibration.py` expecting it to pass immediately after a new
custom LUT is generated; the active LUT is supposed to differ. If the experiment later
returns to the official hybrid state, restore the correct official LUT copy and rerun
the verifier.

## Required physical validation

For each sensor separately, use the standalone reconstruction workflow and record:

- no-contact surface flatness and temporal noise;
- whether a light press is visible;
- whether medium-press height increases continuously;
- saturation, sign reversal, or discontinuity;
- release recovery and baseline drift;
- whether the reconstructed contact location matches the real location;
- repeatability at several positions and over repeated presses.

The hybrid LUT may perform differently on the two custom sensors even though the file
is identical. Accept or reject it per sensor, not as a pair.

## Rollback choices

### Return to a backed-up custom LUT

Copy only the matching sensor's external backup into that sensor's
`depth_calibration/Pixel_to_Depth.npy`, calculate its SHA-256, run the static setup
check, and repeat physical reconstruction. This is no longer the official hybrid
state.

### Return to the official hybrid state

Copy the selected upstream Sensor 1 LUT into the chosen sensor's active depth directory
without changing any camera arrays. Then run:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/verify_hybrid_calibration.py
```

The verifier passes only when both active sensors match the official selected source.
See the detailed experiment record in
[ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md](ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md).
