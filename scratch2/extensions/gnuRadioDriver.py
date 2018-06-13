#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
from gnuradio import gr
from gnuradio import qtgui
from gnuradio import fft
from gnuradio import filter
from gnuradio import blocks
from threading import Thread
from Queue import Queue

import os
import sys
import time
import re
import sip
import limesdr
import scratch_radio

COMMAND_PIPE_NAME = '/tmp/gr-control/command.pipe'

SDR_DEFAULT_FREQ = 433.92e6
SDR_SAMPLE_RATE  = 400e3
SDR_BANDWIDTH    = 300e3

#
# Specifies the base class for a managed flow graph block.
#
class FlowGraphBlock(object):
  def __init__(self):
    pass
  def grBlock(self):
    return None
  def cleanup(self):
    pass

#
# Implements a radio source data block using the gr-limesdr block which
# supports native decimation and digital filtering. This wraps the
# cached component reference to ensure that it is only initialised once.
#
class RadioSourceBlock(FlowGraphBlock):
  sdrSource = None
  def __init__(self, deviceSerialNumber):
    FlowGraphBlock.__init__(self)
    if (RadioSourceBlock.sdrSource == None):
      sdrSrc = limesdr.source(
        deviceSerialNumber, # device_number
        1,                  # device_type = LimeSDR-Mini
        1,                  # chip_mode = SISO
        0,                  # channel = A (in SISO mode)
        0,                  # file_switch = NO (don't load parameters from file)
        "",                 # filename = unused for no parameter file
        SDR_DEFAULT_FREQ,   # rf_freq (default to 433MHz ISM band)
        SDR_SAMPLE_RATE,    # samp_rate (default set to nominal 400 kHz)
        16,                 # oversample (decimate by x16)
        1,                  # calibration_ch0 enabled
        2.5e6,              # calibr_bandw_ch0 (default set to minimum 2.5 MHz)
        0,                  # calibration_ch1 disabled
        0,                  # calibr_bandw_ch1 unused
        3,                  # lna_path_mini = LNAW
        0,                  # lna_path_ch0 unused for LimeSDR-Mini
        0,                  # lna_path_ch1 unused for LimeSDR-Mini
        1,                  # analog_filter_ch0 enabled
        1.5e6,              # analog_bandw_ch0 (default set to minimum 1.5 MHz)
        0,                  # analog_filter_ch1 disabled
        1.5e6,              # analog_bandw_ch1 unused
        1,                  # digital_filter_ch0 enabled
        SDR_BANDWIDTH,      # digital_bandw_ch0 (default to nominal 200 kHz)
        0,                  # digital_filter_ch1 disabled
        SDR_BANDWIDTH,      # digital_bandw_ch1 unused
        40,                 # gain_dB_ch0 (default set to nominal 40dB)
        0,                  # gain_dB_ch1 unused
        0,                  # nco_freq_ch0 is unused
        0,                  # nco_freq_ch1 is unused
        0,                  # cmix_mode_ch0 is unused
        0                   # cmix_mode_ch1 is unused
      )
      RadioSourceBlock.sdrSource = sdrSrc

  def setup(self, topBlock, params):
    if (len(params) != 1):
      print "GNURadio: Invalid number of radio source parameters"
      return None
    try:
      tuningFreq = float(params[0])
    except ValueError, msg:
      print "GNURadio: Invalid radio source parameter - %s" % msg
      return None
    RadioSourceBlock.sdrSource.set_rf_freq(tuningFreq)
    return self

  def grBlock(self):
    return RadioSourceBlock.sdrSource

