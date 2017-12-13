--
-- Implements a LUA radio control module which accepts commands from
-- a given file (or stdin) and creates/connects the specified LuaRadio
-- blocks as appropriate. This may be used to interactively use LuaRadio
-- or control it via a simple command script.
--

local radio = require('radio')

local minSampleRate = 100000
local maxSampleRate = 4000000

--
-- Split the command input into command name and parameters.
--
local function splitParams (cmd)
  local matcher = string.gmatch(cmd, "%S+")
  local command = matcher()
  local params = {}
  for param in matcher do
    params[#params + 1] = param
  end
  return command, params
end

--
-- Add a new radio source data block to the hierarchy. This uses the Lime
-- Microsystems SoapySDR driver which is configured for a frontend filter
-- bandwidth of 1.5 MHz.
--
local function createRadioSource (compName, params, comps)
  local handled = false
  local tuningFreq = tonumber (table.remove(params, 1))
  local sampleRate = tonumber (table.remove(params, 1))
  if (tuningFreq and (tuningFreq > 0) and sampleRate and
    (sampleRate >= minSampleRate) and (sampleRate <= maxSampleRate)) then
    handled = true
    local complexToRealBlock = radio.ComplexToRealBlock()
    local radioBlock = radio.SoapySDRSource("lime", tuningFreq, sampleRate, {bandwidth = 1.5e6, gain = 80})
    local compositeBlock = radio.CompositeBlock()
    compositeBlock:add_type_signature({}, {radio.block.Output("out", radio.types.Float32)})
    compositeBlock:connect(radioBlock, complexToRealBlock)
    compositeBlock:connect(compositeBlock, 'out', complexToRealBlock, 'out')
    comps[compName] = {
      isRadioSource = true,
      inputs = {},
      outputs = {["out"]=true},
      block = compositeBlock}
  end
  return handled
end

--
-- Add a new radio sink block to the hierarchy. This uses the Lime Microsystems
-- SoapySDR driver which is configured for a frontend filter bandwidth of 5 MHz.
--
local function createRadioSink (compName, params, comps)
  local handled = false
  local tuningFreq = tonumber (table.remove(params, 1))
  local sampleRate = tonumber (table.remove(params, 1))
  if (tuningFreq and (tuningFreq > 0) and sampleRate and
    (sampleRate >= minSampleRate) and (sampleRate <= maxSampleRate)) then
    handled = true
    local realToComplexBlock = radio.RealToComplexBlock()
    local radioBlock = radio.SoapySDRSink("lime", tuningFreq, {bandwidth = 5e6, gain = 40, antenna = "BAND2"})
    local compositeBlock = radio.CompositeBlock()
    compositeBlock:add_type_signature({radio.block.Input("in", radio.types.Float32)}, {})
    compositeBlock:connect(realToComplexBlock, radioBlock)
    compositeBlock:connect(compositeBlock, 'in', realToComplexBlock, 'in')
    comps[compName] = {
      isRadioSource = true,
      inputs = {["in"]=true},
      outputs = {},
      block = compositeBlock}
  end
  return handled
end

--
-- Add a new display sink to the hierarchy. This uses the GNU Plot spectrum
-- display. TODO: Add some configuration parameters.
--
local function createDisplaySink (compName, params, comps)
  local handled = true
  comps[compName] = {
    isDisplaySink = true,
    inputs = {["in"]=true},
    outputs = {},
    block = radio.GnuplotSpectrumSink(2048,
      "Spectrum", {yrange = {-120, -40}})}
  return handled
end

--
-- Add a new message source to the hierarchy using the specified source file.
--
local function createMessageSource (compName, params, comps)
  local handled = false
  local sourceFileName = table.remove(params, 1)
  local cpsRate = tonumber (table.remove(params, 1))
  if (sourceFileName and cpsRate) then
    handled = true
    comps[compName] = {
      isMessageSource = true,
      inputs = {},
      outputs = {["out"]=true},
      block = radio.ShortTextMessageSource(sourceFileName, cpsRate)}
  end
  return handled
end

--
-- Add a new message sink to the hierarchy using the specified sink file.
--
local function createMessageSink (compName, params, comps)
  local handled = false
  local sinkFileName = table.remove(params, 1)
  if (sinkFileName) then
    handled = true
    comps[compName] = {
      isMessageSink = true,
      inputs = {["in"]=true},
      outputs = {},
      block = radio.ShortTextMessageSink(sinkFileName)}
  end
  return handled
end

--
-- Add a new simple framer to the hierarchy.
--
local function createSimpleFramer (compName, params, comps)
  local handled = true
  comps[compName] = {
    inputs = {["in"]=true},
    outputs = {["out"]=true},
    block = radio.SimpleFramerBlock()}
  return handled
end

--
-- Add a new simple deframer to the hierarchy.
--
local function createSimpleDeframer (compName, params, comps)
  local handled = true
  comps[compName] = {
    inputs = {["in"]=true},
    outputs = {["out"]=true},
    block = radio.SimpleDeframerBlock()}
  return handled
end

--
-- Add a new Manchester encoder block to the hierarchy.
--
local function createManchesterEncoder (compName, params, comps)
  local handled = true
  comps[compName] = {
    inputs = {["in"]=true},
    outputs = {["out"]=true},
    block = radio.ManchesterEncoderBlock()}
  return handled
end

--
-- Add a new Manchester decoder block to the hierarchy.
--
local function createManchesterDecoder (compName, params, comps)
  local handled = true
  comps[compName] = {
    inputs = {["in"]=true},
    outputs = {["out"]=true},
    block = radio.ManchesterDecoderBlock()}
  return handled
end

--
-- Add a new OOK modulator block to the hierarchy.
--
local function createOokModulator (compName, params, comps)
  local handled = false
  local upsamplingFactor = tonumber (table.remove(params, 1))
  local modulationRate = tonumber (table.remove(params, 1))
  if (upsamplingFactor and modulationRate) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.OokModulatorBlock(upsamplingFactor, modulationRate)}
  end
  return handled
