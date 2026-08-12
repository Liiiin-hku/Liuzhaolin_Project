# Project Notice

This project is derived from the open-source 9DTact project. The upstream paper is "9DTact: A Compact Vision-Based Tactile Sensor for Accurate 3D Shape Reconstruction and Generalizable 6D Force Estimation" (RAL, 2023) by Changyi Lin, Han Zhang, Jikai Xu, Lei Wu, and Huazhe Xu. The paper and project information are available in the upstream repository: <https://github.com/linchangyi1/9DTact>.

`Original/` contains a read-only upstream reference snapshot and is not the normal edit location for custom code. The repository-level `LICENSE` is consistent with the MIT License included in the upstream snapshot.

Custom additions include separate configuration, calibration, and data-path management for Sensor 1 and Sensor 2, together with the Robotiq FT300 six-axis force/torque acquisition workflow. The current workflow runs one tactile sensor at a time.
