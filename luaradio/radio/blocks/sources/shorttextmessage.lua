---
-- Source a sequence of short text messages from a file to be used as payload
-- data.
--

local ffi = require('ffi')

local block = require('radio.core.block')
local types = require('radio.types')

local paddingLen = 128

--- The libc functions used by this process.
ffi.cdef[[
    int open(const char* pathname, int flags);
    int close(int fd);
    int read(int fd, void* buf, size_t count);
]]
local O_NONBLOCK = 2048
local C_BUF_SIZE = 1024

local ShortTextMessageSource = block.factory("ShortTextMessageSource")

function ShortTextMessageSource:instantiate(file, rate)
    if type(file) == "string" then
        self.filename = file
    else
        self.file = assert(file, "Invalid argument #1 (file name)")
    end
    self.rate = assert(rate, "Missing argument #2 (rate)")
    self:add_type_signature({}, {block.Output("out", types.Byte)})
end

function ShortTextMessageSource:get_rate()
    print ("Short text message rate = ", self.rate)
    return self.rate
end

function ShortTextMessageSource:initialize()
    if self.filename then
        self.file = ffi.C.open(self.filename, O_NONBLOCK)
        if self.file == nil then
            error("open(): " .. ffi.string(ffi.C.strerror(ffi.errno())))
        end
    end

    -- Register open file
    self.files[self.file] = true

    -- Allocate C buffer
    self.cbufOffset = 0
    self.cbufLength = 0
    self.cbufArray = ffi.new('uint8_t[?]', C_BUF_SIZE)

    -- Allocate message buffer
    self.offset = 1;
    self.buffer = types.Byte.vector()
    self.padding = types.Byte.vector()
    self.buffer:resize(paddingLen)
    self.padding:resize(paddingLen)
    for i = 0, paddingLen-1 do
        self.buffer.data[i] = types.Byte(0x00)
        self.padding.data[i] = types.Byte(0x00)
    end

    -- Set slow polling flag.
    self.slowPolling = true
end

local function getNextChar (source)
    local nextChar = -1

    -- Read new data block if required
    if (source.cbufOffset == source.cbufLength) then
        source.cbufOffset = 0
        local nbytes = ffi.C.read(source.file, source.cbufArray, C_BUF_SIZE)
        if (nbytes > 0) then
            source.cbufLength = nbytes
        else
            source.cbufLength = 0
        end
    end

    -- Get next character if available
    if (source.cbufOffset < source.cbufLength) then
        nextChar = source.cbufArray[source.cbufOffset]
        source.cbufOffset = source.cbufOffset + 1
    end

    return nextChar
end

function ShortTextMessageSource:process()
    local buffer = self.buffer:resize(paddingLen + 256)

    -- Read in individual characters if available.
    local messageLen = 0
    local nextChar = getNextChar(self)

    -- Implement slow polling for the next message. This prevents further data
    -- output which may force an underflow condition on the radio output.
    if (self.slowPolling) then
        while (nextChar < 0) do
            os.execute("sleep 1")
            nextChar = getNextChar(self)
        end
        self.slowPolling = false
    end

    while (nextChar >= 0) and (messageLen == 0) do
        if (nextChar == 0x0A) then
            messageLen = self.offset
            self.offset = 1
        else
            if (self.offset < 256) then
                buffer.data[paddingLen + self.offset] = types.Byte(nextChar)
                self.offset = self.offset + 1
            end
            nextChar = getNextChar(self)
        end
    end

    -- Insert fixed size idle sequence, discarding oversize messages
    if (messageLen == 0) or (messageLen > 240) then
        self.slowPolling = true
        return self.padding

    -- Return message buffer
    else
        buffer:resize(paddingLen + messageLen)
        buffer.data[paddingLen] = types.Byte(messageLen-1)
        return buffer
    end
end

function ShortTextMessageSource:cleanup()
    if self.filename then
        if ffi.C.close(self.file) ~= 0 then
            error("close(): " .. ffi.string(ffi.C.strerror(ffi.errno())))
        end
    end
end

return ShortTextMessageSource