end

--
-- Add a new OOK demodulator block to the hierarchy.
--
local function createOokDemodulator (compName, params, comps)
  local handled = false
  local baudRate = tonumber (table.remove(params, 1))
  if (baudRate) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.OokDemodulatorBlock(baudRate, false)}
  end
  return handled
end

--
-- Add a new bit rate sampler block to the hierarchy.
--
local function createBitRateSampler (compName, params, comps)
  local handled = false
  local baudRate = tonumber (table.remove(params, 1))
  if (baudRate) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.BitRateSamplerBlock(baudRate, 0)}
  end
  return handled
end

--
-- Add a new real valued file source block to the hierarchy.
--
local function createRealFileSource (compName, params, comps)
  local handled = false
  local fileName = table.remove(params, 1)
  local sampleRate = tonumber (table.remove(params, 1))
  if (fileName and sampleRate) then
    handled = true
    comps[compName] = {
      inputs = {},
      outputs = {["out"]=true},
      block = radio.RealFileSource(fileName, "s8", sampleRate, true)}
  end
  return handled
end

--
-- Add a new real valued file sink block to the hierarchy.
--
local function createRealFileSink (compName, params, comps)
  local handled = false
  local fileName = table.remove(params, 1)
  if (fileName) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {},
      block = radio.RealFileSink(fileName, "s8")}
  end
  return handled
end

--
-- Add a new low pass filter block to the hierarchy.
--
local function createLowPassFilter (compName, params, comps)
  local handled = false
  local bandwidth = tonumber (table.remove(params, 1))
  if (bandwidth and (bandwidth < 1) and (bandwidth > 0)) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.LowpassFilterBlock(127, bandwidth, 1)}
  end
  return handled
end

--
-- Add a new band pass filter block to the hierarchy.
--
local function createBandPassFilter (compName, params, comps)
  local handled = false
  local lowCutoff = tonumber (table.remove(params, 1))
  local highCutoff = tonumber (table.remove(params, 1))
  if (lowCutoff and highCutoff and (lowCutoff > 0) and
    (highCutoff < 1) and (lowCutoff < highCutoff)) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.BandpassFilterBlock(127, {lowCutoff, highCutoff}, 1)}
  end
  return handled
end

