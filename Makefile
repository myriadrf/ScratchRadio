#
# Makefile for building and installing the required SDR projects from
# source. Automatically runs the install phases as part of the process
# which may require the 'sudo' password to be entered at various points.
# For development purposes we use the latest versions of SoapySDR and
# LimeSuite rather than the versions packaged with Raspbian Stretch
#
BUILD_DIR = MyriadRF-Build
SCRATCH_EXT_DIR = /usr/lib/scratch2/scratch_extensions
SCRATCH_IMG_DIR = /usr/lib/scratch2/medialibrarythumbnails

# Make everything by default.
all: LimeSuite GnuRadio ScratchRadio

# Clean up the build directory.
clean:
	rm -rf $(BUILD_DIR)

# Uninstall the ScratchRadio extension (leaves GNU Radio and LimeSuite intact).
uninstall:
	sudo rm -f $(SCRATCH_EXT_DIR)/gnuRadioExtension.js
	sudo rm -f $(SCRATCH_EXT_DIR)/gnuRadioDriver.py
	sudo rm -f $(SCRATCH_EXT_DIR)/gnuradio.html
	sudo rm -f $(SCRATCH_EXT_DIR)/start_gnu_radio.sh
	sudo rm -f $(SCRATCH_IMG_DIR)/myriadrf.png
	# Make sure we only unpatch this file once!
	if grep gnuRadioExtension $(SCRATCH_EXT_DIR)/extensions.json > /dev/null; \
		then sudo patch -R -b $(SCRATCH_EXT_DIR)/extensions.json patches/scratch_extensions.patch; \
		fi

# List of intermediate pseudo-targets.
GnuRadio: /usr/local/lib/libgnuradio-limesdr.so /usr/local/lib/libgnuradio-scratch_radio.so
LimeSuite: /usr/local/bin/LimeUtil

ScratchRadio: $(SCRATCH_EXT_DIR)/gnuRadioExtension.js \
		$(SCRATCH_EXT_DIR)/gnuRadioDriver.py \
		$(SCRATCH_EXT_DIR)/gnuradio.html \
		$(SCRATCH_EXT_DIR)/start_gnu_radio.sh \
		$(SCRATCH_IMG_DIR)/myriadrf.png
	# Make sure we only patch this file once!
	if ! grep gnuRadioExtension $(SCRATCH_EXT_DIR)/extensions.json > /dev/null; \
		then sudo patch -b $(SCRATCH_EXT_DIR)/extensions.json patches/scratch_extensions.patch; \
		fi

# Copy over the Scratch Radio development files.
$(SCRATCH_EXT_DIR)/gnuRadioExtension.js : scratch2/extensions/gnuRadioExtension.js
	sudo cp $< $@
$(SCRATCH_EXT_DIR)/gnuRadioDriver.py : scratch2/extensions/gnuRadioDriver.py
	sudo cp $< $@
$(SCRATCH_EXT_DIR)/gnuradio.html : scratch2/extensions/gnuradio.html
	sudo cp $< $@
$(SCRATCH_EXT_DIR)/start_gnu_radio.sh : scripts/start_gnu_radio.sh
	sudo chmod +x $<; sudo cp $< $@
$(SCRATCH_IMG_DIR)/myriadrf.png : images/myriadrf.png
	sudo cp $< $@

# Install GNU Radio OOT library module from local source.
/usr/local/lib/libgnuradio-scratch_radio.so: $(BUILD_DIR)/gr-scratch_radio/builddir
	cd $(BUILD_DIR)/gr-scratch_radio/builddir; \
		sudo make install; \
		sudo ldconfig

# Build OOT library module from local source.
$(BUILD_DIR)/gr-scratch_radio/builddir:
	cd $(BUILD_DIR); \
		mkdir -p gr-scratch_radio/builddir; \
		cd gr-scratch_radio/builddir; \
		cmake ../../../gnuradio/gr-scratch_radio; \
		make

# Install GNU Radio LimeSDR library from latest source.
/usr/local/lib/libgnuradio-limesdr.so: $(BUILD_DIR)/gr-limesdr/build
	cd $(BUILD_DIR)/gr-limesdr/build; \
		sudo make install; \
		sudo ldconfig

# Build GNU Radio LimeSDR library from latest source.
$(BUILD_DIR)/gr-limesdr/build: $(BUILD_DIR)/gr-limesdr
	cd $(BUILD_DIR)/gr-limesdr; \
		mkdir build; \
		cd build; \
		cmake ..; \
		make

# Get the latest code from the GNU Radio LimeSDR library repo.
$(BUILD_DIR)/gr-limesdr: $(BUILD_DIR)
	cd $(BUILD_DIR); \
		rm -rf gr-limesdr; \
		git clone https://github.com/myriadrf/gr-limesdr.git

# Install LimeSuite.
/usr/local/bin/LimeUtil: $(BUILD_DIR)/LimeSuite/builddir
	cd $(BUILD_DIR)/LimeSuite/builddir; \
		sudo make install; \
		sudo ldconfig
	cd $(BUILD_DIR)/LimeSuite/udev-rules; \
		sudo sh ./install.sh

# Build LimeSuite.
$(BUILD_DIR)/LimeSuite/builddir: $(BUILD_DIR)/LimeSuite /usr/local/bin/SoapySDRUtil
	cd $(BUILD_DIR)/LimeSuite; \
		mkdir builddir; \
		cd builddir; \
		cmake ..; \
		make

# Get the latest code from the LimeSuite repo.
$(BUILD_DIR)/LimeSuite: $(BUILD_DIR)
	cd $(BUILD_DIR); \
		rm -rf LimeSuite; \
		git clone https://github.com/myriadrf/LimeSuite.git

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
