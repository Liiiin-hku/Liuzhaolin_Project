# 9DTact + FT300 自制触觉传感器项目

[English README](README.md) | [版本与验证状态](VERSION_INFO.md)

本仓库是面向毕业设计交付的双自制光学触觉传感器代码工程，基于 9DTact 工作流，覆盖摄像头标定、
三维形状重建、FT300 同步数据采集、数据集处理、六维力模型训练、独立触觉推理和 ROS 1 集成。

Sensor 1 与 Sensor 2 的标定文件、配置、数据集和模型目录彼此隔离。标定、采集、重建、训练或推理前，
一次只激活一个传感器。

> **验证边界：** Windows 已完成的内容属于仓库结构和静态检查，不代表相机、深度响应、FT300、ROS、
> 模型精度或组合硬件测试通过。相关结论仍需在 Ubuntu 20.04 连接真实硬件后逐项验证。

## 当前项目状态

| 环节 | 仓库内容 | 当前证据 |
|---|---|---|
| 传感器切换 | Sensor 1/2 独立模板与激活工具 | 已完成静态配置检查 |
| 摄像头标定 | 自动流程和 7 x 9 手动点选流程 | 两个传感器活动数组存在；Sensor 2 有手动点来源记录 |
| 深度到形状转换 | 官方深度 LUT 混合实验 | 文件一致性通过；物理准确性待实测 |
| 三维形状重建 | 独立程序与 ROS 封装 | 待 Ubuntu 相机实测 |
| FT300 采集 | 图像与 `WrenchStamped` 六维力同步采集 | 需要外部 FT300 驱动和硬件实测 |
| 数据处理 | 完整性检查、归一化以及两种按物体隔离的划分方式 | 离线工具已提供 |
| 力模型训练 | ResNet18 短训练和 DenseNet169 正式训练流程 | 代码已提供；数据集和权重未包含在仓库中 |
| 力推理 | 独立与 ROS 六维力推理 | 需要传感器对应权重并在 Ubuntu 验证 |

## 标定状态必须如实理解

- Sensor 1 和 Sensor 2 分别通过各自的活动路径使用 `row_index.npy`、`col_index.npy` 和
  `position_scale.npy`。当前两个路径中的三份核心数组内容逐字节相同，因此不能据此描述为两个独立生成的
  摄像头映射。
- 两个传感器当前活动的 `Pixel_to_Depth.npy` 都来自上游只读快照中的
  `Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy`。
- 共享 LUT 的 SHA-256 为
  `19C9F3514DCE402D8E710079757394B5445B74E7AFBDD2459DE43798676CB4FF`。
- 当前方案属于实验性混合标定，不等同于分别对两个自制传感器完成了精确深度标定。
- 执行 `shape_reconstruction/_2_Sensor_Calibration.py` 会训练并替换当前活动传感器的 LUT，
  因此会主动退出混合官方 LUT 状态。执行前应备份；如需恢复混合方案，恢复后再次运行
  `python tools/verify_hybrid_calibration.py`。
- 最新 Ubuntu 压缩包中两个传感器均记录 `camera_channel: 2`，形状裁剪尺寸均为 `[280, 380]`，
  力模型 `img_size` 已与其对齐。`/dev/videoX` 编号取决于具体电脑，必须在目标 Ubuntu 主机重新确认。

## 环境基线

- Ubuntu 20.04 LTS
- Python 3.8
- ROS Noetic
- 核心依赖：OpenCV、NumPy、SciPy、Open3D、PyYAML
- 训练依赖：PyTorch 2.0.1、torchvision 0.15.2、TensorBoard
- 外部 FT300 ROS 驱动：必须发布可配置话题类型 `geometry_msgs/WrenchStamped`

仓库不包含 FT300 硬件驱动，也不声称某个厂商驱动获得 ROS Noetic 官方支持。默认示例原始力话题为
`/robotiq_ft_wrench`，实际话题可以配置。

## 新手快速流程

### 1. 安装核心环境

```bash
cd <LOCAL_PROJECT_ROOT>
bash scripts/install_core_ubuntu20.sh
source custom_9dtact/.venv/bin/activate
python scripts/verify_installation.py --profile core
```

ROS 与训练依赖见 [Ubuntu 20.04 安装说明](docs/01_INSTALLATION_UBUNTU20.md)。不要从另一台电脑复制虚拟环境。

### 2. 激活并检查一个传感器

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
```

Sensor 2 将参数改为 `--sensor-id 2`。如目标电脑中的相机不是通道 2，应先修改
`custom_9dtact/configs/` 中对应模板，再重新激活。

### 3. 校验或重新生成摄像头标定

自动标定：

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact/shape_reconstruction
python _1_Camera_Calibration.py
```