--
-- Add a new decimation filter block to the hierarchy.
--
local function createDecimationFilter (compName, params, comps)
  local handled = false
  local decimationFactor = tonumber (table.remove(params, 1))
  if (decimationFactor) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.DecimatorBlock(decimationFactor)}
  end
  return handled
end

--
-- Add a new interpolation filter block to the hierarchy.
--
local function createInterpolationFilter (compName, params, comps)
  local handled = false
  local interpolationFactor = tonumber (table.remove(params, 1))
  if (interpolationFactor) then
    handled = true
    comps[compName] = {
      inputs = {["in"]=true},
      outputs = {["out"]=true},
      block = radio.InterpolatorBlock(interpolationFactor)}
  end
  return handled
end

--
-- Create a new component in the specified composite block.
--
local function createComponent (params, comps)
  local handled = false
  local compType = table.remove(params, 1)
  local compName = table.remove(params, 1)

  -- Check for valid component name and type.
  if ((compName == nil) or (compType == nil)) then
    io.write ("LuaRadio: Malformed CREATE command\n")

  -- Check for duplicate component names.
  elseif (comps[compName]) then
    io.write ("LuaRadio: Duplicate component name - ", compName, "\n")

  -- Create a new radio source component.
  elseif (compType == "RADIO-SOURCE") then
    handled = createRadioSource (compName, params, comps)

  -- Create a new radio sink component.
  elseif (compType == "RADIO-SINK") then
    handled = createRadioSink (compName, params, comps)

  -- Add a new spectrum display sink to the hierarchy.
  elseif (compType == "DISPLAY-SINK") then
    handled = createDisplaySink (compName, params, comps)

  -- Add a new message source component to the hierarchy.
  elseif (compType == "MESSAGE-SOURCE") then
    handled = createMessageSource (compName, params, comps)

  -- Add a new message sink component to the hierarchy.
  elseif (compType == "MESSAGE-SINK") then
    handled = createMessageSink (compName, params, comps)

  -- Add a simple framer component to the hierarchy.
  elseif (compType == "SIMPLE-FRAMER") then
    handled = createSimpleFramer (compName, params, comps)

  -- Add a simple deframer component to the hierarchy.
  elseif (compType == "SIMPLE-DEFRAMER") then
    handled = createSimpleDeframer (compName, params, comps)

  -- Add a Manchester encoding block to the hierarchy.
  elseif (compType == "MANCHESTER-ENCODER") then
    handled = createManchesterEncoder (compName, params, comps)

  -- Add a Manchester decoding block to the hierarchy.
  elseif (compType == "MANCHESTER-DECODER") then
    handled = createManchesterDecoder (compName, params, comps)

  -- Add a OOK modulation block to the hierarchy.
  elseif (compType == "OOK-MODULATOR") then
    handled = createOokModulator (compName, params, comps)

  -- Add an OOK demodulator block to the hierarchy.
  elseif (compType == "OOK-DEMODULATOR") then
    handled = createOokDemodulator (compName, params, comps)

  -- Add a bit rate sampling block.
  elseif (compType == "BIT-RATE-SAMPLER") then
    handled = createBitRateSampler (compName, params, comps)

  -- Add a sample file source block.
  elseif (compType == "REAL-FILE-SOURCE") then
    handled = createRealFileSource (compName, params, comps)

  -- Add a sample file sink block.
  elseif (compType == "REAL-FILE-SINK") then
    handled = createRealFileSink (compName, params, comps)

  -- Add a low pass filter block.
  elseif (compType == "LOW-PASS-FILTER") then
    handled = createLowPassFilter (compName, params, comps)

  -- Add a band pass filter block.
  elseif (compType == "BAND-PASS-FILTER") then
    handled = createBandPassFilter (compName, params, comps)

  -- Add a decimation filter block.
  elseif (compType == "DECIMATION-FILTER") then
    handled = createDecimationFilter (compName, params, comps)

  -- Add an interpolation filter block.
  elseif (compType == "INTERPOLATION-FILTER") then
    handled = createInterpolationFilter (compName, params, comps)
  end

  return handled
end

