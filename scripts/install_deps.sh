#!/bin/bash
#
# Installs standard Raspbian packages which are prerequisites for
# building the various SDR components from source. This script will
# typically be run using 'sudo' on a new installation of Rasbian
# Stretch.
#
apt-get update
apt-get upgrade

# Install common build tools.
yes | apt-get install git g++ make cmake pkg-config

# Ensure that Scratch 2 is installed for non-standard images.
yes | apt-get install scratch2

# Install common Python development packages.
yes | apt-get install libpython-dev python-numpy swig

# Install SQL development packages.
yes | apt-get install libsqlite3-dev

# Install hardware support packages.
yes | apt-get install libi2c-dev libusb-1.0-0-dev

# Install graphics toolkit development packages.
yes | apt-get install gnuplot libwxgtk3.0-dev freeglut3-dev

# Install SDR specific libraries.
yes | apt-get install libfftw3-dev libliquid-dev

# Install GNU Radio and associated dependencies.
yes | apt-get install gnuradio
