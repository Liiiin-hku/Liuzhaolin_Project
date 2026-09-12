English · [中文](README.md)

# Compact Vision-Based Tactile Sensor: Mechanical Design and Hardware Integration

**LIU Zhaolin | MSc Mechanical Engineering graduation project, The University of Hong Kong**

This project adapts the open-source **9DTact** sensing principle to a different camera and mechanical package. My work covers camera mounting, enclosure design, illumination integration, cable clearance, silicone fabrication and prototype assembly. Two sensors were assembled, and a mechanical test platform couples a custom sensor to a **Robotiq FT300** force/torque sensor.

![Two assembled tactile sensor prototypes with flex cables and external decoder boards](docs/assets/sensor-prototypes.jpg)

**Start with the hardware:** [22-second prototype video](05_Demos/Previews/hardware-preview.mp4) · [FT300 coupling platform](docs/assets/ft300-platform.jpg) · [Design and assembly evidence](03_Hardware/README.md)

## Quick links

| Review interest | Entry point |
|---|---|
| Mechanical design, CAD, electronics and fabrication | [Hardware portfolio](03_Hardware/README.md) |
| Physical prototypes and interaction | [Three demonstrations and viewing guide](05_Demos/README.md) |
| Responsibilities and supporting files | [Project overview and contribution evidence](docs/PROJECT_OVERVIEW.md) |
| Software reproduction | [Installation and workflow navigation](02_Software/SOFTWARE_INDEX.md) |

For mechanical design and hardware integration reviews, follow **hardware portfolio → contribution evidence → demonstrations and validation status**. Retained outputs include **two physical prototypes, 12 native part files and one LED-board assembly, nine STL files and three mould DXF files**. Source files, photographs and attribution can be cross-checked. These file counts do not establish a complete assembly package; see the hardware guide for the exact scope.

## My engineering work

- **Compact packaging and camera adaptation:** integrate an OV5640 camera with an external decoder; adapt the enclosure, locating features, retention, window support and cable outlet to the new imaging chain.
- **Illumination and cable integration:** align the camera with the eight-LED board and tactile window; provide flex-cable clearance around fasteners and outside the principal load path.
- **Fabrication and assembly:** prepare printed parts and detachable moulds, seal seams, mix and vacuum-degas silicone, cast and cure successive layers, demould and assemble two prototypes.
- **Calibration and experimental integration:** implement manual 7 × 9 control-point selection to handle distortion and vignetting; carry out image rectification and qualitative shape experiments; design adapters for the FT300 platform.
- **Software workflow:** organise sensor configuration, FT300 acquisition, dataset checks, training/inference entry points and ROS Noetic integration around the upstream methods. Implemented code is distinguished from demonstrated or quantitatively validated performance.

**Attribution boundary:** 9DTact methods and `Original/` belong to the upstream authors. The retained LED PCB project, Gerber ZIP, electronics BOM and placement workbook are byte-identical to files in the upstream snapshot. They support my mounting and illumination integration work; they do not establish an independently authored circuit design.

## Design and integration evidence

![Exploded view of the sensor optical and mechanical stack](docs/assets/sensor-exploded.jpg)

The sensor head contains the camera, centred illumination, window and tactile interface. The decoder remains accessible outside the housing. The design coordinates locating surfaces, retention, fastener access and cable clearance. See the [custom sensor parts](03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/) and [manufacturing record](03_Hardware/09_Manufacturing_Notes/ASSEMBLY_AND_MANUFACTURING_NOTES.md).

![Camera, LED board, flex cable and external decoder](docs/assets/camera-led-integration.jpg)

The portfolio uses **compact structural adaptation**, without a 30% volume-reduction claim. A consistent baseline, modified assembly envelope and calculation are missing. The approximate 42 × 38 × 34 mm stated in the defense is a design description, not a CAD measurement or complete-system volume verification performed for this portfolio.

## Fabrication and experimental platform

The fabrication record covers the transparent G50 support layer, translucent G5 deformation layer and black G25 contact layer. Photographs document mould sealing, mixing, degassing, staged casting, curing and assembly; they are not material-property or lifetime tests.

