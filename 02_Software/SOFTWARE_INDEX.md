# 软件复现入口

[返回首页](../README.md) · [验证状态](../docs/VALIDATION_STATUS.md)

完整软件保存在本仓库的 [Final_Repository_Snapshot](Final_Repository_Snapshot/)，可从这里进入，无需把关联仓库当成唯一入口。

来源：关联仓库 [9DTact_FT300_Custom_Sensor_Project](https://github.com/Liiiin-hku/9DTact_FT300_Custom_Sensor_Project)，分支 `submission/final-sensor-code`，固定 commit `98ebb7da0010df27ef634f9868e557d77fa73ec5`。本次仅只读核对该来源。

## 阅读与操作顺序

| 工作流 | 快照内真实文档 |
|---|---|
| 安装环境 | [Ubuntu 20.04 安装](Final_Repository_Snapshot/docs/01_INSTALLATION_UBUNTU20.md) |
| 传感器选择与配置 | [配置说明](Final_Repository_Snapshot/docs/02_SENSOR_CONFIGURATION.md) |
| 相机图像校正 | [相机标定](Final_Repository_Snapshot/docs/03_CAMERA_CALIBRATION.md) |
| 深度标定与形貌 | [传感器标定](Final_Repository_Snapshot/docs/04_SENSOR_CALIBRATION.md)；[形貌重建](Final_Repository_Snapshot/docs/05_SHAPE_RECONSTRUCTION.md) |
| FT300 数据源 | [FT300 设置](Final_Repository_Snapshot/docs/06_FT300_SETUP.md) |
| 采集与数据处理 | [同步采集](Final_Repository_Snapshot/docs/07_DATA_COLLECTION.md)；[数据处理](Final_Repository_Snapshot/docs/08_DATA_PROCESSING.md) |
| 训练与力推理 | [模型训练](Final_Repository_Snapshot/docs/09_MODEL_TRAINING.md)；[推理说明](Final_Repository_Snapshot/docs/10_FORCE_ESTIMATION.md) |
| ROS 启动 | [ROS 工作流](Final_Repository_Snapshot/docs/11_ROS_WORKFLOW.md)；[问题排查](Final_Repository_Snapshot/docs/12_TROUBLESHOOTING.md) |

项目记录的基线为 Ubuntu 20.04、Python 3.8、ROS Noetic、PyTorch 2.0.1 和 torchvision 0.15.2。依赖按原安装文档处理，本次没有升级项目依赖。

## 可以先做的离线检查

从仓库根目录进入快照后，在具备 NumPy 等依赖的审查环境中执行：

```bash
cd 02_Software/Final_Repository_Snapshot
python -B -m unittest discover -s custom_9dtact/tests -v
python -B scripts/verify_submission.py --strict-package
```

硬件运行前一次选择一个 Sensor，核实相机设备编号、标定来源、驱动和 topic。FT300 驱动不随本项目提供；本仓库缺可直接复现自制六维力结果所需的正式模型和训练集。

`Original/` 与其 LICENSE 保持不变；项目工具位于 `custom_9dtact/`。完整许可见 [LICENSE](Final_Repository_Snapshot/LICENSE)、[NOTICE](Final_Repository_Snapshot/NOTICE.md) 与 [外层权属说明](../docs/RIGHTS_AND_ATTRIBUTION.md)。
