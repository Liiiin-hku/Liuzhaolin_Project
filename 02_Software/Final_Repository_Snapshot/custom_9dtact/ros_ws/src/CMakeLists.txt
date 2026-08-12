cmake_minimum_required(VERSION 3.0.2)
project(Project)

# Standard catkin workspace toplevel file. This keeps a fresh checkout ready for
# `catkin_make` without requiring `catkin_init_workspace src` first.
set(CATKIN_TOPLEVEL TRUE)

set(_cmd "catkin_find_pkg" "catkin" "${CMAKE_SOURCE_DIR}")
execute_process(
  COMMAND ${_cmd}
  RESULT_VARIABLE _res
  OUTPUT_VARIABLE _out
  ERROR_VARIABLE _err
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_STRIP_TRAILING_WHITESPACE
)

if(NOT _res EQUAL 0 AND NOT _res EQUAL 2)
  string(REPLACE ";" " " _cmd_str "${_cmd}")
  message(FATAL_ERROR "Search for catkin in workspace failed (${_cmd_str}): ${_err}")
endif()

if(_res EQUAL 0)
  set(catkin_EXTRAS_DIR "${CMAKE_SOURCE_DIR}/${_out}/cmake")
  include(${catkin_EXTRAS_DIR}/all.cmake NO_POLICY_SCOPE)
  add_subdirectory("${_out}")
else()
  set(CATKIN_TOPLEVEL_FIND_PACKAGE TRUE)
  find_package(catkin QUIET NO_POLICY_SCOPE)
  if(NOT catkin_FOUND)
    message(FATAL_ERROR
      "catkin was not found. Source /opt/ros/noetic/setup.bash before running catkin_make."
    )
  endif()
endif()

catkin_workspace()
