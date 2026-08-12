# Hardware Asset Index

## Completed hardware collection

- 13 native SolidWorks files: 12 parts and one LED-board assembly.
- Nine STL files: seven custom/calibration/connection parts and two gripper parts.
- Three acrylic-mould DXF drawings.
- Project master BOM with 38 procurement/material rows.
- LED PCB electronics BOM with four component rows.
- EasyEDA Pro PCB source, Gerber/drill archive, and 11-row pick-and-place workbook.
- Twenty-four cataloged project images covering completed sensors, electronics, fixtures, moulding, assembly, and manufacturing.
- Manufacturing and assembly notes covering silicone preparation, mould sealing, casting, curing, and vacuum degassing.

## Native CAD

- SolidWorks sources: `01_CAD_Source/`
- Custom/calibration/connection STL files: `03_Print_Files_STL/Converted/SolidWorks_Parts/`
- Existing gripper STL files: `03_Print_Files_STL/Existing_Source/Gripper/`
- STL-to-SolidWorks mapping and structural checks: `03_Print_Files_STL/STL_SOURCE_MAPPING.csv`
- Acrylic-mould drawings: `04_Engineering_Drawings/Acrylic_Mold/`

All seven supplied custom STL files pass binary structure, finite-coordinate, non-degenerate, single-component, and closed 2-manifold checks. STL files do not encode units, so manufacturing scale and tolerances should be confirmed against the native CAD before printing.

## BOM and electronics

- Project BOM: `05_BOM/Mechanical/Project_Master_BOM.xlsx`
- Electronics BOM: `05_BOM/Electronics/BOM_LED-PCB.xlsx`
- BOM summary: `BOM_INDEX.md`
- EasyEDA project: `07_PCB_and_Electronics/LED_PCB/Source_Project/9DTact_LED_ProEAD.epro`
- Gerber/drill data: `07_PCB_and_Electronics/LED_PCB/Gerber/`
- Pick-and-place: `07_PCB_and_Electronics/LED_PCB/Assembly_Data/PickAndPlace_LED-PCB.xlsx`
- Electronics index: `07_PCB_and_Electronics/ELECTRONICS_INDEX.md`

## Photographs and manufacturing record

- Photo catalog: `08_Renders_and_Photos/PHOTO_CATALOG.md`
- Photo source mapping: `08_Renders_and_Photos/PHOTO_SOURCE_MAPPING.csv`
- Completed dual sensors: `08_Renders_and_Photos/Completed_Hardware/completed_dual_custom_sensors.jpg`
- Sensor exploded view: `08_Renders_and_Photos/Assembly_and_Design/sensor_exploded_view_annotated.jpg`
- FT300 and benchtop fixtures: `08_Renders_and_Photos/Test_Setups/`
- LED PCB/camera photographs: `07_PCB_and_Electronics/Photos/`
- Process photographs: `09_Manufacturing_Notes/Process_Photos/`
- Assembly/manufacturing notes: `09_Manufacturing_Notes/ASSEMBLY_AND_MANUFACTURING_NOTES.md`
