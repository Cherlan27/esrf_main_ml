# -*- coding: utf-8 -*-

"""The setup script."""

import sys
from setuptools import setup, find_packages

TESTING = any(x in sys.argv for x in ["test", "pytest"])

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ["numpy"]

setup_requirements = ["pytest-runner", "pytest"] if TESTING else []

test_requirements = ["pytest-cov", "mock"]

setup(
    author="AG Schreiber",
    author_email="linus.pithan@uni-tuebingen.de",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    description="helper tools for closed loop beamtime",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme,
    include_package_data=True,
    keywords="xrrhelpers",
    name="closed_loop_xrr",
    # package_dir={"": ""},
    packages=["closed_loop_xrr"],
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="http://softmatter-gitserv.am10.uni-tuebingen.de/machine-learning/closed_loop_beamtime.git",
    version="0.1.0",
    zip_safe=False,
    # entry_points={"console_scripts": ["dcmfatgui = dcmfat_gui.fat_test_gui:main"]},
)
