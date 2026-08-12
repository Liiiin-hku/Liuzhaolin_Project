cmake_minimum_required(VERSION 3.0.2)
project(nine_dtact_ft300_ros)

find_package(catkin REQUIRED COMPONENTS
  cv_bridge
  geometry_msgs
  message_filters
  ros_numpy
  rospy
  sensor_msgs
  std_msgs
  std_srvs
)

catkin_package(
  CATKIN_DEPENDS cv_bridge geometry_msgs message_filters ros_numpy rospy sensor_msgs std_msgs std_srvs
)

catkin_install_python(PROGRAMS
  scripts/repository_runner.py
  scripts/sensor_node.py
  scripts/ft300_data_collector_node.py
  scripts/shape_reconstruction_node.py
  scripts/force_estimation_node.py
  scripts/shape_force_node.py
  scripts/wrench_comparison_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY config launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
