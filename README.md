English · [中文](README_ZH.md)

# Compact Vision-Based Tactile Sensor for Robotic End Effectors

**Mechanical Design · Prototyping · Hardware Integration**<br>
**LIU Zhaolin | MSc Mechanical Engineering, The University of Hong Kong**

An engineering project bringing together compact sensor packaging, optical hardware, silicone fabrication and robotic mounting interfaces. Building on **9DTact**, I developed camera and enclosure adaptations, integrated illumination and internal routing, fabricated and assembled **two tactile sensor prototypes**, and built a test platform mechanically coupled to a **Robotiq FT300** six-axis force/torque sensor.

This portfolio follows the work from **CAD and component integration to physical prototypes and tactile contact demonstrations**, with engineering drawings, manufacturing records, software and experimental materials available to explore.

![Two assembled tactile sensor prototypes with flexible camera cables and external decoder boards](docs/assets/sensor-prototypes.jpg)

*Two assembled prototypes showing the printed housings, tactile interfaces, flexible camera connections and external decoder boards.*

## Explore the project

| Start here | What you can review |
|---|---|
| [Mechanical design and hardware](03_Hardware/README.md) | Sensor parts, robotic mounting concepts, FT300 adapters, PCB integration and BOMs |
| [Prototype and contact demonstrations](05_Demos/README.md) | Short video extracts, original recordings and viewing instructions |
| [Engineering contributions](docs/PROJECT_OVERVIEW.md) | Responsibilities, design methods and supporting source files |
| [Software and system integration](02_Software/SOFTWARE_INDEX.md) | Camera calibration tools, reconstruction, FT300 workflows and ROS documentation |

**Quick hardware tour:** [22-second prototype video](05_Demos/Previews/hardware-preview.mp4) · [FT300 test platform](docs/assets/ft300-platform.jpg) · [Manufacturing photo collection](03_Hardware/08_Renders_and_Photos/PHOTO_CATALOG.md)

## My engineering contributions

| Workstream | Design and implementation |
|---|---|
| **Mechanical packaging** | Adapted the sensor housing, locating features, camera retention and optical-window support around an OV5640 imaging module and external decoder board. |
| **Optical and electrical integration** | Coordinated the lens, eight-LED illumination board and tactile window; arranged the flexible cable outlet and clearances around fasteners and the mechanical load path. |
| **Fabrication and assembly** | Prepared printed components and silicone moulds; carried out sealing, mixing, vacuum degassing, layered casting, curing, demoulding and prototype assembly. |
| **Image calibration and tactile experiments** | Implemented an interactive 7 × 9 calibration-point selection tool, worked on image rectification, and carried out spherical-indenter and contact-shape reconstruction experiments. |
| **Test fixtures and robotic interfaces** | Developed mounting adapters for the FT300-coupled platform and a two-finger gripper mounting concept, supported by CAD, STL files and assembly renderings. |
| **Software and ROS integration** | Organised sensor configurations and tools for FT300 acquisition, coordinate transforms, data checks, training/inference workflows and ROS Noetic operation. |

## Sensor architecture and compact packaging

![Exploded view of the sensor housing, camera, illumination board, optical window and layered silicone interface](docs/assets/sensor-exploded.jpg)

The mechanical design brings the camera, illumination, optical window and compliant tactile interface into a compact sensor head. Locating and retention features coordinate the optical stack, while an external decoder board connects through a flexible cable. Cable routing, assembly access and the mounting interface are considered alongside the sensor's optical requirements.

[Sensor CAD parts](03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/) · [STL models](03_Hardware/03_Print_Files_STL/README.md) · [Assembly and manufacturing records](03_Hardware/09_Manufacturing_Notes/ASSEMBLY_AND_MANUFACTURING_NOTES.md)

![Camera and eight-LED board integrated with the flexible cable and decoder](docs/assets/camera-led-integration.jpg)

*Camera, illumination and cable integration. The LED PCB is reused from the upstream design; my work focuses on its mechanical placement, optical alignment and integration into the adapted sensor.*

## Silicone fabrication and prototype assembly