#
# Implements a radio sink data block using the gr-limesdr block which
# supports native interpolation and digital filtering. This wraps the
# cached component reference to ensure that it is only initialised once.
#
class RadioSinkBlock(FlowGraphBlock):
  sdrSink = None
  def __init__(self, deviceSerialNumber):
    FlowGraphBlock.__init__(self)
    if (RadioSinkBlock.sdrSink == None):
      sdrSnk = limesdr.sink(
        deviceSerialNumber, # device_number
        1,                  # device_type = LimeSDR-Mini
        1,                  # chip_mode = SISO
        0,                  # channel = A (in SISO mode)
        0,                  # file_switch = NO (don't load parameters from file)
        "",                 # filename = unused for no parameter file
        SDR_DEFAULT_FREQ,   # rf_freq (default to 433MHz ISM band)
        SDR_SAMPLE_RATE,    # samp_rate (default set to nominal 400 kHz)
        16,                 # oversample (interpolate by x16)
        0,                  # calibration_ch0 disabled - TODO: get this working
        5e6,                # calibr_bandw_ch0 (default set to minimum 5 MHz)
        0,                  # calibration_ch1 disabled
        0,                  # calibr_bandw_ch1 unused
        1,                  # pa_path_mini = BAND1
        0,                  # pa_path_ch0 unused for LimeSDR-Mini
        0,                  # pa_path_ch1 unused for LimeSDR-Mini
        1,                  # analog_filter_ch0 enabled
        5e6,                # analog_bandw_ch0 (default set to minimum 5 MHz)
        0,                  # analog_filter_ch1 disabled
        1.5e6,              # analog_bandw_ch1 unused
        1,                  # digital_filter_ch0 enabled
        SDR_BANDWIDTH,      # digital_bandw_ch0 (default to nominal 200 kHz)
        0,                  # digital_filter_ch1 disabled
        SDR_BANDWIDTH,      # digital_bandw_ch1 unused
        40,                 # gain_dB_ch0 (default set to nominal 40dB)
        0,                  # gain_dB_ch1 unused
        0,                  # nco_freq_ch0 is unused
        0,                  # nco_freq_ch1 is unused
        0,                  # cmix_mode_ch0 is unused
        0                   # cmix_mode_ch1 is unused
      )
      RadioSinkBlock.sdrSink = sdrSnk

  def setup(self, topBlock, params):
    if (len(params) != 1):
      print "GNURadio: Invalid number of radio sink parameters"
      return None
    try:
      tuningFreq = float(params[0])
    except ValueError, msg:
      print "GNURadio: Invalid radio sink parameter - %s" % msg
      return None
    RadioSinkBlock.sdrSink.set_rf_freq(tuningFreq)
    return self

  def grBlock(self):
    return RadioSinkBlock.sdrSink

#
# Implements a frequency domain display sink block with complex data input.
# This reconfigures an idle display if one is available, or creates a new
# display on demand.
#
class DisplaySinkFreqBlock(FlowGraphBlock):
  idleFreqSinkCs = []
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, compName, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of frequency plot parameters"
      return None
    try:
      tuningFreq = float(params[0])
      sampleRate = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid frequency plot parameter - %s" % msg
      return None

    # Create a new QT GUI component if required.
    plotTitle = "Spectrum Plot For '%s' Block" % compName
    if (len(DisplaySinkFreqBlock.idleFreqSinkCs) == 0):
      self.plotSink = qtgui.freq_sink_c(
        1024, fft.window.WIN_HANN, tuningFreq, sampleRate, plotTitle)
      self.pyobj = sip.wrapinstance(self.plotSink.pyqwidget(), QtGui.QWidget)

    # Reuse an existing idle component.
    else:
      idleFreqSinkC = DisplaySinkFreqBlock.idleFreqSinkCs.pop()
      self.plotSink = idleFreqSinkC[0];
      self.plotSink.set_frequency_range(tuningFreq, sampleRate)
      self.plotSink.set_title(plotTitle)
      self.pyobj = idleFreqSinkC[1];
    self.pyobj.show()
    return self

  def grBlock(self):
    return self.plotSink

  def cleanup(self):
    self.pyobj.hide()
    idleFreqSinkC = (self.plotSink, self.pyobj)
    DisplaySinkFreqBlock.idleFreqSinkCs.append(idleFreqSinkC)

