---
-- Implements a bit rate sampler for asynchronous input bit streams, where the
-- input is a sequence of samples at some multiple of the nominal bit rate and
-- the output is the sampled bit sequence. This effectively combines the
-- functionality of the existing zero crossing timing recovery block, sampler
-- and symbol slicer block in a way which doesn't cause mult-path data flow
-- lockup problems when stopping the radio.
--
-- @category Digital Conversion
-- @block BitRateSamplerBlock
-- @tparam number baudrate Baudrate in symbols per second
-- @tparam[opt=false] number threshold Slicing threshold (default 0)
--
-- @signature in:Float32 > out:Bit
--
-- @usage
-- local bitRateSampler = radio.BitRateSamplerBlock(baudrate, threshold)

local block = require('radio.core.block')
local types = require('radio.types')

local BitRateSamplerBlock = block.factory("BitRateSamplerBlock")

function BitRateSamplerBlock:instantiate(baudrate, threshold)
    self.baudrate = assert(baudrate, "Missing argument #1 (baudrate)")
    self.threshold = threshold or 0

    self:add_type_signature({block.Input("in", types.Float32)}, {block.Output("out", types.Bit)})
end

function BitRateSamplerBlock:initialize()
    inputSampleRate = block.Block.get_rate(self)
    downsamplingFactor = inputSampleRate / self.baudrate
    print ("Bit rate sampler oversampling factor " .. inputSampleRate .. "/" .. self.baudrate)
    if (downsamplingFactor < 4) then
        error ("Invalid oversampling factor " .. inputSampleRate .. "/" .. self.baudrate)
    end

    self.downsample = downsamplingFactor
    self.sampleInterval = downsamplingFactor - 1
    self.samplePoint = downsamplingFactor / 2
    self.sampleCount = 0
    self.lastSampleVal = 0
    self.out = types.Bit.vector()
end

function BitRateSamplerBlock:get_rate()
    print ("Sampled bit rate: " .. self.baudrate)
    return self.baudrate
end

function BitRateSamplerBlock:process(x)
    local thisSample = 0
    local lastSample = self.lastSampleVal
    local threshold = self.threshold

    local out = self.out:resize(1 + x.length / self.sampleInterval)
    out:resize(0)

    for i = 0, x.length-1 do
        thisSample = x.data[i].value

        -- Update sample counter, aligning to threshold crossing events.
        if (((thisSample - threshold) * (lastSample - threshold)) <= 0) then
            self.sampleCount = 0
        elseif (self.sampleCount == self.sampleInterval) then
            self.sampleCount = 0
        else
            self.sampleCount = self.sampleCount + 1
        end

        -- Perform bit sampling at specified sample point.
        if (self.sampleCount == self.samplePoint) then
            local bitValue = (thisSample >= self.threshold) and 1 or 0
            out:append(types.Bit(bitValue))
        end

        lastSample = thisSample
    end

    self.lastSampleVal = thisSample
    return out
end

return BitRateSamplerBlock
