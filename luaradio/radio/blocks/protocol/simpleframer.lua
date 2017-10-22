---
-- Implements a simple framer block which accepts a series of frame payloads
-- formatted as in:Byte. Inter-frame idle periods are indicated by byte values
-- of zero, and the first non-zero byte after the inter-frame idle period is
-- interpreted as a length byte which specifies the number of subsequent bytes
-- that form the message to be transmitted.
-- The output consists of frames formatted as follows:
--   Preamble       : 0x55 0x55 0x55
--   Start of frame : 0x7E
--   Frame length   : Number of bytes in body (excludes length and CRC bytes)
--   Payload        : Payload data (integer number of bytes, at least one)
--   CRC            : CRC over all payload bytes including the length byte
--                    (x16 + x14 + x12 + x11 + x8 + x5 + x4 + x2 + 1)
-- Frame outputs are a sequence of bytes where 0x00 and 0x01 represent valid
-- data bits and other values represent idle bits.
--
-- @category Protocol
-- @block SimpleFramerBlock
--
-- @signature in:Byte > out:Byte
--
-- @usage
-- local framer = radio.SimpleFramerBlock()

local bit = require('bit')

local block = require('radio.core.block')
local types = require('radio.types')

local SimpleFramerBlock = block.factory("SimpleFramerBlock")

function SimpleFramerBlock:instantiate()
    self:add_type_signature({block.Input("in", types.Byte)}, {block.Output("out", types.Byte)})
end

function SimpleFramerBlock:initialize()
    self.out = types.Byte.vector()
    self.idle = true
    self.byteCount = 0
    self.crc = 0x0000
end

local function sendDataByte (out, offset, byteData)
    local byteShift = byteData
    for i = 0, 7 do
        local bitValue = bit.band(byteShift,1)
        byteShift = bit.rshift(byteShift,1)
        out.data[8*offset+i] = types.Byte(bitValue)
    end
end

local function sendIdleByte (out, offset)
    for i = 0, 7 do
        out.data[8*offset+i] = types.Byte(0xFF)
    end
end

local function updateCrc (crc, byteData)
    -- TODO: This!
    return crc
end

function SimpleFramerBlock:process(x)
    local out = self.out:resize(x.length*8)
    local offset = 0

    for i = 0, x.length-1 do
        local thisByte = x.data[i]

        -- processes out of frame idle bytes until a size byte is detected
        if (self.idle) then
            if thisByte.value == 0x00 then
                -- idle insertion
                sendIdleByte(out, offset+i)
            else
                -- header insertion
                out = self.out:resize(self.out.length+32)
                sendDataByte(out, offset+i, 0x55)
                sendDataByte(out, offset+i+1, 0x55)
                sendDataByte(out, offset+i+2, 0x55)
                sendDataByte(out, offset+i+3, 0x7E)
                sendDataByte(out, offset+i+4, thisByte.value)
                offset = offset + 4
                self.idle = false
                self.byteCount = thisByte.value
                self.crc = updateCrc(0xFFFF, thisByte.value)
            end

        -- processes frame payload data until the end of frame
        else
            sendDataByte (out, offset+i, thisByte.value)
            self.byteCount = self.byteCount - 1
            self.crc = updateCrc(self.crc, thisByte.value)

            -- insert CRC at end of frame
            if self.byteCount == 0 then
                out = self.out:resize(self.out.length+32)
                sendDataByte(out, offset+i+1, bit.bnot(self.crc))
                sendDataByte(out, offset+i+2, bit.bnot(bit.rshift(self.crc, 8)))
                sendIdleByte(out, offset+i+3)
                sendIdleByte(out, offset+i+4)
                offset = offset + 4
                self.idle = true
            end
        end
    end

    return out
end

return SimpleFramerBlock