#
# Implements a waterfall display sink block with complex data input.
# This reconfigures an idle display if one is available, or creates a new
# display on demand.
#
class DisplaySinkWaterfallBlock(FlowGraphBlock):
  idleWaterfallSinkCs = []
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, compName, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of waterfall plot parameters"
      return None
    try:
      tuningFreq = float(params[0])
      sampleRate = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid waterfall plot parameter - %s" % msg
      return None

    # Create a new QT GUI component if required.
    plotTitle = "Waterfall Plot For '%s' Block" % compName
    if (len(DisplaySinkWaterfallBlock.idleWaterfallSinkCs) == 0):
      self.plotSink = qtgui.waterfall_sink_c(
        512, fft.window.WIN_HANN, tuningFreq, sampleRate, plotTitle)
      self.plotSink.set_update_time(1)
      self.pyobj = sip.wrapinstance(self.plotSink.pyqwidget(), QtGui.QWidget)

    # Reuse an existing idle component.
    else:
      idleWaterfallSinkC = DisplaySinkWaterfallBlock.idleWaterfallSinkCs.pop()
      self.plotSink = idleWaterfallSinkC[0];
      self.plotSink.set_frequency_range(tuningFreq, sampleRate)
      self.plotSink.set_title(plotTitle)
      self.pyobj = idleWaterfallSinkC[1];
    self.pyobj.show()
    return self

  def grBlock(self):
    return self.plotSink

  def cleanup(self):
    self.pyobj.hide()
    idleWaterfallSinkC = (self.plotSink, self.pyobj)
    DisplaySinkWaterfallBlock.idleWaterfallSinkCs.append(idleWaterfallSinkC)

#
# Implements a low pass filter block with configurable cutoff frequency.
#
class LowPassFilterBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 3):
      print "GNURadio: Invalid number of low pass filter parameters"
      return None
    try:
      sampleRate = float(params[0])
      cutoffFreq = float(params[1])
      gain = float(params[2])
    except ValueError, msg:
      print "GNURadio: Invalid low pass filter parameter - %s" % msg
      return None
    if ((cutoffFreq <= 0) or (cutoffFreq >= sampleRate/2)):
      print "GNURadio: Low pass cutoff frequency out of range"
      return None

    # Calculate the FIR filter taps using the Blackman-Harris window method.
    transitionWidth = sampleRate/25
    filterTaps = filter.firdes.low_pass(gain, sampleRate,
      cutoffFreq, transitionWidth, filter.firdes.WIN_BLACKMAN_HARRIS)
    print "Generated FIR filter with %d taps" % len(filterTaps)
    self.firFilter = filter.fir_filter_ccf(1, filterTaps)
    return self

  def grBlock(self):
    return self.firFilter

#
# Implements a band pass filter block with configurable cutoff frequencies.
# This creates a single sided band pass filter with complex coefficients
# suitable for use with single sided modulation schemes such as ASK and FSK.
#
class BandPassFilterBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 4):
      print "GNURadio: Invalid number of band pass filter parameters"
      return None
    try:
      sampleRate = float(params[0])
      lowCutoffFreq = float(params[1])
      highCutoffFreq = float(params[2])
      gain = float(params[3])
    except ValueError, msg:
      print "GNURadio: Invalid band pass filter parameter - %s" % msg
      return None
    if ((lowCutoffFreq <= 0) or (highCutoffFreq >= sampleRate/2) or
        (lowCutoffFreq >= highCutoffFreq)):
      print "GNURadio: Band pass cutoff frequencies out of range"
      return None

    # Calculate the FIR filter taps using the Blackman-Harris window method.
    transitionWidth = sampleRate/25
    filterTaps = filter.firdes.complex_band_pass(gain, sampleRate, lowCutoffFreq,
      highCutoffFreq, transitionWidth, filter.firdes.WIN_BLACKMAN_HARRIS)
    print "Generated FIR filter with %d taps" % len(filterTaps)
    self.firFilter = filter.fir_filter_ccc(1, filterTaps)
    return self

  def grBlock(self):
    return self.firFilter

