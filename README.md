# Entry Level SDR Educational Tools For Raspberry Pi

![ScratchRadio](/images/ScratchRadio-detail.jpg)

This repository contains entry level educational tools for introducing SDR
technology on the Raspberry Pi platform. A Raspberry Pi 3 Model B running
Raspbian Stretch is the recommended host configuration.

## Installation and Setup

The following installation steps assume a new installation of Raspbian Stretch
is being used. All the required package dependencies for building the various
SDR components can be installed by running the 'install_deps.sh' script with
superuser privileges. Note that it may be necessary to re-run this script if
any of the package installation steps fail:

  > sudo  ./scripts/install_deps.sh

The Raspbian Stretch distribution already contains pre-built packages for
SoapySDR and LimeUtils, but these are out of date relative to the current
repositories and they need to be built and installed from source instead. The
'LimeSuite' makefile target automates this process:

  > make LimeSuite

The main GNU Radio package from the Raspbian Stretch distribution is
installed as one of the required dependencies. However, an up to date
version of the GR-OsmoSDR package needs to be compiled against the latest
SoapySDR release, together with the out of tree GNU Radio module from this
repository which contains the dedicated Scratch Radio components:

  > make GnuRadio

Finally, the latest files for Scratch2 integration can be installed as follows:

  > make ScratchRadio

The default makefile target is 'all' which will run the builds for LimeSuite,
GnuRadio and ScratchRadio in the required order. After running the build
process, all the intermediate files can be removed by using the 'clean'
target:

  > make clean

## Running Scratch Radio

In order to use the Scratch radio blocks, the corresponding GNU Radio wrapper
script needs to be running. This occurs automatically on loading the Scratch
Radio extension. The wrapper script currently runs in a new terminal window
which can be useful for development and debugging purposes.

It should now be possible to access the radio functions from Scratch by running
Scratch2 from the Raspbian programming menu and selecting the 'Add an Extension
option under 'More Blocks'.

## Removing Scratch Radio

The Scratch Radio extension can be removed by using the 'uninstall' makefile
target as follows:

  > make uninstall

This will remove the extension files from the Scratch2 installation directory
but leaves the GNU Radio and LimeSuite installations intact.
