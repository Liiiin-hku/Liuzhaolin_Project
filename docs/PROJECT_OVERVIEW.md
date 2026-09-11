# 项目概览与个人贡献证据

[返回首页](../README.md) · [硬件导航](../03_Hardware/README.md) · [验证状态](VALIDATION_STATUS.md)

项目面向机器人末端有限安装空间中的视触觉感知。机械工作围绕新相机的安装、镜头与照明对准、硅胶界面制造、排线保护和外部加载接口展开，形成两套样机及 FT300 机械耦合平台。

## 负责内容、方法与证据

| 负责内容 | 设计或实现方法 | 对应材料 | 已有验证及边界 |
|---|---|---|---|
| 传感器结构适配 | 调整外壳与基座，协调相机固定、窗口支撑、安装耳与排线间隙 | [Optimized_Sensor CAD](../03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/)；[爆炸图](assets/sensor-exploded.jpg)；论文第 4 章 | 成品照片和装配记录；本次未打开 SolidWorks 重建，完整定制装配体及 STEP 尚缺 |
| 相机重新选型和定位 | OV5640 相机头内置、解码板外置，通过柔性排线连接 | [电子实物](../03_Hardware/07_PCB_and_Electronics/Photos/sensor_electronics_components.jpg)；[主 BOM](../03_Hardware/05_BOM/Mechanical/Project_Master_BOM.xlsx)；答辩第 5 页 | 实物安装可见；未测光学一致性或批次重复性 |
| 照明与布线集成 | 将八 LED 板与镜头、窗口协调安装；排线避开紧固件与主要载荷路径 | [LED/相机特写](../03_Hardware/07_PCB_and_Electronics/Photos/led_pcb_and_camera.jpg)；[PCB 来源核对](HARDWARE_PROVENANCE.csv) | 安装照片支持集成工作；现存 PCB 源文件与上游相同，独立原创电路设计待补证据 |
| 模具、硅胶制备和样机装配 | 打印及亚克力模具，封边、混合、脱泡、逐层浇注、固化脱模 | [制造过程照片](../03_Hardware/09_Manufacturing_Notes/Process_Photos/)；[DXF](../03_Hardware/04_Engineering_Drawings/Acrylic_Mold/)；论文 4.5–4.8 | 两套成品及过程记录；缺分层厚度统计、气泡率、寿命或材料试验 |
| 手动相机图像校正 | 7 × 9 点有序选择，辅助放大、撤销、预览，再调用 RBF 映射 | [实际脚本](../02_Software/Final_Repository_Snapshot/custom_9dtact/shape_reconstruction/manual_camera_calibration_v2.py)；[标定过程图片](../04_Data_and_Models/02_Calibration_Data/Documentation_Images/Camera_Calibration/) | 63 点脚本和映射数组存在；两套核心数组相同，Sensor 1 独立点选来源不足 |
| 深度与形貌实验 | 球形压头、图像差分及像素到深度映射，观察螺纹接触形貌 | [压头与过程](../04_Data_and_Models/02_Calibration_Data/Documentation_Images/Depth_Calibration/)；[形貌结果](../04_Data_and_Models/03_Processed_Data/Shape_Reconstruction_Results/shape_reconstruction_result.png) | 有实验与定性结果；活动 LUT 复用上游，未提供独立深度误差指标 |
| FT300 机械耦合与加载平台 | 设计传感器和 FT300 连接基座，建立载荷传递路径 | [连接零件](../03_Hardware/01_CAD_Source/SolidWorks_Parts/Test_Connections/)；[平台实物](assets/ft300-platform.jpg)；论文 6.1 | 平台和独立读数的历史描述；缺冻结的置零、变换及完整采集会话日志 |
| 夹爪安装机构 | 保留左右夹爪零件及双传感器朝向抓取区域的装配方案 | [夹爪 CAD](../03_Hardware/01_CAD_Source/SolidWorks_Parts/Gripper/)；[夹爪 STL](../03_Hardware/03_Print_Files_STL/Existing_Source/Gripper/)；[渲染](assets/gripper-cad.jpg) | CAD 方案级；没有可核实的 R5 型号关联、实物抓取或触觉控制实验 |
| 数据与 ROS 集成 | 参数化 FT300 topic、置零/坐标变换、同步三元组、数据检查、训练/推理入口和六个 ROS launch | [数据采集代码](../02_Software/Final_Repository_Snapshot/custom_9dtact/data_collection/collect_data_ft300.py)；[ROS 工作流](../02_Software/Final_Repository_Snapshot/docs/11_ROS_WORKFLOW.md) | 代码实现与离线测试通过；未完成可复核的自制传感器六维力模型定量闭环 |

## 与上游的边界

`Original/` 保存 9DTact 原始代码、设计与许可。本项目沿用其感知原理、RBF 校正和形貌处理路线，新增或适配的脚本不意味着上游算法成为本项目原创。新增工具集中在 `custom_9dtact/`，详见 [冻结快照 Notice](../02_Software/Final_Repository_Snapshot/NOTICE.md)。

本次按 SHA-256 对比外层硬件与快照 `Original/`。13 个原生 SolidWorks 文件中，7 个与上游文件完全相同，包括 LED 板模型、标定板、亚克力窗口和隔离环；其余 6 个文件与该快照不相同。**字节不同只说明文件版本不同，本身不能证明原创设计。** [硬件来源清单](HARDWARE_PROVENANCE.csv) 记录所有外层工程文件的对应关系。

LED PCB 的 `.epro`、Gerber ZIP、电子 BOM、贴片坐标完全相同。部分展开 Gerber 文件有字节差异，尚未证明属于电路修改，不用它们支持独立 PCB 设计主张。

## 尺寸与夹爪型号

“体积缩减约 30%”尚未找到可重算的比较对。答辩 PDF 第 9 页写有约 42 × 38 × 34 mm，但没有明确是否包含安装耳、排线、外置解码板和加载夹具。本次 STL 包络检查仅辅助识别模型范围，STL 无单位，且单个外壳不代表整套系统体积。因此首页不使用缩减百分比。

可见夹爪资料被论文描述为自制双指夹爪装配；没有原厂型号、接口图或装配引用将其闭环到“方舟无限 R5”。保留这条待补证据线索，不断言相关工作从未开展。

## 论文与当前文件的关系

[论文展示版 PDF](../01_Academic/01_Thesis/Final/Dissertation_LIU%20Zhaolin.pdf) 第 4–7 章和 [答辩 PDF](../01_Academic/03_Defense/Final/final%20report.pdf) 是主要工程叙述来源。论文的独立相机/深度实验描述与当前活动标定文件不完全相同，当前复现以冻结配置和哈希核对结果为准。

论文封面的学号已从展示 PDF 移除，技术正文未改；原始可编辑论文不包含在此展示版本。旧版本的技术局限已汇入 [验证状态](VALIDATION_STATUS.md)。
