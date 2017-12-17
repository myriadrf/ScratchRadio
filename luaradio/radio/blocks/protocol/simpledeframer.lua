---
-- Implements a simple deframer block which accepts a bitstream formatted as
-- in:Bit. The input consists of frames formatted as follows:
--   Preamble       : 0x55 0xAA 0x55 0xAA 0x55 0xAA
--   Start of frame : 0x7E 0x81 0xC3 0x3C
--   Frame length   : Number of bytes in body (excludes length and CRC bytes)
--   Payload        : Payload data (integer number of bytes, at least one)
--   Checksum       : Checksum over all payload bytes including the length byte
--                    using the 16-bit modulo 255 Fletcher checksum.
-- Deframer outputs are a sequence of bytes representing the deframed messages,
-- where the first byte is the message length and subsequent bytes are the
-- message contents.
--
-- @category Protocol
-- @block SimpleDeframerBlock
--
-- @signature in:Bit > out:Byte
--
-- @usage
-- local deframer = radio.SimpleDeframerBlock()

local bit = require('bit')

local block = require('radio.core.block')
local types = require('radio.types')

local states = { idle=1, getLength=2, getPayload=3, getCrc1=4, getCrc2=5 }

local SimpleDeframerBlock = block.factory("SimpleDeframerBlock")

function SimpleDeframerBlock:instantiate()
    self:add_type_signature({block.Input("in", types.Bit)}, {block.Output("out", types.Byte)})
    self:add_type_signature({block.Input("in", types.Byte)}, {block.Output("out", types.Byte)})
end

function SimpleDeframerBlock:initialize()
    self.out = types.Byte.vector()
    self.state = states.idle
    self.byteCount = 0
    self.bitCount = 0
    self.rxByte = 0
    self.rxSync = 0
    self.rxMessage = types.Byte.vector()
    self.rxOffset = 0
    self.checksums = {0, 0}
end

function SimpleDeframerBlock:get_rate()
    return block.Block.get_rate(self) / 8
end

local function updateChecksum (checksums, byteData)
    checksums[1] = checksums[1] + byteData
    checksums[2] = checksums[2] + checksums[1]
    return checksums
end

function SimpleDeframerBlock:process(x)
    local out = self.out:resize(0)
    local offset = 0

    for i = 0, x.length-1 do
        self.rxByte = bit.rshift(self.rxByte, 1)
        self.rxSync = bit.rshift(self.rxSync, 1)
        if (x.data[i].value ~= 0) then
            self.rxByte = bit.bor(self.rxByte, 0x80)
            self.rxSync = bit.bor(self.rxSync, 0x80000000)
        end
        self.bitCount = bit.band(self.bitCount+1, 0x7)

        local rxByte = self.rxByte
        local rxMessage = self.rxMessage

        -- search for start of frame sync word
        if (self.state == states.idle) then
            if (self.rxSync == 0x3CC3817E) then
              self.state = states.getLength
              self.bitCount = 0
            end

        -- get the message length byte
        elseif (self.state == states.getLength) then
            if (self.bitCount == 0) then
                self.state = states.getPayload
                self.byteCount = rxByte
                rxMessage:resize(1+rxByte)
                rxMessage.data[0] = types.Byte(rxByte)
                self.rxOffset = 1
                self.checksums = updateChecksum({0, 0}, rxByte)
            end

        -- process payload body
        elseif (self.state == states.getPayload) then
            if (self.bitCount == 0) then
                rxMessage.data[self.rxOffset] = types.Byte(rxByte)
                self.checksums = updateChecksum(self.checksums, rxByte)
                if (self.rxOffset == self.byteCount) then
                    self.state = states.getCrc1
                else
                    self.rxOffset = self.rxOffset + 1
                end
            end

        -- verify checksum 1
        elseif (self.state == states.getCrc1) then
            if (self.bitCount == 0) then
                if (rxByte == self.checksums[1] % 255) then
                    self.state = states.getCrc2
                else
                    self.state = states.idle
                end
            end

        -- verify checksum 2
        else
            if (self.bitCount == 0) then
                self.state = states.idle
                if (rxByte == self.checksums[2] % 255) then
                    out = self.out:resize(offset + rxMessage.length)
                    for j = 0, rxMessage.length-1 do
                        out.data[offset+j] = rxMessage.data[j]
                    end
                    offset = offset + rxMessage.length
                end
            end
        end
    end

    return out
end

return SimpleDeframerBlock
