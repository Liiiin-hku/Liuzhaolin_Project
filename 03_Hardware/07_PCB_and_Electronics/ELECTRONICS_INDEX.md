# PCB and Electronics Index

## Retained engineering assets

| Asset | Path | Contents |
|---|---|---|
| EasyEDA Pro project | `LED_PCB/Source_Project/9DTact_LED_ProEAD.epro` | Schematic and PCB source archive |
| Gerber and drill set | `LED_PCB/Gerber/` | Copper, solder-mask, silkscreen, outline, and drill files |
| Original Gerber ZIP | `LED_PCB/Gerber_Archive/Gerber_LED-PCB_.zip` | Manufacturing archive |
| Electronics BOM | `../05_BOM/Electronics/BOM_LED-PCB.xlsx` | Four component rows |
| Pick-and-place | `LED_PCB/Assembly_Data/PickAndPlace_LED-PCB.xlsx` | Eleven placement rows |
| Hardware photographs | `Photos/` | LED PCB and camera/illumination assemblies |

## System integration

The custom sensor combines the OV5640 USB camera/decoder, LED illumination PCB, optical/acrylic components, and multilayer elastomer structure. The Robotiq FT300 is mounted in the test setup as the six-axis force/torque label and comparison device. The Ubuntu software consumes a parameterized `geometry_msgs/WrenchStamped` topic from the laboratory FT300 driver.

Before powering or rewiring hardware, verify voltage, current, polarity, connector orientation, and current limiting against the actual laboratory assembly and component documentation.
