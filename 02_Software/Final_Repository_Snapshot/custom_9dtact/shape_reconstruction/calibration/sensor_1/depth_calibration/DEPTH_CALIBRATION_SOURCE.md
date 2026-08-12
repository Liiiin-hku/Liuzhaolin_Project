# Sensor 1 深度标定来源说明

## 当前活动文件

- 文件：`Pixel_to_Depth.npy`
- 替换日期：2026-07-26
- 来源：官方 `Original` 9DTact 项目的深度查找表
- 官方源文件项目内相对路径：`Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`
- 官方源文件 SHA-256：`19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`
- 当前目标文件 SHA-256：`19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`

## 标定边界

Sensor 1 仍使用 Sensor 1 自己的 Camera Calibration，包括其 `row_index.npy`、`col_index.npy` 和 `position_scale.npy`。本次没有从官方项目或 Sensor 2 复制任何 Camera Calibration 文件。

当前配置是“自制 Sensor 1 Camera Calibration + 官方 9DTact `Pixel_to_Depth.npy`”的实验性混合标定方案。它不等于已经对自制 Sensor 1 完成准确的深度标定，也不能据此声称形状重建精度或轻压灵敏度已经改善。

## 验证与回滚

Windows 环境只能进行文件、哈希和 NumPy 静态检查。必须回到 Ubuntu 20.04，连接 Sensor 1 真实硬件后运行 Shape Reconstruction，检查无接触平整度、轻压响应、连续增高、松开恢复和按压位置。

如果实际效果变差或出现异常，应停止实验，并从项目外部的修改前备份目录恢复 `Sensor1_Pixel_to_Depth_custom_before_original_lut.npy`，覆盖当前 Sensor 1 的 `Pixel_to_Depth.npy`。回滚时不得改动 Sensor 1 的 Camera Calibration。
