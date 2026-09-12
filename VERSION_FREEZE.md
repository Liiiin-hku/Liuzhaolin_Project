# 版本来源与作品集整理版本

## 两层版本身份

- 本仓库：`Liiiin-hku/Liuzhaolin_Project`，默认分支 `main`。
- 原始外层交接提交：`3d3de84763bf30712eb6fb94a00f48f3ecc1210e`。
- 2026-09-12 外层历史按公开展示范围定向整理，提交 SHA 已改变；上述标识仅用于原始交接版本追溯，不代表当前可达提交。软件来源 commit 不变。
- 作品集整理日期：2026-09-11；外层文档与展示资源版本 `portfolio-2026-09-11`（文档版本名，不是 Git tag）。
- 招聘阅读入口更新：2026-09-12；外层展示文档版本 `portfolio-2026-09-12`。硬件和冻结软件内容不变。
- 当前外层文件清单：[SUBMISSION_MANIFEST.csv](SUBMISSION_MANIFEST.csv)。该清单记录当前工作树的实际文件大小和 SHA-256，LFS 视频按完整文件计算。

新版资料包不与原教师交接包逐字节相同；旧 ZIP 与旧校验值不适用于此版本。本次不创建新的交接压缩包。

## 冻结软件来源

- [本仓库完整软件快照](02_Software/Final_Repository_Snapshot/)
- [来源仓库固定提交](https://github.com/Liiiin-hku/9DTact_FT300_Custom_Sensor_Project/commit/98ebb7da0010df27ef634f9868e557d77fa73ec5)
- 来源分支：`submission/final-sensor-code`；commit：`98ebb7da0010df27ef634f9868e557d77fa73ec5`。
- 来源 Git tree：`445e66e20cff0a31f2e4b0d39f1afa5cca17cdbb`。
- 本资料包冻结子树：`be4d19e64ce433d0b2a6341ba59b7a797d27c7bf`，共 297 个文件，其中 `Original/` 为 138 个文件。

2026-09-11 只读比对来源仓库固定提交：297 个路径一致，206 个文件的 Git blob 完全相同，90 个文件仅有已存在的 CRLF/LF 差异；快照内 `SUBMISSION_MANIFEST.csv` 的 296 条路径一致，其中 90 行的 size/SHA-256 对应这些换行差异。因此原外层文档中“与远端 commit 逐字节一致”的说法不准确。

本次**没有修改冻结子树中的任何文件**，也没有为了统一换行改写 `Original/`。代码与配置的来源可追溯，但应按上述字节差异理解。[比对清单](docs/SOFTWARE_SOURCE_COMPARISON.csv) · [Original 冻结清单](02_Software/Repository_Version_Info/ORIGINAL_FROZEN_SHA256.csv)

## 论文、硬件与数据

| 资产 | 当前文件与完整性 |
|---|---|
| 论文展示 PDF | [39 页 PDF](01_Academic/01_Thesis/Final/Dissertation_LIU%20Zhaolin.pdf)；SHA-256 `e578ed6644dbb0c75e4d61198f1136a02b066b1e5bdf333bc7f49ba4ea824379` |
| 原始答辩 PDF/PPTX | [答辩资料](01_Academic/03_Defense/Final/)；本次保持文件字节不变 |
| 阶段报告展示范围 | [阶段导航](01_Academic/02_Stage_Reports/README.md)；早期两轮调研改留摘要，两份后续 PDF 定点省略第三方引用图，修改与哈希见 [映射](01_Academic/REPORT_DISPLAY_EDITS.csv) |
| CAD、STL、DXF、PCB、BOM | [硬件导航](03_Hardware/README.md)；原始工程文件和引用路径不变 |
| 相机与深度数组 | 仍在冻结快照内，活动状态见 [验证说明](docs/VALIDATION_STATUS.md) |
| 原始图片及三个视频 | 原路径和文件字节不变；展示副本有独立来源映射 |
| 第三方全文 | 仅保留明确声明再分发许可的两份 CC BY PDF 与上游项目记录；完整书目见 [文献库](01_Academic/04_Reference_Library/REFERENCE_LIBRARY_INDEX.md) |

论文展示 PDF 移除封面学号和 PDF 元数据，39 页渲染比较仅第 1 页对应区域不同。可编辑原论文和教师评审表不在当前展示版本。

## 维护与验证

外层变更后更新根清单，排除 `.git`、缓存、临时文件、私有资料及清单自身，不覆盖软件内部原始清单。软件变更必须单独记录来源与验证，不能继续宣称快照未变。

[维护记录](docs/MAINTENANCE.md) · [技术验证](docs/VALIDATION_STATUS.md) · [许可与来源](docs/RIGHTS_AND_ATTRIBUTION.md)
