"""Python package metadata for repository-in-place development.

Calibration arrays, models, datasets, ROS launch files, and visualization
assets are intentionally operated from the checked-out repository.  This
metadata installs only the importable Python modules and their core runtime
dependencies.
"""

from pathlib import Path

from setuptools import find_packages, setup


PROJECT_ROOT = Path(__file__).resolve().parent


def read_requirements(name):
    """Return concrete requirement lines from one local requirement file."""
    return [
        line.strip()
        for line in (PROJECT_ROOT / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
        and not line.lstrip().startswith("-r")
    ]


setup(
    name="9dtact-ft300-custom-sensor",
    version="2.0.0",
    packages=find_packages(),
    url="https://github.com/Liiiin-hku/9DTact_FT300_Custom_Sensor_Project",
    license="MIT",
    author="9DTact FT300 Custom Sensor Project contributors",
    description=(
        "Custom dual-sensor 9DTact calibration, shape reconstruction, "
        "FT300 data acquisition, and six-axis force estimation"
    ),
    python_requires=">=3.8,<3.11",
    install_requires=read_requirements("requirements-core.txt"),
    extras_require={
        "training": (
            read_requirements("requirements-training.txt")
            + read_requirements("requirements-pytorch.txt")
        ),
    },
)