--
-- Connect two or more components in the specified composite block.
--
local function connectComponents (params, topBlock, comps)
  local producerName = table.remove(params, 1)
  local producerPort = table.remove(params, 1)
  local consumerName = table.remove(params, 1)
  local consumerPort = table.remove(params, 1)

  -- Check for valid components and ports.
  if ((producerName == nil) or (producerPort == nil) or
    (consumerName == nil) or (consumerPort == nil)) then
    io.write ("LuaRadio: Malformed CONNECT command\n")
    return false
  end

  -- Check for components being present.
  local producer = comps[producerName]
  local consumer = comps[consumerName]
  if (producer == nil) then
    io.write ("LuaRadio: Unknown producer in CONNECT - ", producerName, "\n")
    return false
  elseif (consumer == nil) then
    io.write ("LuaRadio: Unknown consumer in CONNECT - ", consumerName, "\n")
    return false
  end

  -- Check for supported output port name.
  if (not producer.outputs[producerPort]) then
    io.write ("LuaRadio: Unknown producer port in CONNECT - ", producerPort, "\n")
    return false
  elseif (not consumer.inputs[consumerPort]) then
    io.write ("LuaRadio: Unknown consumer port in CONNECT - ", consumerPort, "\n")
    return false
  end

  -- Connect the producer and consumer blocks in the toplevel block.
  topBlock:connect(producer.block, producerPort, consumer.block, consumerPort)
  return true
end

--
-- Provides processing for setup commands received during radio
-- configuration.
--
local function processSetupCommands (cmd, topBlock, comps)
  local handled = false
  local command, params = splitParams (cmd)

  print ("Setup command : ", command)
  for i = 1, #params do
    print ("Params  : ", params[i])
  end

  -- Create a new block.
  if (command == "CREATE") then
    handled = createComponent (params, comps)
  elseif (command == "CONNECT") then
    handled = connectComponents (params, topBlock, comps)
  end

  if (not handled) then
    io.write ("LuaRadio: Unhandled setup command - ", cmd, "\n")
  end
  return handled
end

--
-- Provides processing for interactive commands received while the radio
-- is running.
--
local function processInteractiveCommands (cmd, topBlock, comps)
  local handled = false

  if (not handled) then
    io.write ("LuaRadio: Unhandled interactive command - ", cmd, "\n")
  end
end

--
-- Provides main processing loop for the LuaRadio control interface.
--
local function luaRadioControl ()

  -- Create the top-level table which is used to hold all the components
  -- which are to be placed in the 'top' composite block.
  local comps = {}
  local topBlock = radio.CompositeBlock()

  -- Loop indefinitely reading command lines from the input. Invalid
  -- commands are logged to the standard output.
  while (true) do
    local command
    local doneSleep = false
    repeat
      command = io.read()
      if (command == nil) then
        os.execute("sleep 1")
        io.write (".")
        doneSleep = true
      end
    until (command ~= nil)
    if (doneSleep) then
      io.write ("\n")
    end

    -- Force reset, which stops the radio and deletes all components.
    if (command == "RESET") then
      if (topBlock:status().running) then
        topBlock:stop()
      end
      comps = {}
      topBlock = radio.CompositeBlock()
      io.write ("LuaRadio: RESET\n")

    -- Start the radio running if it is currently idle.
    elseif (command == "START") then
      if (not topBlock:status().running) then
        io.write ("LuaRadio: STARTING\n")
        topBlock:start()
        io.write ("LuaRadio: STARTED\n")
      end

    -- Stop the radio from running.
    elseif (command == "STOP") then
      if (topBlock:status().running) then
        io.write ("LuaRadio: STOPPING\n")
        topBlock:stop()
        io.write ("LuaRadio: STOPPED\n")
      else
        io.write ("LuaRadio: STOP (NOT RUNNING)\n")
      end

    -- Process interactive commands for running radio.
    elseif (topBlock:status().running) then
      processInteractiveCommands (command, topBlock, comps)

    -- Process radio setup commands.
    else
      processSetupCommands (command, topBlock, comps)
    end
  end
end

--
-- Run the control handler using the input from the specified file, or
-- default to stdin.
--
if (arg[1] ~= nil) then
  io.input(arg[1])
end

luaRadioControl()
