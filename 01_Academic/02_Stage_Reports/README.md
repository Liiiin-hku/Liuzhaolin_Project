# 阶段记录与早期方案摘要

[学术资料导航](../ACADEMIC_INDEX.md) · [当前贡献与验证边界](../../docs/VALIDATION_STATUS.md)

## 2025 年 10–11 月：方案调研

早期工作比较了触觉感知、机器人手控制与上层策略的方案，考虑过磁流体触觉传感器及 BiDexHand/VR 集成路线。进一步调研发现，多材料制备、液体密封和环境磁场会增加磁流体方案的实施难度，因此转向具有公开制造资料的 9DTact 路线。

这部分是**技术选型和方案学习**，没有在本项目中完成 BiDexHand、VR 遥操作或强化学习控制的实现。早期报告中的参考性能数字也不代表本项目测量结果。

原 2025.10.5 和 2025.11.2 的 PDF/PPTX 含第三方产品图、他人演示和嵌入媒体，当前展示版本保留本摘要与来源链接。原始材料未作为本项目工程证据重新包装。

- [9DTact 原作者项目与制造资料](https://linchangyi1.github.io/9DTact/)
- [BiDexHand 原项目](https://github.com/wengmister/BiDexHand)
- [本仓库文献索引](../04_Reference_Library/REFERENCE_LIBRARY_INDEX.md)

## 后续制造与实验记录

| 阶段 | 可查看文件 | 阅读边界 |
|---|---|---|
| 2026-01 初始制造与环境搭建 | [11 页报告](2026.1.18.pdf) | 记录早期样机、环境流程和代码截图；第 8 页省略第三方机器人照片 |
| 2026-02 图像与向量工作流 | [14 页报告](2026.2.1.pdf) | 展示定性界面响应及后续训练需求；第 13 页省略厂商宣传图片，不把向量画面当精度证明 |
| 2026-04 夹爪设计与后续计划 | [11 页中期报告](interm%20report.pdf) · [源文件](Interim%20Report.pptx) | 夹爪 CAD 和控制方案属于设计阶段，计划内容不等于完成抓取验证 |
| 2026-07 样机制造和 FT300 平台 | [8 页后期报告](2026.7.19.pdf) · [源文件](2026.7.19.pptx) | 有制造、装配及平台实物；同期列出的数据集、训练和验证工作仍需独立证据 |

两份展示 PDF 的修改页和 SHA-256 记录在 [展示修改映射](../REPORT_DISPLAY_EDITS.csv)。未编辑页面与原件的逐页渲染一致，页数和页码不变。图片省略处有明确文字说明。

## 上游图像归属

报告中的原版结构图、形貌与力估计管线、混合通道原理属于 9DTact 原作者。可核对 [原结构图](../../02_Software/Final_Repository_Snapshot/Original/source/design.jpeg)、[管线图](../../02_Software/Final_Repository_Snapshot/Original/source/pipelie.png)、[原项目海报](../../02_Software/Final_Repository_Snapshot/Original/source/Poster.png) 与 [保留的 MIT 许可](../../02_Software/Final_Repository_Snapshot/Original/LICENSE)。上游公开指标不能引用为本项目性能。