#
# Implements a decimation filter block with configurable decimation rate.
#
class DecimationFilterBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of decimation filter parameters"
      return None
    try:
      decimationFactor = int(params[0])
      gain = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid decimation filter parameter - %s" % msg
      return None
    if ((decimationFactor <= 0) or (decimationFactor > 20)):
      print "GNURadio: Decimation factor out of range"
      return None

    # Calculate the FIR filter taps using the Blackman-Harris window method.
    cutoffFreq = 0.375 / decimationFactor
    transitionWidth = 0.25 / decimationFactor
    filterTaps = filter.firdes.low_pass(gain, 1.0,
      cutoffFreq, transitionWidth, filter.firdes.WIN_BLACKMAN_HARRIS)
    print "Generated FIR filter with %d taps" % len(filterTaps)
    self.firFilter = filter.fir_filter_ccf(decimationFactor, filterTaps)
    return self

  def grBlock(self):
    return self.firFilter

#
# Implements an interpolation filter block with configurable interpolation
# rate.
#
class InterpolationFilterBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of interpolation filter parameters"
      return None
    try:
      interpolationFactor = int(params[0])
      gain = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid interpolation filter parameter - %s" % msg
      return None
    if ((interpolationFactor <= 0) or (interpolationFactor > 20)):
      print "GNURadio: Interpolation factor out of range"
      return None

    # Calculate the FIR filter taps using the Blackman-Harris window method.
    cutoffFreq = 0.375 / interpolationFactor
    transitionWidth = 0.25 / interpolationFactor
    filterTaps = filter.firdes.low_pass(gain, 1.0,
      cutoffFreq, transitionWidth, filter.firdes.WIN_BLACKMAN_HARRIS)
    print "Generated FIR filter with %d taps" % len(filterTaps)
    self.firFilter = filter.interp_fir_filter_ccf(interpolationFactor, filterTaps)
    return self

  def grBlock(self):
    return self.firFilter

#
# Implements a ScratchRadio message source block.
#
class MessageSourceBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of message source parameters"
      return None

    # Creates the message pipe FIFO if not already present.
    try:
      msgFileName = params[0]
      msgPipePath = os.path.dirname(msgFileName)
      if not os.path.exists(msgPipePath):
        os.makedirs(msgPipePath)
      if not os.path.exists(msgFileName):
        os.mkfifo(msgFileName)
    except Exception, msg:
      print "GNURadio: Invalid message source file name - %s" % msg
      return None
    try:
      msgCpsRate = int(params[1])
    except Exception, msg:
      print "GNURadio: Invalid message source CPS rate - %s" % msg
      return None

    self.msgSource = scratch_radio.message_source(msgFileName, msgCpsRate)
    return self

  def grBlock(self):
    return self.msgSource

#
# Implements a ScratchRadio message sink block.
#
class MessageSinkBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 1):
      print "GNURadio: Invalid number of message sink parameters"
      return None

    # Creates the message pipe FIFO if not already present.
    try:
      msgFileName = params[0]
      msgPipePath = os.path.dirname(msgFileName)
      if not os.path.exists(msgPipePath):
        os.makedirs(msgPipePath)
      if not os.path.exists(msgFileName):
        os.mkfifo(msgFileName)
    except Exception, msg:
      print "GNURadio: Invalid message sink file name - %s" % msg
      return None

    self.msgSink = scratch_radio.message_sink(msgFileName)
    return self

  def grBlock(self):
    return self.msgSink

#
# Implements a ScratchRadio simple framer block.
#
class SimpleFramerBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)
    self.simpleFramer = scratch_radio.simple_framer()

  def grBlock(self):
    return self.simpleFramer

