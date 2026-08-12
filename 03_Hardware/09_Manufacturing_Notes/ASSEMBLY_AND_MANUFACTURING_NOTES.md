# Assembly and Manufacturing Notes

The authoritative assembly and fabrication description is in `01_Academic/01_Thesis/Final/Dissertation_LIU Zhaolin.pdf`, Chapter 4. The following is a navigation summary of the retained manufacturing evidence.

1. The camera, flexible cable, decoder board, and eight-LED PCB are integrated as the optical stack.
2. The enclosure provides camera seating, sensing-window support, cable clearance, and external mounting lugs.
3. The detachable mould supports staged casting of the recorded G50, G5, and G25 silicone layers.
4. Source records describe seam sealing, material mixing, vacuum degassing, casting, curing, demoulding, and final sensor assembly.
5. Each assembled sensor requires its own camera and sensor calibration records before use.

## Photograph evidence

The project photo catalog is `03_Hardware/08_Renders_and_Photos/PHOTO_CATALOG.md`. Original-to-delivery filename and SHA-256 traceability is recorded in `03_Hardware/08_Renders_and_Photos/PHOTO_SOURCE_MAPPING.csv`.

Manufacturing-process photographs are located in `03_Hardware/09_Manufacturing_Notes/Process_Photos/`:

1. `Process_Photos/printed_mold_and_housing_parts.jpg` records the printed mould and housing components.
2. `Process_Photos/mold_hot_glue_sealing.jpg` records seam sealing before casting.
3. `Process_Photos/silicone_material_preparation.jpg` and `Process_Photos/silicone_vacuum_degassing.jpg` record material preparation and degassing.
4. `Process_Photos/transparent_g50_bottom_layer.jpg`, `Process_Photos/translucent_g5_middle_layer.jpg`, and `Process_Photos/black_g25_top_layer.jpg` document the three recorded cured silicone layers.
5. `Process_Photos/multi_layer_casting_molds.jpg` records two assembled multi-layer moulds.

Assembly and integration evidence is located at:

- `03_Hardware/08_Renders_and_Photos/Completed_Hardware/completed_dual_custom_sensors.jpg`
- `03_Hardware/08_Renders_and_Photos/Assembly_and_Design/sensor_exploded_view_annotated.jpg`
- `03_Hardware/08_Renders_and_Photos/Assembly_and_Design/custom_gripper_assembly_render.png`
- `03_Hardware/08_Renders_and_Photos/Test_Setups/sensor_ft300_calibration_fixture.jpg`
- `03_Hardware/08_Renders_and_Photos/Test_Setups/benchtop_sensor_test_fixture.jpg`
- `03_Hardware/08_Renders_and_Photos/Test_Setups/screw_loading_sensor_test.jpg`

These photographs document the project's hardware integration and multi-stage manufacturing process.

## Seven supplied STL exports

The following seven binary STL files are present and structurally readable. Each is paired by base name with its preserved SolidWorks part; the STL files are delivery exports, while the `.SLDPRT` files remain the editable design sources.

| Native SolidWorks part | Supplied STL export |
|---|---|
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Calibration/calibration_board.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Calibration/calibration_board.STL` |
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/acrylic_window.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Optimized_Sensor/acrylic_window.STL` |
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/isolation_ring.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Optimized_Sensor/isolation_ring.STL` |
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/sensor_base.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Optimized_Sensor/sensor_base.STL` |
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Optimized_Sensor/sensor_shell_optimized.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Optimized_Sensor/sensor_shell_optimized.STL` |
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Test_Connections/FT300_connection base.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Test_Connections/FT300_connection base.STL` |
| `03_Hardware/01_CAD_Source/SolidWorks_Parts/Test_Connections/sensor_connection base.SLDPRT` | `03_Hardware/03_Print_Files_STL/Converted/SolidWorks_Parts/Test_Connections/sensor_connection base.STL` |

Before fabrication, use the native SolidWorks geometry, project BOM, intended printer/material settings, and the actual mating hardware to confirm scale, orientation, support strategy, hole clearances, and fit. The original thesis figures and unmodified CAD/BOM files are the design authority.
