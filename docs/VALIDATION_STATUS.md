# 验证状态与技术边界

[返回首页](../README.md) · [贡献证据](PROJECT_OVERVIEW.md) · [版本来源](../VERSION_FREEZE.md)

核对日期：2026-09-11。以代码、活动数组、实物照片、实验记录和视频共同判断。历史材料没有记录的事项写为“当前仓库缺记录”，不据此认定从未做过。

## 四类证据

- **代码已实现**：有入口与相关逻辑，可做静态或离线检查。
- **有定性演示**：实物、界面或形貌响应可见，不能据此推导精度与实时性能。
- **有定量验证**：必须包含试验条件、原始数据、独立参考与可重算指标；本项目不对自定义力模型或形貌精度作此主张。
- **当前仓库缺记录**：证据链尚不能闭合，保留待补材料及相应表述边界。

## 六维力流程逐项区分

| 环节 | 已有证据 | 尚未闭合 |
|---|---|---|
| FT300 机械耦合与独立读数 | 转接 CAD、平台照片，论文 6.1/答辩第 14 页描述初步读数实验 | FT300 驱动版本、真实 topic/frame/rate 与完整运行日志 |
| FT300 无载软件置零 | 采集脚本及 `wrench.py` 实现，离线测试覆盖偏置处理 | 实机无载统计、漂移、预载和零点会话记录；不等于触觉力映射标定 |
| 坐标变换 | 旋转、轴符号及力矩原点位移处理代码 | 最终机械坐标、实测 R/t、轴向加载验证与变换记录 |
| 图像和六轴标签同步采集 | ApproximateTimeSynchronizer、三元组原子写入、数据完整性工具 | 最终自制传感器的规范同步训练数据集和 acquisition_sessions 记录 |
| 触觉图像到六维力映射标定/训练 | 数据拆分、归一化、ResNet/DenseNet 训练与推理入口 | 正式自制模型 checkpoint、训练日志、配套数据与模型配置 |
| 独立精度验证 | 有方法与实验设计说明 | 独立测试集、误差计算结果及测试条件；不报告 MAE/RMSE/R² 等数值 |
| 六轴向量视频 | 触觉按压与屏幕向量变化可见 | 模型、输入数据源、单位、标定版本与传感器编号未冻结；既不能当作 FT300 实测值证明，也不能当作自定义模型预测精度证明 |

上述代码位于 [FT300 采集](../02_Software/Final_Repository_Snapshot/custom_9dtact/data_collection/collect_data_ft300.py)、[wrench 工具](../02_Software/Final_Repository_Snapshot/custom_9dtact/force_estimation/wrench.py)、[训练](../02_Software/Final_Repository_Snapshot/custom_9dtact/force_estimation/train.py) 和 [推理](../02_Software/Final_Repository_Snapshot/custom_9dtact/force_estimation/_1_Force_Estimation.py)。正常推理路径使用触觉图像；FT300 用于标签和可选比较，两者不可混称。

## 相机与深度标定

手动相机标定脚本支持 7 × 9、共 63 点选择及 RBF 校正；保留了 Sensor 2 点选来源。对活动文件的哈希复核确认：Sensor 1 与 Sensor 2 的 `row_index.npy`、`col_index.npy`、`position_scale.npy` 逐字节相同。Sensor 1 缺独立点集来源，不能写成两套均有独立相机标定证据。

两个活动 `Pixel_to_Depth.npy` 都与 `Original/shape_reconstruction/calibration/sensor_1/depth_calibration/Pixel_to_Depth.npy` 相同，SHA-256 为 `19c9f3514dce402d8e710079757394b5445b74e7afbdd2459de43798676cb4ff`。这是保留的混合 LUT 实验配置。

论文与照片描述了球形压头及深度标定过程，螺纹重建提供定性结果；这些历史记录不能替代当前活动 LUT 的独立来源。没有对应到最终活动文件的独立深度误差测量、标定重复性或重装一致性记录。

快照内较早的局部 README 可能要求“不得复制标定”；当前实际冻结状态及例外由 [最终软件审查](../02_Software/Final_Repository_Snapshot/FINAL_AUDIT_REPORT.md) 和 [混合 LUT 实验记录](../02_Software/Final_Repository_Snapshot/docs/ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md) 解释，本次保留原文件，不追改历史软件说明。

## 机械、电气与制造限制

- 13 个原生 CAD 文件存在，但没有完整自定义传感器/夹爪 STEP 装配；原始 SolidWorks 创作版本、单位和重建状态尚未确认。
- 本次未对装配干涉、强度、疲劳、密封、寿命及制造公差做试验。9 个 STL 的结构检查不等于可制造性或尺寸验收。
- 制造照片和两套实物支持制作完成；缺最终逐步装配、端到端接线与统一供电参数，未形成经负责人核准的完整硬件说明。
- 夹爪仅有 CAD/STL 与渲染；当前没有实物抓取或触觉闭环控制证据。
- 缺按传感器编号和条件记录的结构化失败案例集；现有成功视频不代表覆盖全部工况。
- “约 30%”体积变化、R5 型号归属、原创 PCB 设计均不能由现有材料独立核实。

## 本次重新执行的检查

环境为 Windows、Python 3.12。项目运行基线仍为 Ubuntu 20.04 / Python 3.8 / ROS Noetic；测试依赖仅安装在仓库外的审查环境。

| 检查 | 本次结果 |
|---|---|
| `python -B -m unittest discover -s custom_9dtact/tests -v` | 30/30 通过；使用测试产生的临时样本，不代表真实采集数据 |
| `python -B scripts/verify_submission.py --strict-package` | 通过；包含 Python 语法、配置、XML、标定哈希与提交包检查 |
| 冻结软件比对 | 与整理前 Git 树一致；关联来源 297 个路径一致，90 个文件仅换行差异及相应内部清单差异，见版本说明 |
| 作品集链接与清单 | 使用仓库外检查程序校验路径、大小写、展示资源与 SHA-256 清单 |

没有运行硬件启动脚本、传感器切换写入、重新标定、真实同步采集、模型训练、CUDA 或 ROS master；没有进行 Ubuntu 实机验证或 SolidWorks 重建。冻结快照旧审查报告中的历史结果保留原日期，不冒充本次测试。