#
# Implements a ScratchRadio simple deframer block.
#
class SimpleDeframerBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)
    self.simpleDeframer = scratch_radio.simple_deframer()

  def grBlock(self):
    return self.simpleDeframer

#
# Implements a Manchester encoder block.
#
class ManchesterEncoderBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)
    self.encoder = scratch_radio.manc_enc(False)

  def grBlock(self):
    return self.encoder

#
# Implements a Manchester decoder block.
#
class ManchesterDecoderBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)
    self.decoder = scratch_radio.manc_dec(False)

  def grBlock(self):
    return self.decoder

#
# Implements an OOK modulator block.
#
class OokModulatorBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 3):
      print "GNURadio: Invalid number of OOK modulator parameters"
      return None

    # Specify the sample rate and baud rate.
    try:
      baudRate = int(params[0])
      sampleRate = int(params[1])
      modFreq = int(params[2])
    except ValueError, msg:
      print "GNURadio: Invalid OOK modulator parameter - %s" % msg
      return None

    # TODO: Should check valid range for baudRate and sampleRate.
    self.modulator = scratch_radio.ook_modulator(baudRate, sampleRate, modFreq)
    return self

  def grBlock(self):
    return self.modulator

#
# Implements an OOK demodulator block.
#
class OokDemodulatorBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of OOK demodulator parameters"
      return None

    # Specify the sample rate and baud rate.
    try:
      baudRate = int(params[0])
      sampleRate = int(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid OOK demodulator parameter - %s" % msg
      return None

    # TODO: Should check valid range for baudRate and sampleRate.
    self.demodulator = scratch_radio.ook_demodulator(baudRate, sampleRate)
    return self

  def grBlock(self):
    return self.demodulator

#
# Implements a symbol synchronisation block.
#
class SymbolSyncBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of symbol sync parameters"
      return None

    # Specify the sample rate and baud rate.
    try:
      baudRate = int(params[0])
      sampleRate = int(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid symbol sync parameter - %s" % msg
      return None

    # TODO: Should check valid range for baudRate and sampleRate.
    self.symbolSync = scratch_radio.symbol_sync(baudRate, sampleRate)
    return self

  def grBlock(self):
    return self.symbolSync

#
# Implements a sample rate limiter block which should be used in loopback
# type applications to limit the average sample rate.
#
class SampleRateLimiterBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of sample rate limit parameters"
      return None

    # Specify the sample data type.
    if params[0] == 'b':
      sampleSize = 1
    else:
      print "GNURadio: Unsupported sample rate limit data type"
      return None

    # Specify the sample rate.
    try:
      sampleRate = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid sample rate limit parameter - %s" % msg
      return None

    self.throttleBlock = blocks.throttle(sampleSize, sampleRate)
    return self

  def grBlock(self):
    return self.throttleBlock

#
# Implements the flow graph. On initialisation ensures that the graph is reset
# to a known state and builds a mapping of component types to their associated
# creation functions.
#
class FlowGraph(gr.top_block):
  def __init__(self, deviceSerialNumber):
    gr.top_block.__init__(self, "Scratch Flow Graph")
    self.comps = {}
    self.compCreateFns = {}
    self.compCreateFns["RADIO-SOURCE"] = self._createRadioSource
    self.compCreateFns["RADIO-SINK"] = self._createRadioSink
    self.compCreateFns["DISPLAY-SINK"] = self._createDisplaySink
    self.compCreateFns["LOW-PASS-FILTER"] = self._createLowPassFilter
    self.compCreateFns["BAND-PASS-FILTER"] = self._createBandPassFilter
    self.compCreateFns["DECIMATION-FILTER"] = self._createDecimationFilter
    self.compCreateFns["INTERPOLATION-FILTER"] = self._createInterpolationFilter
    self.compCreateFns["MESSAGE-SOURCE"] = self._createMessageSource
    self.compCreateFns["MESSAGE-SINK"] = self._createMessageSink
    self.compCreateFns["SIMPLE-FRAMER"] = self._createSimpleFramer
    self.compCreateFns["SIMPLE-DEFRAMER"] = self._createSimpleDeframer
    self.compCreateFns["MANCHESTER-ENCODER"] = self._createManchesterEncoder
    self.compCreateFns["MANCHESTER-DECODER"] = self._createManchesterDecoder
    self.compCreateFns["OOK-MODULATOR"] = self._createOokModulator
    self.compCreateFns["OOK-DEMODULATOR"] = self._createOokDemodulator
    self.compCreateFns["BIT-RATE-SAMPLER"] = self._createSymbolSync
    self.compCreateFns["SAMPLE-RATE-LIMITER"] = self._createSampleRateLimiter
    self.deviceSerialNumber = deviceSerialNumber

  # Add a new radio source data block to the hierarchy. This uses the Lime
  # Microsystems SoapySDR driver.
  def _createRadioSource(self, compName, params):
    radioSourceBlock = RadioSourceBlock(deviceSerialNumber)
    return radioSourceBlock.setup(self, params)

  # Add a new radio sink data block to the hierarchy. This uses the Lime
  # Microsystems SoapySDR driver.
  def _createRadioSink(self, compName, params):
    radioSinkBlock = RadioSinkBlock(deviceSerialNumber)
    return radioSinkBlock.setup(self, params)

  # Create a new display sink. This is currently limited to a simple FFT
  # or waterfall displays, but more advanced options can be included at
  # a later date
  def _createDisplaySink(self, compName, params):
    displayType = params.pop(0)
    if (displayType == "WATERFALL"):
      displaySinkBlock = DisplaySinkWaterfallBlock()
    else:
      displaySinkBlock = DisplaySinkFreqBlock()
    return displaySinkBlock.setup(compName, params)

  # Create a new low pass filter. This is currently limited in terms of
  # configuration options to specifying the nominal sample rate, 3dB
  # cutoff point and filter gain.
  def _createLowPassFilter(self, compName, params):
    filterBlock = LowPassFilterBlock()
    return filterBlock.setup(params)

  # Create a new band pass filter. This is currently limited in terms of
  # configuration options to specifying the nominal sample rate, 3dB
  # cutoff points and filter gain.
  def _createBandPassFilter(self, compName, params):
    filterBlock = BandPassFilterBlock()
    return filterBlock.setup(params)

  # Create a new decimation filter. This is currently limited in terms
  # configuration options to specifying the decimation factor and gain.
  # The 3dB cutoff point is at 75% of the downsampled Nyquist rate.
  def _createDecimationFilter(self, compName, params):
    filterBlock = DecimationFilterBlock()
    return filterBlock.setup(params)

  # Create a new interpolation filter. This is currently limited in terms
  # configuration options to specifying the interpolation factor and gain.
  # The 3dB cutoff point is at 75% of the input Nyquist rate.
  def _createInterpolationFilter(self, compName, params):
    filterBlock = InterpolationFilterBlock()
    return filterBlock.setup(params)

  # Create a new message source block.
  def _createMessageSource(self, compName, params):
    messageSource = MessageSourceBlock()
    return messageSource.setup(params)

  # Create a new message sink block.
  def _createMessageSink(self, compName, params):
    messageSink = MessageSinkBlock()
    return messageSink.setup(params)

  # Create a new simple framer block.
  def _createSimpleFramer(self, compName, params):
    return SimpleFramerBlock()

  # Create a new simple deframer block.
  def _createSimpleDeframer(self, compName, params):
    return SimpleDeframerBlock()

  # Create a new Manchester encoder block.
  def _createManchesterEncoder(self, compName, params):
    return ManchesterEncoderBlock()

  # Create a new Manchester decoder block.
  def _createManchesterDecoder(self, compName, params):
    return ManchesterDecoderBlock()

  # Create a new OOK modulator block.
  def _createOokModulator(self, compName, params):
    modulator = OokModulatorBlock()
    return modulator.setup(params)

  # Create a new OOK demodulator block.
  def _createOokDemodulator(self, compName, params):
    demodulator = OokDemodulatorBlock()
    return demodulator.setup(params)

  # Create a new symbol timing recovery block.
  def _createSymbolSync(self, compName, params):
    symbolSync = SymbolSyncBlock()
    return symbolSync.setup(params)

  # Create a new sample rate limiting block.
  def _createSampleRateLimiter(self, compName, params):
    sampleRateLimiter = SampleRateLimiterBlock()
    return sampleRateLimiter.setup(params)

  # Resets the flow graph by disconnecting all the components and then removing
  # them from the component table. This uses the cleanup method to release any
  # associated component resources.
  def resetGraph(self):
    self.disconnect_all()
    for component in self.comps.values():
      component.cleanup()
    self.comps = {}

  # Perform initial processing for the 'CREATE' command. This checks the common
  # command fields and then dispatches further processing to component specific
  # functions.
  def createComponent(self, params):
    if (len(params) < 2):
      print "GNURadio: Malformed CREATE command"
      return False
    compType = params.pop(0)
    compName = params.pop(0)

    # Check for duplicate component names.
    if (compName in self.comps):
      print "GNURadio: Duplicate component name - %s" % compName
      return False

    # Get the component creation function to use.
    if (compType not in self.compCreateFns):
      print "GNURadio: Unknown component type - %s" % compType
      return False
    compCreateFn = self.compCreateFns[compType]

    # Run the component creation function.
    newComp = compCreateFn(compName, params)
    if (newComp == None):
      return False
    else:
      self.comps[compName] = newComp
      return True

  # Add a connection between two existing components. Note that the port fields
  # are currently ignored, since no multiple input or multiple output blocks
  # are defined.
  def connectComponents(self, params):
    if (len(params) != 4):
      print "GNURadio: Malformed CONNECT command"
      return False
    sourceName = params[0];
    targetName = params[2];

    # Check for valid component names.
    if (sourceName not in self.comps):
      print "GNURadio: Unknown source for connection - %s" % sourceName
      return False
    if (targetName not in self.comps):
      print "GNURadio: Unknown target for connection - %s" % targetName
      return False

    # Hook up the associated GNU Radio blocks.
    source = self.comps[sourceName]
    target = self.comps[targetName]
    self.connect(source.grBlock(), target.grBlock())
    return True

#
# Implements command parsing on a timed callback from the main QT event loop.
# This allows QT GUI components to be manipulated in direct response to the
# incoming commands.
#
class CommandParser(QtCore.QObject):
  def __init__(self, parent, commandQueue, deviceSerialNumber):
    QtCore.QObject.__init__(self, parent)
    self.cmdQueue = commandQueue
    self.flowGraph = FlowGraph(deviceSerialNumber)
    self.radioRunning = False
    self.timerId = self.startTimer(500)

  def _processInteractiveCommands(self, command):
    print "Interactive command: %s" % command
    handled = False
    cmdTerms = command.split()
    cmdType = cmdTerms.pop(0)

    if (not handled):
      print "GNURadio: Unhandled interactive command type - %s" % cmdType
    return handled

  def _processSetupCommands(self, command):
    print "Setup command: %s" % command
    handled = False
    cmdTerms = command.split()
    cmdType = cmdTerms.pop(0)

    # Create a new block.
    if (cmdType == "CREATE"):
      handled = self.flowGraph.createComponent(cmdTerms)

    # Connect existing blocks.
    elif (cmdType == "CONNECT"):
      handled = self.flowGraph.connectComponents(cmdTerms)

    # Ignore comments.
    elif (cmdType == "#"):
      handled = True

    if (not handled):
      print "GNURadio: Unhandled setup command type - %s" % cmdType
    return handled

  # Parses individual commands as they are removed from the command queue.
  def _parseCommand(self, command):
    handled = False

    # Force reset, which stops the radio and deletes all components.
    if (command == "RESET"):
      handled = True
      if (self.radioRunning):
        print "GNURadio: STOPPING"
        self.flowGraph.stop()
        self.flowGraph.wait()
        self.radioRunning = False
        print "GNURadio: STOPPED"
      self.flowGraph.resetGraph()
      print "GNURadio: RESET"

    # Start the radio running if it is currently idle.
    elif (command == "START"):
      handled = True
      if (not self.radioRunning):
        print "GNURadio: STARTING"
        self.flowGraph.start()
        self.radioRunning = True
        print "GNURadio: STARTED"
      else:
        print "GNURadio: STARTED (ALREADY RUNNING)"

    # Stop the radio from running.
    elif (command == "STOP"):
      handled = True
      if (self.radioRunning):
        print "GNURadio: STOPPING"
        self.flowGraph.stop()
        self.flowGraph.wait()
        self.radioRunning = False
        print "GNURadio: STOPPED"
      else:
        print "GNURadio: STOPPED (NOT RUNNING)"

    # Process interactive commands for running radio.
    elif (self.radioRunning):
      handled = self._processInteractiveCommands(command)

    # Process radio setup commands.
    else:
      handled = self._processSetupCommands (command)

  # Overrides the standard QTObject timer callback to parse outstanding
  # commands from the command queue.
  def timerEvent(self, event):
    if (self.timerId == event.timerId()):
      while (not self.cmdQueue.empty()):
        self._parseCommand(self.cmdQueue.get())

#
# Implements command file reader as an independent Python thread, which carries
# out blocking line reads on the command file and forwards them to the main
# QT application thread via a Python queue.
#
class CommandReader(Thread):
  def __init__(self, commandQueue):
    Thread.__init__(self)

    # Creates the command pipe FIFO if not already present.
    commandPipePath = os.path.dirname(COMMAND_PIPE_NAME)
    if not os.path.exists(commandPipePath):
      os.makedirs(commandPipePath)
    if not os.path.exists(COMMAND_PIPE_NAME):
      os.mkfifo(COMMAND_PIPE_NAME)

    # Registers the command queue instance.
    self.cmdQueue = commandQueue
    self.running = True

  def run(self):
    cmdFile = open(COMMAND_PIPE_NAME, 'r')
    while self.running:
      cmd = cmdFile.readline().rstrip()
      if (cmd == ''):
        time.sleep(0.5)
      else:
        self.cmdQueue.put(cmd)
        while (self.cmdQueue.full()):
          time.sleep(0.5)

#
# Check for the availability of a single LimeMini device on startup.
#
def checkForLimeMini():
  regex = '\s*\*\s*\[\s*(.+),\s*(.+),\s*(.+),\s*(.+),\s*serial=(.+)\]'
  limeUtil = os.popen("LimeUtil -find")
  deviceList = limeUtil.readlines()
  limeUtil.close()
  deviceSerialNumber = None
  for deviceInfo in deviceList:
    matches = re.match(regex, deviceInfo)
    if (matches != None):
      deviceInfo = matches.groups()
      if (deviceInfo[0] == "LimeSDR Mini"):
        deviceSerialNumber = deviceInfo[4]
  return deviceSerialNumber

#
# Run the main application.
#
def runApp(deviceSerialNumber):
  qapp = QtGui.QApplication(sys.argv)
  cmdQueue = Queue(8)
  cmdReader = CommandReader(cmdQueue)
  cmdReader.start()
  cmdParser = CommandParser(qapp, cmdQueue, deviceSerialNumber)
  qapp.exec_()

if __name__ == '__main__':
  try:
    deviceSerialNumber = checkForLimeMini()
    if (deviceSerialNumber == None):
      print "No LimeSDR Mini Device Found!"
    else:
      print "Starting GNU Radio Driver Application For Device: ", deviceSerialNumber
      runApp(deviceSerialNumber)
  except [[KeyboardInterrupt]]:
    pass
