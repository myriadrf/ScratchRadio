---
-- Sink a sequence of short text messages into a file as they are extracted
-- from payload data.
--

local block = require('radio.core.block')
local types = require('radio.types')

local ShortTextMessageSink = block.factory("ShortTextMessageSink")

function ShortTextMessageSink:instantiate(file)
    if type(file) == "string" then
        self.filename = file
    else
        self.file = assert(file, "Invalid argument #1 (file name)")
    end

    self:add_type_signature({block.Input("in", types.Byte)}, {})
end

function ShortTextMessageSink:initialize()
    self.file = assert(io.open(self.filename, "a"))
    self.txCount = 0

    -- Register open file
    self.files[self.file] = true
end

function ShortTextMessageSink:process(x)
    for i = 0, x.length-1 do
        local rxByte = x.data[i].value

        -- process length byte
        if (self.txCount == 0) then
            self.txCount = rxByte

        -- write data byte
        else
            self.txCount = self.txCount - 1
            self.file:write(string.char(rxByte))
            if (self.txCount == 0) then
                self.file:write("\n")
                self.file:flush()
            end
        end
    end
end

return ShortTextMessageSink