手动 7 x 9 点选并重新拍摄参考图与样本图：

```bash
python manual_camera_calibration_v2.py --capture
```

按行优先顺序点击 63 个点；`A` 切换吸附；鼠标右键或 `U` 撤销；Enter 预览；小写 `s` 保存。
工具会在覆盖活动数组前创建带时间戳的内部备份。完整步骤见
[摄像头标定](docs/03_CAMERA_CALIBRATION.md)。Sensor 2 当前有手动点来源记录；Sensor 1 的活动数组没有独立的
手动点源文件，因此不要把其来源描述为可独立重现的手动点选结果。

### 4. 校验混合深度 LUT

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/verify_hybrid_calibration.py
```

该命令只证明文件哈希、数组形状和有限性满足检查条件，不证明真实物理深度响应准确。

### 5. 运行三维形状重建

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/activate_sensor.py --sensor-id 1
python tools/check_sensor_setup.py --sensor-id 1
cd shape_reconstruction
python _3_Shape_Reconstruction.py
```

Sensor 2 必须在新的终端会话中独立激活和测试。分别记录无接触平整度、轻压显示、中压连续性、松开恢复和
接触位置是否正确。

### 6. 采集 FT300 标签数据

FT300 在本项目中用于训练和验证的真实六维力标签。应依次启动 ROS master、触觉图像发布节点、外部 FT300
驱动，再启动采集程序。采集前先检查话题：

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_ft300_topic.py --topic /robotiq_ft_wrench
```

完整步骤见 [FT300 设置](docs/06_FT300_SETUP.md) 和
[数据采集](docs/07_DATA_COLLECTION.md)。结束时先停止记录，再停止采集器，然后停止相机和 FT300 驱动，
最后停止 `roscore`。

### 7. 数据处理、训练与推理

两个传感器的数据集和模型必须分开。训练前运行：

```bash
cd <LOCAL_PROJECT_ROOT>/custom_9dtact
python tools/check_dataset_integrity.py \
  --dataset-root Dataset_sensor_1 \
  --require-normalized \
  --check-splits
```

先用 ResNet18 做短训练检查，再进行 DenseNet169 正式训练。正常的神经网络触觉推理只依赖相机图像和对应
模型权重，不依赖 FT300；只有采集新标签或将预测与真实力比较时需要 FT300。

### 8. ROS 工作流

Catkin 包位于 `custom_9dtact/ros_ws/src/9dtact_ft300_ros`，包含以下六个入口：

- `sensor1_shape.launch`
- `sensor2_shape.launch`
- `ft300_collection.launch`
- `force_estimation.launch`
- `shape_force_demo.launch`
- `compare_prediction_with_ft300.launch`

使用前阅读实际 launch 文件参数，完整顺序见 [ROS 工作流](docs/11_ROS_WORKFLOW.md)。

## 完整文档

- [项目概览](docs/00_PROJECT_OVERVIEW.md)
- [Ubuntu 20.04 安装](docs/01_INSTALLATION_UBUNTU20.md)
- [传感器配置](docs/02_SENSOR_CONFIGURATION.md)
- [摄像头标定](docs/03_CAMERA_CALIBRATION.md)
- [传感器/深度标定](docs/04_SENSOR_CALIBRATION.md)
- [形状重建](docs/05_SHAPE_RECONSTRUCTION.md)
- [FT300 设置](docs/06_FT300_SETUP.md)
- [数据采集](docs/07_DATA_COLLECTION.md)
- [数据处理](docs/08_DATA_PROCESSING.md)
- [模型训练](docs/09_MODEL_TRAINING.md)
- [力估计](docs/10_FORCE_ESTIMATION.md)
- [ROS 工作流](docs/11_ROS_WORKFLOW.md)
- [故障排查](docs/12_TROUBLESHOOTING.md)
- [项目目录](docs/13_PROJECT_TREE.md)
- [官方深度 LUT 混合实验记录](docs/ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md)

## 仓库保护规则

- `Original/` 是字节级保留的上游只读快照，不应修改、删除或重命名其中任何文件。
- 数据集、模型权重、`.runtime/`、缓存、日志、临时输出和训练包不进入 Git。
- 不得交换 Sensor 1 与 Sensor 2 的标定文件、数据集或模型路径。
- 每次真实硬件实验前备份活动标定与数据。

许可证见 [LICENSE](LICENSE)，上游与第三方说明见 [NOTICE.md](NOTICE.md)。
