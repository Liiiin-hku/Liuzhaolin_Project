# 仓库结构迁移报告

## 范围

- 本地项目占位路径：`<LOCAL_PROJECT_ROOT>`
- 上游快照：`<LOCAL_PROJECT_ROOT>/Original`
- 活动项目：`<LOCAL_PROJECT_ROOT>/custom_9dtact`
- 执行日期：2026-07-22（Asia/Singapore）

本次只进行仓库结构、路径、文档、依赖、运行时文件、许可证、模型占位和静态安全
检查，没有修改 `Original/`，也没有修改标定、重建、网络、损失函数、FT300 物理
定义或 ROS 话题含义。

## Original 完整性

修改前在仓库外生成了 147 个普通文件的相对路径、大小和 SHA-256 清单。修改后的
清单采用同样方式生成，并与修改前逐项比较。归档证据：

- `ORIGINAL_MANIFEST_BEFORE.csv`
- `ORIGINAL_MANIFEST_AFTER.csv`

最终结果：修改前 147 个文件，修改后 147 个文件，逐项差异数为 0；两份外部清单的
SHA-256 均为
`791be7236209a7f89fb0afaa947c96bd9e99624f60fbea39ae322e76edfd7393`。

## 结构变化

- 活动目录从旧的日期中文名称重命名为 `custom_9dtact`；
- 长期中文文档使用稳定 ASCII 文件名并移动到 GitHub 仓库根目录的 `docs/`；
- 活动配置改由 `tools/activate_sensor.py` 本地生成；
- 当前传感器状态与配置备份迁移到 `custom_9dtact/.runtime/`；
- 本地 PDF、输出、数据集、模型和训练包由 `.gitignore` 排除；
- 按物体划分脚本已改用稳定文件名 `split_train_test_by_object.py`。

## 作者标定重复副本

`custom_9dtact/reference_assets/original_author_calibration` 与
`Original/shape_reconstruction/calibration` 共 36 个对应文件。删除前已逐文件比较相对
路径、大小和 SHA-256，差异数为 0，因此活动项目中的二进制重复副本已删除。
作者参考标定仍完整保存在只读 `Original/` 中；两个自制传感器不能直接使用这些结果。

## 本地内容保护

目录重命名前后分别统计了 `Dataset_sensor_1`、`Dataset_sensor_2`、`saved_models`、
`saved_models_sensor_1`、`saved_models_sensor_2`、两个真实标定目录和 `output` 的文件数
与总大小。重命名后的逐目录比较差异数为 0。本地 PDF 和模型没有因取消 Git 跟踪而
被删除。

## 静态验证边界

验证只允许读取文件、解析 YAML、编译 Python、切换本地活动配置和生成临时训练包。
没有访问相机、ROS Master、FT300、CUDA、GPU、真实标定硬件或真实训练。静态检查
通过不等于硬件功能、标定精度或模型效果通过。
