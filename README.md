# Entry Level SDR Educational Tools For Raspberry Pi

![ScratchRadio](/images/ScratchRadio-detail.jpg)

This repository contains entry level educational tools for introducing SDR 
technology on the Raspberry Pi platform. A Raspberry Pi 3 Model B running 
Raspbian Stretch is the recommended host configuration.

## Installation and Setup

The following installation steps assume a new installation of Raspbian Stretch 
is being used. All the required package dependencies for building the various 
SDR components can be installed by running the 'install_deps.sh' script with 
superuser privileges:

  > sudo  ./scripts/install_deps.sh

The Raspbian Stretch distribution already contains pre-built packages for 
SoapySDR and LimeUtils, but these are out of date relative to the current 
repositories and they need to be built and installed from source instead. The 
'LimeSuite' makefile target automates this process:

  > make LimeSuite

LuaRadio also needs to be installed in the same way. It uses the standard 
Raspbian packages for LiquidDSP and fast FFT libraries:

  > make LuaRadio

Finally, the latest files for Scratch2 integration can be installed as follows:

  > make ScratchRadio
  
## Running Scratch Radio

In order to use the Scratch radio blocks, the corresponding LuaRadio wrapper 
script needs to be running. Once the code is more mature this process will need 
to be automated, but for now, the script can be started as a foreground task for 
debugging purposes as follows:

  > ./scripts/start_lua_radio.sh

It should now be possible to access the radio functions from Scratch by running 
Scratch2 from the Raspbian programming menu and selecting the 'Add an Extension 
option under 'More Blocks'.

