# 05 - 3D Shape Reconstruction

[Previous: Sensor calibration](04_SENSOR_CALIBRATION.md) | [Home](../README.md) | [Next: FT300 setup](06_FT300_SETUP.md)

## Preconditions

Complete these steps for the selected sensor before opening the reconstruction program:

- confirm the Ubuntu camera channel with `v4l2-ctl`;
- activate the matching sensor templates;
- pass `tools/check_sensor_setup.py`;
- inspect the camera-calibration preview;
- record whether the active LUT is the hybrid official LUT or a custom LUT;
- remove all contact before establishing the reference surface.

The current image pipeline expects a `640 x 480` camera frame and produces a
`280 x 380` rectified crop for both sensor configurations.

## Sensor 1 procedure

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
source .venv/bin/activate
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
cd shape_reconstruction
python _3_Shape_Reconstruction.py
```

## Sensor 2 procedure

Open a fresh terminal after stopping Sensor 1:

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
source .venv/bin/activate
python tools/activate_sensor.py --sensor-id 2
python tools/check_sensor_setup.py --sensor-id 2
cd shape_reconstruction
python _3_Shape_Reconstruction.py
```

The program displays the rectified grayscale image, depth map, and Open3D point cloud.
Press `q` in the OpenCV window or close the Open3D visualizer to stop. Confirm that the
camera has been released before activating the other sensor.

## Required validation sequence

For each sensor, record the sensor ID, camera channel, active calibration hashes, date,
lighting, host, and operator. Then perform:

1. **No contact:** observe surface flatness, offset, noise, and drift for a fixed period.
2. **Light press:** confirm a small deformation appears at the physical contact point.
3. **Medium press:** confirm height changes continuously rather than jumping or
   reversing.
4. **Release:** confirm the reconstructed surface returns near its no-contact baseline.
5. **Location sweep:** press center, edges, and corners and compare real versus displayed
   contact location.
6. **Repeatability:** repeat a consistent press several times and compare response.

Do not describe light-press sensitivity as improved until measurements on the physical
sensor support that conclusion.

## Interpreting common symptoms

| Symptom | Likely checks |
|---|---|
| Camera does not open | Verify `/dev/videoX`, permissions, and competing processes |
| Output is rotated or mirrored | Recheck point order and physical orientation |
| Grid folds or crosses | Rebuild camera mapping; inspect manual preview before saving |
| Crop is incomplete | Confirm `crop_size: [280, 380]` and camera calibration |
| No-contact surface is uneven | Check reference image, lighting stability, camera mapping, and LUT |
| Contact position is wrong | Check row/column mapping and crop origin |
| Height sign or scale is implausible | Treat the active LUT as unvalidated and compare against a controlled backup |
| Sensor 1 and Sensor 2 look identical | Confirm active marker, configuration, camera, and calibration paths |

## Hybrid-LUT comparison

When comparing the official hybrid LUT with a custom LUT:

- change only the intended sensor's `Pixel_to_Depth.npy`;
- preserve that sensor's camera-mapping files;
- keep illumination and mechanical test conditions constant;
- hash and label every LUT;
- record results for Sensor 1 and Sensor 2 separately;
- restore from a verified backup rather than copying from the other sensor.

Running `_2_Sensor_Calibration.py` changes the active LUT and exits the current hybrid
state. If the official LUT is later restored for both sensors, rerun
`python tools/verify_hybrid_calibration.py`.

Proceed to FT300 setup only after standalone reconstruction is stable enough to capture
meaningful tactile images.