![Detachable moulds used for staged silicone fabrication](docs/assets/silicone-manufacturing.jpg)

![Custom sensor mechanically coupled to Robotiq FT300](docs/assets/ft300-platform.jpg)

The FT300 and sensor adapter parts are retained in [Test_Connections](03_Hardware/01_CAD_Source/SolidWorks_Parts/Test_Connections/). A two-finger gripper integration concept is supported by left/right CAD and STL parts and an assembly rendering. Physical grasping and tactile closed-loop control are not established by the current records. The proposed identification as the Fangzhou Wuxian R5 is not yet supported by a traceable model or manufacturer reference.

![Two-finger gripper integration CAD rendering; design concept only](docs/assets/gripper-cad.jpg)

## Demonstrations and validation

The [demo guide](05_Demos/README.md) presents hardware, pressing/shape response and six-axis vector visualisation recordings. The vector video's model, signal source, physical units and sensor identity lack a complete session record. It cannot establish whether the display represents FT300 measurements or tactile-model predictions, or demonstrate prediction accuracy.

Manual point selection, rectification, spherical-indenter work and qualitative screw reconstruction have retained evidence. In the current frozen software, Sensor 1 and Sensor 2 share identical core camera arrays and both active depth LUTs match the upstream LUT. Historical experiment descriptions must be distinguished from the active packaged files.

| Scope | Evidence and boundary |
|---|---|
| Two prototypes, fabrication and FT300 platform | CAD, process photographs, physical hardware and qualitative demonstrations |
| Rectification and shape reconstruction | Scripts, arrays, process images and qualitative results; no independent error evaluation |
| FT300 zeroing, frame transforms and synchronisation | Implemented code and offline tests; frozen real acquisition-session logs are missing |
| Custom image-to-six-axis force mapping | Training and inference code; no curated paired training dataset, formal checkpoint or independent accuracy results |
| Gripper integration | CAD/STL and rendering; physical grasping validation is not established |

On **2026-09-11**, **30 offline tests and the frozen software's static submission check passed on Windows / Python 3.12**. This run did not operate Ubuntu/ROS hardware, a camera, FT300, model training or a SolidWorks rebuild. See [validation status](docs/VALIDATION_STATUS.md).

## Repository navigation

| Area | Contents |
|---|---|
| [01_Academic](01_Academic/ACADEMIC_INDEX.md) | Display dissertation PDF, defense, stage records and 33 bibliography entries |
| [02_Software](02_Software/SOFTWARE_INDEX.md) | Complete frozen software snapshot available in this repository |
| [03_Hardware](03_Hardware/README.md) | CAD, STL, DXF, PCB, BOM, photographs and manufacturing records |
| [04_Data_and_Models](04_Data_and_Models/DATA_MODEL_INDEX.md) | Calibration inventories, process images, shape result and collection protocol |
| [05_Demos](05_Demos/README.md) | Video covers, viewing links and interpretation |

[Timeline](PROGRESS_TIMELINE.md) · [Version provenance](VERSION_FREEZE.md) · [File manifest](SUBMISSION_MANIFEST.csv) · [Archived technical handover](docs/archive/HANDOVER.md)

## Reproduction and attribution

Start with the [software guide](02_Software/SOFTWARE_INDEX.md), which links to real installation and operating documents inside the snapshot. The documented baseline is Ubuntu 20.04, Python 3.8 and ROS Noetic. Run one sensor at a time and keep configurations, calibration, datasets and models associated with their sensor.

Credit goes to the [9DTact authors and upstream project](https://github.com/linchangyi1/9DTact). The software source is fixed at related-repository commit `98ebb7da0010df27ef634f9868e557d77fa73ec5`. The portfolio revision changes the outer presentation while preserving the frozen software. The original handover snapshot has documented line-ending and manifest differences from the remote commit; see [version provenance](VERSION_FREEZE.md).

[Rights and attribution](docs/RIGHTS_AND_ATTRIBUTION.md) distinguish software, CAD/PCB, photos, dissertation and third-party papers. No new blanket open-source licence is applied to this portfolio; existing upstream licences and credits remain effective.
