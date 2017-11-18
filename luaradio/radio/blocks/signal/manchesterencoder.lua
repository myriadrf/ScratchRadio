---
-- Encode an input bitstream using Manchester encoding. May be a continuous
-- sequence of input bits formatted as in:Bit or a sequence of frames formatted
-- as in:Byte, where 0x00 and 0x01 represent valid bits and other values
-- represent idle bits.
--
-- @category Digital
-- @block ManchesterEncoderBlock
-- @tparam[opt=false] bool invert Invert the output.
-- @tparam[opt=false] bool invertIdle Invert the idle output.
--
-- @signature in:Bit > out:Bit
-- @signature in:Byte > out:Bit
--
-- @usage
-- local manchester_encoder = radio.ManchesterEncoderBlock()

local block = require('radio.core.block')
local types = require('radio.types')

local ManchesterEncoderBlock = block.factory("ManchesterEncoderBlock")

function ManchesterEncoderBlock:instantiate(invert, invertIdle)
    self.invert = invert or false
    self.invertIdle = invertIdle or false

    self:add_type_signature({block.Input("in", types.Bit)}, {block.Output("out", types.Bit)})
    self:add_type_signature({block.Input("in", types.Byte)}, {block.Output("out", types.Bit)})
end

function ManchesterEncoderBlock:initialize()
    self.out = types.Bit.vector()
end

function ManchesterEncoderBlock:get_rate()
    return block.Block.get_rate(self) * 2
end

function ManchesterEncoderBlock:process(x)
    local out = self.out:resize(2*x.length)

    for i = 0, x.length-1 do
        local thisBit = x.data[i]
        if thisBit.value == 0 then
            -- 0 to 1 transition
            out.data[2*i] = types.Bit(self.invert and 1 or 0)
            out.data[2*i+1] = types.Bit(self.invert and 0 or 1)
        elseif thisBit.value == 1 then
            -- 1 to 0 transition
            out.data[2*i] = types.Bit(self.invert and 0 or 1)
            out.data[2*i+1] = types.Bit(self.invert and 1 or 0)
        else
            -- idle insertion
            out.data[2*i] = types.Bit(self.invertIdle and 1 or 0)
            out.data[2*i+1] = types.Bit(self.invertIdle and 1 or 0)
        end
    end

    return out
end

return ManchesterEncoderBlock
