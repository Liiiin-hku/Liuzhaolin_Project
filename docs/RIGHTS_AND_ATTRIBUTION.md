# 许可与素材来源

[返回首页](../README.md)

本仓库用于工程成果展示。公开可读不自动赋予全部材料商业使用、改编或再分发许可；已有明确许可的资产继续按其原条款使用。

| 资产范围 | 来源与适用范围 |
|---|---|
| 冻结软件与 `Original/` | 保留 [软件 LICENSE](../02_Software/Final_Repository_Snapshot/LICENSE)、[NOTICE](../02_Software/Final_Repository_Snapshot/NOTICE.md) 和 [Original/LICENSE](../02_Software/Final_Repository_Snapshot/Original/LICENSE)。不修改原作者声明，不将其扩展为外层全部资料的统一许可 |
| 上游设计及其外层副本 | 通过 [HARDWARE_PROVENANCE](HARDWARE_PROVENANCE.csv) 识别精确匹配；保留上游来源及已有适用许可，不以复制位置改变原有权利 |
| 本项目定制 CAD、制造与实验照片、展示文档 | 用于查看个人工程工作；本次未另行授予统一开源或商业使用许可。涉及合作或机构权利时，进一步使用须与相应权利人确认 |
| PCB 与厂商器件资料 | PCB 源工程、Gerber ZIP、BOM 与贴片坐标具有上游复用关系。厂商标识属于相应权利人，FT300 手册提供官方链接 |
| 论文和答辩 | 保留必要学术署名与引文；论文展示 PDF 移除学号，技术正文不变。文内第三方图表的引文不等于对其另行授予许可，复用时需回查原来源 |
| 文献全文 | 仅保留 PDF 本身明确声明 CC BY 的 REF_10 和 REF_15，以及官方 9DTact 项目记录及其 LICENSE；其余文献使用书目信息、DOI 与官方链接 |
| 展示图片和视频节选 | 来自现存项目图片与录像，来源、处理和哈希见 [图片映射](assets/IMAGE_SOURCES.json) 与 [视频节选映射](../05_Demos/Previews/PREVIEW_SOURCES.json)。不含本次生成式实物或性能曲线 |

## 上游致谢

9DTact: A Compact Vision-Based Tactile Sensor for Accurate 3D Shape Reconstruction and Generalizable 6D Force Estimation，Changyi Lin、Han Zhang、Jikai Xu、Lei Wu、Huazhe Xu。[上游项目](https://github.com/linchangyi1/9DTact) · [DOI](https://doi.org/10.1109/LRA.2023.3339397)

本项目保留其感知原理、算法与参考工程，个人结构适配、制造和集成见 [贡献说明](PROJECT_OVERVIEW.md)。本次没有给整个资料包添加 MIT 或其他统一许可。

## 保留的开放文献

- Wenzhen Yuan, Siyuan Dong, Edward H. Adelson. *GelSight: High-Resolution Robot Tactile Sensors for Estimating Geometry and Force.* Sensors 17(12), 2762 (2017). [DOI](https://doi.org/10.3390/s17122762)。PDF 明确声明 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，保留完整未修改文件和原署名。
- Benjamin Ward-Cherrier et al. *The TacTip Family: Soft Optical Tactile Sensors with 3D-Printed Biomimetic Morphologies.* Soft Robotics 5(2), 216–227 (2018). [DOI](https://doi.org/10.1089/soro.2017.0052)。所保留出版 PDF 的机构封面标为 CC BY，文中说明允许署名后的分发与复制；保留原许可、署名与未修改文件，具体使用遵循该 PDF 的原声明。

逐项入口见 [文献库](../01_Academic/04_Reference_Library/REFERENCE_LIBRARY_INDEX.md)。源站可下载、开放获取标签和再分发许可是不同事项；尚未明确再分发权利的全文不包含在当前展示版本。

## 阶段报告中的引用媒体

2025 年两轮调研报告改为 [技术摘要与来源入口](../01_Academic/02_Stage_Reports/README.md)，原 PDF/PPTX 中未确认许可的第三方产品图、他人演示及嵌入媒体不随当前版本分发。2026 年 1 月和 2 月展示 PDF 分别省略一处第三方机器人照片及一页厂商产品图，页内注明处理，技术实验记录保留；[映射](../01_Academic/REPORT_DISPLAY_EDITS.csv) 标明修改页和哈希。

保留报告中的 9DTact 原结构图、管线图、混合通道图和论文 Figure 2.1 可与冻结快照 `Original/source/` 下的原作者图像和海报对应。它们是上游关联文档，沿用同目录项目保留的 MIT 许可和作者信息；其原论文中的测试结果不能当成本项目结果。
