--
-- Implements a LUA radio control module which accepts commands from
-- a given file (or stdin) and creates/connects the specified LuaRadio
-- blocks as appropriate. This may be used to interactively use LuaRadio
-- or control it via a simple command script.
--

local radio = require('radio')

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
-- Add a new radio source data block to the hierarchy. This uses the
-- Lime Microsystems SoapySDR driver which is configured for a sample
-- rate of 4 MHz and a frontend filter bandwidth of 1.5 MHz. The low
-- frequency antenna A is used as the input.
--
local function createRadioSource (compName, params, comps)
  local handled = false
  local tuningFreq = tonumber (table.remove(params, 1))
  if (tuningFreq) then
    handled = true
    comps[compName] = {
      isRadioSource = true,
      inputs = {},
      outputs = {["out"]=true},
      block = radio.SoapySDRSource("lime", tuningFreq, 4e6,
        {gain = 80, bandwidth = 1.5e6, antenna="LNAL"})}
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
  if (sourceFileName) then
    handled = true
    comps[compName] = {
      isMessageSource = true,
      inputs = {},
      outputs = {["out"]=true},
      block = radio.ShortTextMessageSource(sourceFileName, 1200)}
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
    repeat
      command = io.read()
    until (command ~= nil)

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
        topBlock:stop()
        io.write ("LuaRadio: STOP\n")
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
