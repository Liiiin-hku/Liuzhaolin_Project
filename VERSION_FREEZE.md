# Version Freeze

## Package identity

- Project: 9DTact + Robotiq FT300 Custom Tactile Sensor Project
- Showcase cleanup date: 2026-08-13 (Asia/Singapore)
- Final handover root: `<DESKTOP>/Liuzhaolin_Project`
- Inventory: `SUBMISSION_MANIFEST.csv`
- Archive: `<DESKTOP>/Liuzhaolin_Project.zip`
- Archive checksum: `<DESKTOP>/Liuzhaolin_Project_SHA256.txt`

## Authoritative software

- Snapshot: `02_Software/Final_Repository_Snapshot/`
- Public repository: `https://github.com/Liiiin-hku/9DTact_FT300_Custom_Sensor_Project`
- Default/frozen branch: `submission/final-sensor-code`
- Commit: `98ebb7da0010df27ef634f9868e557d77fa73ec5`
- Commit subject: `finalize: complete 9DTact FT300 graduation project package`
- Release tag: No release tag available
- Submodules: 0
- Git LFS files: 0
- Upstream `Original/`: 138 files with retained SHA-256 inventory

The code snapshot is kept byte-for-byte consistent with the public frozen commit.

## Authoritative academic deliverables

| Asset | Path | SHA-256 |
|---|---|---|
| Final dissertation source | `01_Academic/01_Thesis/Final/Dissertation_LIU Zhaolin.docx` | `5ebdf27357be616c875c912429c64ba284421323a752e388116574b4b2b3638b` |
| Final dissertation render | `01_Academic/01_Thesis/Final/Dissertation_LIU Zhaolin.pdf` | `c45d84d223785a19720dac332483fbd8703991d900d34abbf0db85b455a5a383` |
| Final defense source | `01_Academic/03_Defense/Final/Final Report.pptx` | `f21215fa9b5e4d21655561fd0f3648784c1a601207017a9dadc642526f2709f2` |
| Final defense PDF | `01_Academic/03_Defense/Final/final report.pdf` | `a1eab9b8abe9879b5d29b1fd3d2019286bbb90eb983ae97e23049ed3bedb468c` |

The compact package retains six stage/progress PDFs and four editable stage/interim decks. Related project videos are independently indexed under `05_Demos/`.

## Authoritative hardware and electronics

- Native SolidWorks sources: `03_Hardware/01_CAD_Source/`
- STL authority and source mapping: `03_Hardware/03_Print_Files_STL/`
- Project BOM: `03_Hardware/05_BOM/Mechanical/Project_Master_BOM.xlsx`
- Electronics BOM: `03_Hardware/05_BOM/Electronics/BOM_LED-PCB.xlsx`
- PCB/Gerber/placement data: `03_Hardware/07_PCB_and_Electronics/`
- Project photographs: `03_Hardware/08_Renders_and_Photos/`
- Manufacturing record: `03_Hardware/09_Manufacturing_Notes/`

## Authoritative calibration and demonstrations

- Active Sensor 1/Sensor 2 calibration: frozen software snapshot under `custom_9dtact/shape_reconstruction/calibration/`.
- Hybrid depth-LUT SHA-256: `19c9f3514dce402d8e710079757394b5445b74e7afbdd2459de43798676cb4ff` for the upstream source and both active targets.
- Calibration evidence: `04_Data_and_Models/02_Calibration_Data/`.
- Shape Reconstruction result: `04_Data_and_Models/03_Processed_Data/Shape_Reconstruction_Results/`.
- Three successful qualitative demonstrations: `05_Demos/Successful/`.

## Change control

Any content change requires regeneration of `SUBMISSION_MANIFEST.csv`, the ZIP archive, and its detached SHA-256 file. Any software change requires a new Git commit identity rather than continued use of the frozen commit above.
