#!/usr/bin/env bash
# Install the core 9DTact environment on Ubuntu 20.04 with ROS Noetic.
# This script performs software installation and static import checks only.

set -Eeuo pipefail

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

info() {
  printf '\n==> %s\n' "$*"
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
CUSTOM_ROOT="${REPOSITORY_ROOT}/custom_9dtact"
VENV_ROOT="${CUSTOM_ROOT}/.venv"
ROS_SETUP="/opt/ros/noetic/setup.bash"

[[ -f /etc/os-release ]] || die 'Cannot identify the operating system.'
# shellcheck disable=SC1091
source /etc/os-release
[[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "20.04" ]] || \
  die "Expected Ubuntu 20.04; found ${PRETTY_NAME:-unknown system}."

command -v python3 >/dev/null 2>&1 || die 'python3 is not installed.'
PYTHON_VERSION="$(python3 -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')"
[[ "${PYTHON_VERSION}" == "3.8" ]] || \
  die "Expected Python 3.8; found Python ${PYTHON_VERSION}."

[[ -f "${ROS_SETUP}" ]] || die \
  'ROS Noetic was not found at /opt/ros/noetic. Install ROS Noetic first.'
[[ -f "${CUSTOM_ROOT}/requirements-core.txt" ]] || die \
  'custom_9dtact/requirements-core.txt is missing.'
[[ -f "${CUSTOM_ROOT}/ros_ws/src/9dtact_ft300_ros/package.xml" ]] || die \
  'The nine_dtact_ft300_ros catkin package source is missing.'

if [[ "${EUID}" -eq 0 ]]; then
  APT=(apt-get)
else
  command -v sudo >/dev/null 2>&1 || die 'sudo is required for apt installation.'
  APT=(sudo apt-get)
fi

info 'Installing Ubuntu and ROS core dependencies'
"${APT[@]}" update
DEBIAN_FRONTEND=noninteractive "${APT[@]}" install -y --no-install-recommends \
  build-essential \
  libgl1 \
  libglib2.0-0 \
  python3-pip \
  python3-venv \
  v4l-utils \
  ros-noetic-catkin \
  ros-noetic-cv-bridge \
  ros-noetic-geometry-msgs \
  ros-noetic-message-filters \
  ros-noetic-ros-numpy \
  ros-noetic-rospy \
  ros-noetic-sensor-msgs \
  ros-noetic-std-msgs \
  ros-noetic-std-srvs

if [[ -d "${VENV_ROOT}" ]]; then
  [[ -x "${VENV_ROOT}/bin/python" ]] || die \
    "Existing path is not a usable virtual environment: ${VENV_ROOT}"
  if ! grep -Eiq '^include-system-site-packages[[:space:]]*=[[:space:]]*true' \
    "${VENV_ROOT}/pyvenv.cfg"; then
    die "Existing ${VENV_ROOT} does not expose ROS system packages. Back it up, remove it, and rerun."
  fi
  info "Reusing existing virtual environment: ${VENV_ROOT}"
else
  info "Creating ROS-aware Python environment: ${VENV_ROOT}"
  python3 -m venv --system-site-packages "${VENV_ROOT}"
fi

# shellcheck disable=SC1090
source "${VENV_ROOT}/bin/activate"

info 'Installing pinned core Python dependencies'
python -m pip install --upgrade 'pip<25' wheel
python -m pip install -r "${CUSTOM_ROOT}/requirements-core.txt"

info 'Building the catkin workspace'
# shellcheck disable=SC1090
source "${ROS_SETUP}"
cd "${CUSTOM_ROOT}/ros_ws"
catkin_make
# shellcheck disable=SC1090
source "${CUSTOM_ROOT}/ros_ws/devel/setup.bash"

info 'Running core and ROS import checks'
cd "${REPOSITORY_ROOT}"
python scripts/verify_installation.py --profile core
python scripts/verify_installation.py --profile ros

cat <<EOF

Core installation and static dependency checks completed.

For each new terminal, run:
  source /opt/ros/noetic/setup.bash
  source ${VENV_ROOT}/bin/activate
  source ${CUSTOM_ROOT}/ros_ws/devel/setup.bash

This script did not install an external FT300 driver, open a camera, start a ROS
master, access FT300 hardware, run Shape Reconstruction, install the training stack,
or test a trained model. Continue with docs/02_SENSOR_CONFIGURATION.md.
EOF
