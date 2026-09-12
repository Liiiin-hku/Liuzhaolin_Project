[English](README.md) · 中文

# 面向机器人末端执行器的紧凑型视触觉传感器

**Compact Vision-Based Tactile Sensor for Robotic End Effectors**<br>
**机械结构设计 · 样机制造 · 硬件集成**<br>
**刘钊麟 LIU Zhaolin｜香港大学机械工程硕士**

本项目围绕机器人末端的触觉感知，将紧凑型结构、光学硬件、分层硅胶制造与机械安装接口结合起来。基于开源 **9DTact**，我完成相机与外壳安装适配、照明和内部布线集成，制造并装配 **两套触觉传感器样机**，搭建与 **Robotiq FT300** 六维力传感器机械耦合的实验平台。

仓库展示从 **CAD 和器件集成到实物样机与触觉交互演示** 的工程过程，提供设计文件、制造记录、软件和实验材料。

![两套已装配的触觉传感器样机](docs/assets/sensor-prototypes.jpg)

## 快速查看

| 入口 | 可以查看的内容 |
|---|---|
| [结构设计与硬件](03_Hardware/README.md) | 传感器零件、夹爪安装方案、FT300 转接件、PCB 集成和 BOM |
| [实物与交互演示](05_Demos/README.md) | 短片、原始录像和观看说明 |
| [个人工程贡献](docs/PROJECT_OVERVIEW.md) | 负责内容、设计方法与对应文件 |
| [软件与系统集成](02_Software/SOFTWARE_INDEX.md) | 相机标定、形貌重建、FT300 工作流及 ROS 文档 |

**先看实物：** [22 秒样机短片](05_Demos/Previews/hardware-preview.mp4) · [FT300 实验平台](docs/assets/ft300-platform.jpg) · [制造与实物图集](03_Hardware/08_Renders_and_Photos/PHOTO_CATALOG.md)

## 我的工程工作

- **机械封装与相机适配**：围绕 OV5640 相机和外置解码板，调整外壳、定位、固定、窗口支撑和引线空间。
- **光学与电气集成**：协调镜头、八 LED 照明板与触觉窗口的位置，处理柔性排线出口、紧固件避让和载荷路径。
- **制造与样机装配**：准备打印件和硅胶模具，完成封边、混合、真空脱泡、分层浇注、固化、脱模和两套样机装配。
- **图像校正与触觉实验**：实现交互式 7 × 9 标定点选择工具，开展图像校正、球形压头及接触形貌重建实验。
- **测试夹具与末端接口**：开发 FT300 耦合平台转接结构，以及双指夹爪的传感器安装 CAD 方案。
- **软件与 ROS 集成**：组织传感器配置、FT300 采集、坐标变换、数据检查、训练/推理工作流和 ROS Noetic 运行工具。

## 紧凑型结构与光学集成

![传感器机械与光学结构爆炸图](docs/assets/sensor-exploded.jpg)

传感器头部集成相机、照明、窗口与柔性触觉界面。定位和固定结构协调光学组件，外部解码板通过柔性排线连接；设计同时考虑线缆路径、装配操作空间与安装接口。

[传感器 CAD](03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/) · [STL 模型](03_Hardware/03_Print_Files_STL/README.md) · [装配与制造记录](03_Hardware/09_Manufacturing_Notes/ASSEMBLY_AND_MANUFACTURING_NOTES.md)

![相机、八 LED 照明板与排线集成](docs/assets/camera-led-integration.jpg)

*LED PCB 沿用上游设计；我的工作重点为机械安装、光学对准，以及适配后传感器的照明和布线集成。*

## 硅胶制备与样机制造

触觉界面采用 **G50 透明支撑层、G5 半透明变形层与 G25 黑色接触层**。制造流程涵盖模具准备、封边、混合脱泡、逐层浇注与固化、脱模及最终装配。

![分层硅胶制造模具与零件](docs/assets/silicone-manufacturing.jpg)

工程资料包括 **12 个 SolidWorks 原生零件、1 个 LED 板装配体、9 个 STL 和3个模具 DXF**，并提供器件照片、制造过程与物料清单。

[制造过程照片](03_Hardware/09_Manufacturing_Notes/Process_Photos/) · [模具图纸](03_Hardware/04_Engineering_Drawings/Acrylic_Mold/) · [BOM 导航](03_Hardware/BOM_INDEX.md)

## FT300 平台与机器人末端安装

![传感器与 Robotiq FT300 机械耦合平台](docs/assets/ft300-platform.jpg)

通过专用连接零件，将触觉传感器与 FT300 六维力参考设备机械耦合，为接触实验建立安装接口与载荷传递路径。仓库保留平台实物、转接 CAD 和配套采集工作流。

[FT300 转接零件](03_Hardware/01_CAD_Source/SolidWorks_Parts/Test_Connections/) · [FT300 软件配置](02_Software/Final_Repository_Snapshot/docs/06_FT300_SETUP.md)

![双指夹爪与触觉传感器安装 CAD 方案](docs/assets/gripper-cad.jpg)

*双指夹爪安装概念：左右零件与传感器布局在 CAD 阶段形成装配方案。*

[夹爪 CAD](03_Hardware/01_CAD_Source/SolidWorks_Parts/Gripper/) · [夹爪 STL](03_Hardware/03_Print_Files_STL/Existing_Source/Gripper/)

## 实验与演示

录像展示样机外观、计算环境接入、触觉按压与形貌界面响应。实验资料包括标定点选择、球形压头过程和接触形貌重建结果。

| 演示 | 入口 |
|---|---|
| 样机外观、照明与连接 | [22 秒节选](05_Demos/Previews/hardware-preview.mp4) |
| 触觉按压与形貌响应 | [28 秒节选](05_Demos/Previews/shape-preview.mp4) |
| 六轴向量界面展示 | [28 秒节选](05_Demos/Previews/vector-preview.mp4) |

打开视频文件后点击 **View raw** 或 **Download raw file** 下载观看。[视频导航](05_Demos/README.md) 提供原始录像、节选时间及说明；[技术验证记录](docs/VALIDATION_STATUS.md) 说明实验条件与软件检查。

## 工程资料与项目背景

[论文与项目报告](01_Academic/ACADEMIC_INDEX.md) · [软件](02_Software/SOFTWARE_INDEX.md) · [硬件](03_Hardware/README.md) · [标定与实验材料](04_Data_and_Models/DATA_MODEL_INDEX.md) · [演示](05_Demos/README.md)

软件文档采用 **Ubuntu 20.04 / Python 3.8 / ROS Noetic** 环境，安装与操作从 [软件导航](02_Software/SOFTWARE_INDEX.md) 进入。

本项目对应我的硕士论文 *Development of a Compact Vision-Based Tactile Sensor for Robotic End Effectors*。感谢 [9DTact 原作者](https://github.com/linchangyi1/9DTact) 提供感知方法及开源设计。上游算法、参考硬件与许可保留署名，项目适配与集成工具在源码快照中说明。软件来源 commit 为 `98ebb7da0010df27ef634f9868e557d77fa73ec5`。

[项目时间线](PROGRESS_TIMELINE.md) · [版本来源](VERSION_FREEZE.md) · [权属与致谢](docs/RIGHTS_AND_ATTRIBUTION.md) · [文件清单](SUBMISSION_MANIFEST.csv)
