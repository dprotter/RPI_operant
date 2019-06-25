#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'RPI_operant'
DESCRIPTION = 'A Rasbperry Pi based operant test chamber package'
URL = 'https://github.com/dprotter/RPI_operant'
EMAIL = 'david.protter@colorado.edu'
AUTHOR = 'David Protter'
REQUIRES_PYTHON = '>=3.4.0'
VERSION = '0.1.0'

# What packages are required for this module to be executed?
REQUIRED = [
    numpy, RPi.GPIO, adafruit-circuitpython-servokit, netifaces, smtplib,
]


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,

    # If your package is a single module, use this instead of 'packages':
    py_modules=['mypackage'],

    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='University of Colorado, Donaldson Lab',

)
