#
# Makefile for building and installing the required SDR projects from
# source. Automatically runs the install phases as part of the process
# which may require the 'sudo' password to be entered at various points.
# For development purposes we use the latest versions of SoapySDR and
# LimeSuite rather than the versions packaged with Raspbian Stretch
#
BUILD_DIR = MyriadRF-Build
SCRATCH_EXT_DIR = /usr/lib/scratch2/scratch_extensions

# List of pseudo-targets.
LuaRadio: /usr/local/bin/luaradio
LimeSuite: /usr/local/bin/LimeUtil

ScratchRadio: $(SCRATCH_EXT_DIR)/luaRadioExtension.js \
		$(SCRATCH_EXT_DIR)/luaRadioDriver.lua \
		$(SCRATCH_EXT_DIR)/luaradio.html
	# Make sure we only patch this file once!
	if ! grep luaRadioExtension $(SCRATCH_EXT_DIR)/extensions.json > /dev/null; \
		then sudo patch -b $(SCRATCH_EXT_DIR)/extensions.json patches/scratch_extensions.patch; \
		fi

# Copy over the Scratch Radio development files.
$(SCRATCH_EXT_DIR)/luaRadioExtension.js : scratch2/extensions/luaRadioExtension.js
	sudo cp $< $@
$(SCRATCH_EXT_DIR)/luaRadioDriver.lua : scratch2/extensions/luaRadioDriver.lua
	sudo cp $< $@
$(SCRATCH_EXT_DIR)/luaradio.html : scratch2/extensions/luaradio.html
	sudo cp $< $@

# Install Lua Radio.
/usr/local/bin/luaradio: $(BUILD_DIR)/luaradio/embed/build/libluaradio.a
	cd $(BUILD_DIR)/luaradio/embed; \
		sudo make install; \
		sudo ldconfig

# Build Lua Radio.
$(BUILD_DIR)/luaradio/embed/build/libluaradio.a: $(BUILD_DIR)/luaradio
	cd $(BUILD_DIR)/luaradio/embed; \
		make lib

# Get the latest code from the LuaRadio repo.
$(BUILD_DIR)/luaradio: $(BUILD_DIR)
	cd $(BUILD_DIR); \
		rm -rf luaradio; \
		git clone https://github.com/vsergeev/luaradio.git

# Install LimeSuite.
/usr/local/bin/LimeUtil: $(BUILD_DIR)/LimeSuite/builddir
	cd $(BUILD_DIR)/LimeSuite/builddir; \
		sudo make install; \
		sudo ldconfig
	cd $(BUILD_DIR)/LimeSuite/udev-rules; \
		sudo ./install.sh

# Build LimeSuite.
$(BUILD_DIR)/LimeSuite/builddir: $(BUILD_DIR)/LimeSuite /usr/local/bin/SoapySDRUtil
	cd $(BUILD_DIR)/LimeSuite; \
		mkdir builddir; \
		cd builddir; \
		cmake ..; \
		make

# Get the latest code from the LimeSuite repo.
$(BUILD_DIR)/LimeSuite: $(BUILD_DIR) patches/LimeSuite.patch
	cd $(BUILD_DIR); \
		rm -rf LimeSuite; \
		git clone https://github.com/myriadrf/LimeSuite.git
	patch -p1 --directory=$@ < patches/LimeSuite.patch

# Install SoapySDR.
/usr/local/bin/SoapySDRUtil: $(BUILD_DIR)/SoapySDR/build
	cd $(BUILD_DIR)/SoapySDR/build; \
		sudo make install; \
		sudo ldconfig

# Build SoapySDR.
$(BUILD_DIR)/SoapySDR/build: $(BUILD_DIR)/SoapySDR
	cd $(BUILD_DIR)/SoapySDR; \
		mkdir build; \
		cd build; \
		cmake ..; \
		make

# Get the latest code from the SoapySDR repo.
$(BUILD_DIR)/SoapySDR: $(BUILD_DIR)
	cd $(BUILD_DIR); \
		rm -rf SoapySDR; \
		git clone https://github.com/pothosware/SoapySDR.git

$(BUILD_DIR):
	mkdir $@
