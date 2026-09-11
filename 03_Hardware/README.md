# 结构设计、样机与硬件资料

[返回首页](../README.md) · [个人贡献证据](../docs/PROJECT_OVERVIEW.md)

这里展示从结构适配到实物制造的工程材料。原始 CAD、装配体、PCB、BOM 和制造照片保持原路径；展示图片是压缩副本。

![传感器结构爆炸图](../docs/assets/sensor-exploded.jpg)

## 先看结构和实物

| 主题 | 工程入口 | 可直接浏览的证据 |
|---|---|---|
| 外壳、基座、窗口和隔离环 | [Optimized_Sensor](01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/) | [双传感器成品](08_Renders_and_Photos/Completed_Hardware/completed_dual_custom_sensors.jpg) |
| FT300 与传感器连接基座 | [Test_Connections](01_CAD_Source/SolidWorks_Parts/Test_Connections/) | [FT300 耦合平台](08_Renders_and_Photos/Test_Setups/sensor_ft300_calibration_fixture.jpg) |
| 双指夹爪安装方案 | [左右夹爪 CAD](01_CAD_Source/SolidWorks_Parts/Gripper/) | [装配渲染](08_Renders_and_Photos/Assembly_and_Design/custom_gripper_assembly_render.png) |
| 3D 打印交付 | [9 个 STL 与映射](03_Print_Files_STL/README.md) | [打印件照片](09_Manufacturing_Notes/Process_Photos/printed_mold_and_housing_parts.jpg) |
| 分层浇注模具 | [3 个亚克力 DXF](04_Engineering_Drawings/Acrylic_Mold/) | [模具及硅胶制造记录](09_Manufacturing_Notes/ASSEMBLY_AND_MANUFACTURING_NOTES.md) |

原生 SolidWorks 为 **12 个零件和 1 个 LED 板装配体**，不等同于完整的自定义传感器或夹爪装配工程。STL 为 9 个，其中 7 个为转换交付、2 个为既有夹爪 STL。本次未执行 SolidWorks 打开、重建、单位或装配引用检查；没有重命名或移动 CAD。

## PCB、照明和 BOM

- [PCB 工程、Gerber、贴片坐标与电子照片](07_PCB_and_Electronics/ELECTRONICS_INDEX.md)
- [主 BOM 与电子 BOM](BOM_INDEX.md)：主表 38 行材料/采购条目；电子表 4 行器件类型；贴片表 11 个位置。
- [电子实物：相机、LED 板、排线与解码板](07_PCB_and_Electronics/Photos/sensor_electronics_components.jpg)

主 BOM 用于器件和制造资料定位，采购单价与汇总并不代表单个样机的物料成本。保留的 PCB 工程、Gerber ZIP、电子 BOM 与贴片表与上游快照相同；个人工作按照明安装和硬件集成说明。[文件来源核对](../docs/HARDWARE_PROVENANCE.csv)

## 制造与装配

从 [制造记录](09_Manufacturing_Notes/ASSEMBLY_AND_MANUFACTURING_NOTES.md) 查看模具封边、混合脱泡、分层浇注、固化脱模和装配过程。完整 [图片目录](08_Renders_and_Photos/PHOTO_CATALOG.md) 与 [来源映射](08_Renders_and_Photos/PHOTO_SOURCE_MAPPING.csv) 保留原图线索。

仍缺与最终 CAD/BOM 逐项对应并经复核的装配步骤、完整端到端接线图及统一供电范围说明。实际制造前需要核实尺寸、孔隙配合、极性与电源条件；这些限制详见 [验证状态](../docs/VALIDATION_STATUS.md)。
