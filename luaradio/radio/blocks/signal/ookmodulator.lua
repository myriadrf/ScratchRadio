---
-- Implements a simple On/Off Keying modulator, where the input is a sequence
-- of bits that will be encoded as off (0) or on (1), where the number of
-- output samples per bit can be configured using the 'upsamplingFactor'
-- parameter and the modulation frequency can be selected as an integer multiple
-- of the bit rate using the 'modulationRate' parameter.
--
-- @category Modulator
-- @block OokModulatorBlock
-- @tparam[opt=8] int upsamplingFactor Upsampling factor relative to bit rate.
-- @tparam[opt=4] int modulationRate Modulation rate relative to bit rate.
--
-- @signature in:Bit > out:Float32
--
-- @usage
-- local modulator = radio.OokModulatorBlock(factor, rate)

local ffi = require('ffi')

local block = require('radio.core.block')
local types = require('radio.types')

local OokModulatorBlock = block.factory("OokModulatorBlock")

function OokModulatorBlock:instantiate(upsamplingFactor, modulationRate)
    if (upsamplingFactor < 2) then
        error ("Invalid upsampling factor")
    elseif (2 * modulationRate > upsamplingFactor) then
        error ("Invalid modulation rate")
    else
        self.upscale = upsamplingFactor
    end

    -- Build lookup tables for bit encoding
    self.mod0Table = types.Float32.vector(upsamplingFactor)
    self.mod1Table = types.Float32.vector(upsamplingFactor)
    for i = 0, upsamplingFactor - 1 do
        local modTableEntry
        if (4 * modulationRate > upsamplingFactor) then
            modTableEntry = math.cos(2 * i * math.pi * modulationRate / upsamplingFactor)
        else
            modTableEntry = math.sin(2 * i * math.pi * modulationRate / upsamplingFactor)
        end
        self.mod0Table.data[i] = types.Float32(0)
        self.mod1Table.data[i] = types.Float32(modTableEntry)
    end
    self.modTableSize = upsamplingFactor * ffi.sizeof(types.Float32(0))

    self:add_type_signature({block.Input("in", types.Bit)}, {block.Output("out", types.Float32)})
end

function OokModulatorBlock:initialize()
    self.out = types.Float32.vector()
end

function OokModulatorBlock:get_rate()
    return block.Block.get_rate(self) * self.upscale
end

ffi.cdef[[
void *memcpy(void *dest, const void *src, size_t n);
void *memset(void *dest, int c, size_t n);
]]

function OokModulatorBlock:process(x)
    local out = self.out:resize(self.upscale*x.length)

    for i = 0, x.length-1 do
        local thisBit = x.data[i]
        if thisBit.value == 0 then
            ffi.C.memcpy(out.data[i*self.upscale], self.mod0Table.data[0], self.modTableSize)
        else
            ffi.C.memcpy(out.data[i*self.upscale], self.mod1Table.data[0], self.modTableSize)
        end
    end

    return out
end

return OokModulatorBlock