The tactile interface uses a layered silicone construction: a transparent **G50 support layer**, a translucent **G5 deformation layer** and a black **G25 contact layer**. The fabrication workflow covers mould preparation, seam sealing, mixing and vacuum degassing, successive casting and curing, followed by demoulding and final assembly.

![Moulds and components used in the layered silicone fabrication process](docs/assets/silicone-manufacturing.jpg)

The engineering archive includes **12 native SolidWorks part files, one LED-board assembly, nine STL files and three mould DXF files**, alongside component photographs, manufacturing records and bills of materials.

[Fabrication photographs](03_Hardware/09_Manufacturing_Notes/Process_Photos/) · [Mould drawings](03_Hardware/04_Engineering_Drawings/Acrylic_Mold/) · [BOM navigation](03_Hardware/BOM_INDEX.md)

## FT300 test platform and end-effector mounting

![Custom tactile sensor mounted on a Robotiq FT300 mechanical test platform](docs/assets/ft300-platform.jpg)

The test fixture mechanically couples the tactile sensor to a **Robotiq FT300** reference force/torque sensor. Dedicated adapter parts provide a mounting interface and load-transfer path for contact experiments. The repository includes the physical setup, connection CAD and supporting acquisition workflows.

[FT300 adapter parts](03_Hardware/01_CAD_Source/SolidWorks_Parts/Test_Connections/) · [FT300 software setup](02_Software/Final_Repository_Snapshot/docs/06_FT300_SETUP.md)

![CAD rendering of a two-finger gripper concept with tactile sensor mounting interfaces](docs/assets/gripper-cad.jpg)

*Two-finger gripper mounting concept: left/right parts and sensor placement developed at the CAD stage.*

[Gripper CAD](03_Hardware/01_CAD_Source/SolidWorks_Parts/Gripper/) · [Gripper STL files](03_Hardware/03_Print_Files_STL/Existing_Source/Gripper/)

## Experiments and demonstrations

The project records show the assembled sensor, its connection to the computing environment, and tactile contact with an accompanying shape-reconstruction display. Calibration materials include point-selection images, spherical-indenter experiments and a reconstructed contact-shape example.

| Recording | View |
|---|---|
| Prototype appearance, illumination and connections | [22-second extract](05_Demos/Previews/hardware-preview.mp4) |
| Pressing interaction and shape response | [28-second extract](05_Demos/Previews/shape-preview.mp4) |
| Six-axis vector interface demonstration | [28-second extract](05_Demos/Previews/vector-preview.mp4) |

Open a video file and select **View raw** or **Download raw file** to watch. The [demo guide](05_Demos/README.md) provides original recordings, timestamps and interpretation. [Technical validation notes](docs/VALIDATION_STATUS.md) document experiment conditions and software checks.

## Engineering archive

| Area | Contents |
|---|---|
| [Academic work](01_Academic/ACADEMIC_INDEX.md) | Dissertation, presentation, project reports and reference index |
| [Software](02_Software/SOFTWARE_INDEX.md) | Frozen source snapshot, installation and operating guides |
| [Hardware](03_Hardware/README.md) | CAD, STL, DXF, PCB, BOM, photographs and manufacturing records |
| [Calibration and experiment materials](04_Data_and_Models/DATA_MODEL_INDEX.md) | Calibration files, process images and contact-shape results |
| [Demonstrations](05_Demos/README.md) | Video covers, short extracts and original recordings |

The documented software environment is **Ubuntu 20.04 / Python 3.8 / ROS Noetic**. Start with the [installation and workflow guide](02_Software/SOFTWARE_INDEX.md).

## Project background and attribution

This portfolio presents the engineering work associated with my master's dissertation, *Development of a Compact Vision-Based Tactile Sensor for Robotic End Effectors*.

The project builds on the [9DTact sensing methods and open-source design](https://github.com/linchangyi1/9DTact). Upstream algorithms, reference hardware and licences are retained with their attribution; project-specific adaptations and integration tools are documented in the source snapshot. The software reference commit is `98ebb7da0010df27ef634f9868e557d77fa73ec5`.

[Project timeline](PROGRESS_TIMELINE.md) · [Version provenance](VERSION_FREEZE.md) · [Rights and attribution](docs/RIGHTS_AND_ATTRIBUTION.md) · [File manifest](SUBMISSION_MANIFEST.csv)
