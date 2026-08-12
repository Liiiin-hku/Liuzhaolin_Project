# Legacy BOTA Data Collector

`collect_data_bota_legacy.py` is retained only to document the upstream
MiniONE/rokubimini acquisition path. It is not installed by the catkin package,
not imported by active code, and not used by the FT300 workflow.

Use `custom_9dtact/data_collection/collect_data_ft300.py` for current data
collection. The active collector accepts a configurable
`geometry_msgs/WrenchStamped` topic from an external FT300 driver.

The legacy script requires the external `rokubimini_msgs` package and its
device-specific reset service. No validation or hardware result is claimed for
that archived workflow.
