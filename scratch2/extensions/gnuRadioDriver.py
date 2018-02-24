#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
from gnuradio import gr
from gnuradio import qtgui
from gnuradio import fft
from gnuradio import filter
from threading import Thread
from Queue import Queue

import os
import sys
import time
import sip
import osmosdr

COMMAND_PIPE_NAME='/tmp/gr-control/command.pipe'

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
# Implements a radio source data block. This wraps the cached component
# reference to ensure that it is only initialised once.
#
class RadioSourceBlock(FlowGraphBlock):
  sdrSource = None
  def __init__(self):
    FlowGraphBlock.__init__(self)
    if (RadioSourceBlock.sdrSource == None):
      RadioSourceBlock.sdrSource = osmosdr.source(args="soapy=0,driver=lime")

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of radio source parameters"
      return None
    try:
      tuningFreq = float(params[0])
      sampleRate = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid radio source parameter - %s" % msg
      return None

    # Set the sample rate and tuning frequency, checking that these are in
    # range for the hardware.
    print "Found LimeSDR Source"
    sdrSrc = RadioSourceBlock.sdrSource
    sdrSampleRate = sdrSrc.set_sample_rate(sampleRate)
    if (abs(sdrSampleRate-sampleRate) > abs(sampleRate*0.005)):
      print "GNURadio: Invalid radio source sample rate - %f" % sampleRate
      return None
    print "Configured Source Sample Rate = %e" % sdrSampleRate
    sdrTuningFreq = sdrSrc.set_center_freq(tuningFreq, 0)
    if (abs(sdrTuningFreq-tuningFreq) > abs(tuningFreq*0.005)):
      print "GNURadio: Invalid radio source tuning frequency - %f" % tuningFreq
      return None
    print "Configured Source Centre Frequency = %e" % sdrTuningFreq
    return self

  def grBlock(self):
    return RadioSourceBlock.sdrSource

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
    plotTitle = "FFT Plot For '%s' Block" % compName
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
# Implements a low pass filter block with configurable cutoff frequency.
#
class LowPassFilterBlock(FlowGraphBlock):
  def __init__(self):
    FlowGraphBlock.__init__(self)

  def setup(self, params):
    if (len(params) != 2):
      print "GNURadio: Invalid number of low pass filter parameters"
      return None
    try:
      sampleRate = float(params[0])
      cutoffFreq = float(params[1])
    except ValueError, msg:
      print "GNURadio: Invalid low pass filter parameter - %s" % msg
      return None
    if ((cutoffFreq <= 0) or (cutoffFreq >= sampleRate/2)):
      print "GNURadio: Low pass cutoff frequency out of range"
      return None

    # Calculate the FIR filter taps using the Blackman-Harris window method.
    transitionWidth = sampleRate/25
    filterTaps = filter.firdes.low_pass(1.0, sampleRate,
      cutoffFreq, transitionWidth, filter.firdes.WIN_BLACKMAN_HARRIS)
    print "Generated FIR filter with %d taps" % len(filterTaps)
    self.firFilter = filter.fir_filter_ccf(1, filterTaps)
    return self

  def grBlock(self):
    return self.firFilter

#
# Implements the flow graph. On initialisation ensures that the graph is reset
# to a known state and builds a mapping of component types to their associated
# creation functions.
#
class FlowGraph(gr.top_block):
  def __init__(self):
    gr.top_block.__init__(self, "Scratch Flow Graph")
    self.comps = {}
    self.compCreateFns = {}
    self.compCreateFns["RADIO-SOURCE"] = self._createRadioSource
    self.compCreateFns["DISPLAY-SINK"] = self._createDisplaySink
    self.compCreateFns["LOW-PASS-FILTER"] = self._createLowPassFilter

  # Add a new radio source data block to the hierarchy. This uses the Lime
  # Microsystems SoapySDR driver.
  def _createRadioSource(self, compName, params):
    radioSourceBlock = RadioSourceBlock()
    return radioSourceBlock.setup(params)

  # Create a new display sink. This is currently limited to a simple FFT
  # display, but more advanced options can be included at a later date
  def _createDisplaySink(self, compName, params):
    displaySinkBlock = DisplaySinkFreqBlock()
    return displaySinkBlock.setup(compName, params)

  # Create a new low pass filter. This is currently limited in terms of
  # configuration options to specifying the 3dB cutoff point.
  def _createLowPassFilter(self, compName, params):
    filterBlock = LowPassFilterBlock()
    return filterBlock.setup(params)

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
  def __init__(self, parent, commandQueue):
    QtCore.QObject.__init__(self, parent)
    self.cmdQueue = commandQueue
    self.flowGraph = FlowGraph()
    self.radioRunning = False
    self.timerId = self.startTimer(500)

  def _processInteractiveCommands(self, command):
    print "Interactive command: %s" % command
    handled = False

    if (not handled):
      print "GNURadio: Unhandled interactive command - %s" % command
    return handled

  def _processSetupCommands(self, command):
    print "Setup command: %s" % command
    handled = False
    cmdTerms = command.split()
    command = cmdTerms.pop(0)

    # Create a new block.
    if (command == "CREATE"):
      handled = self.flowGraph.createComponent(cmdTerms)

    # Connect existing blocks.
    elif (command == "CONNECT"):
      handled = self.flowGraph.connectComponents(cmdTerms)

    if (not handled):
      print "GNURadio: Unhandled setup command - %s" % command
    return handled

  # Parses individual commands as they are removed from the command queue.
  def _parseCommand(self, command):
    handled = False
    print "CMD : " + command

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
        print "Read command : ", cmd
        self.cmdQueue.put(cmd)
        while (self.cmdQueue.full()):
          time.sleep(0.5)

def main():
  qapp = QtGui.QApplication(sys.argv)
  cmdQueue = Queue(8)
  cmdReader = CommandReader(cmdQueue)
  cmdReader.start()
  cmdParser = CommandParser(qapp, cmdQueue)
  qapp.exec_()

if __name__ == '__main__':
  try:
    main()
  except [[KeyboardInterrupt]]:
    pass
