#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 <+YOU OR YOUR COMPANY+>.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import numpy
from gnuradio import gr

class simple_deframer(gr.basic_block):
    """
    docstring for block simple_deframer
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="simple_deframer",
            in_sig=[numpy.uint8],
            out_sig=[numpy.uint8])
        self.idle = True
        self.msgReceived = False
        self.header = 0
        self.msgByteCount = 0
        self.msgLength = 0
        self.msgBuffer = range(255)
        self.checksums = [0, 0]

    def forecast(self, noutput_items, ninput_items_required):
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items * 8

    def getDataByte(self, in0, inputIndex):
        byteShift = 0
        for i in range(8):
            byteShift >>= 1
            if in0[inputIndex+i] != 0:
                byteShift |= 0x80
        return byteShift

    def updateChecksum(self, byteData):
        self.checksums[0] = self.checksums[0] + byteData
        self.checksums[1] = self.checksums[1] + self.checksums[0]

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        inputIndex = 0
        outputIndex = 0
        while (inputIndex <= (len(in0) - 8)) and (outputIndex < len(out)):

            # If a valid message has been received, copy it from the
            # local buffer to the output.
            if self.msgReceived:
                out[outputIndex] = self.msgBuffer[self.msgByteCount]
                outputIndex += 1
                self.msgByteCount += 1
                if self.msgByteCount == self.msgLength:
                    self.idle = True
                    self.msgReceived = False
                    self.msgLength = 0

            # In the idle state, search for the start of frame header.
            # Matches on the byte sequence 0x7E, 0x81, 0xC3, 0x3C.
            elif self.idle:
                if in0[inputIndex] == 0:
                    if self.header == 0x3CC3817E:
                        self.idle = False
                        self.header = 0
                    else:
                        self.header >>= 1
                else:
                    self.header = 0x40000000 | (self.header >> 1)
                inputIndex += 1

            # Get the number of bytes in the frame.
            elif self.msgLength == 0:
                self.msgByteCount = 0
                self.msgLength = self.getDataByte(in0, inputIndex)
                inputIndex += 8
                self.checksums = [0, 0]
                self.updateChecksum(self.msgLength)
                if self.msgLength == 0:
                    self.idle = True

            # Read the specified number of bytes from the input
            elif self.msgByteCount < self.msgLength:
                inputData = self.getDataByte(in0, inputIndex)
                inputIndex += 8
                self.msgBuffer[self.msgByteCount] = inputData
                self.msgByteCount += 1
                self.updateChecksum(inputData)

            # Validate first checksum byte.
            elif self.msgByteCount == self.msgLength:
                checkByte = self.getDataByte(in0, inputIndex)
                inputIndex += 8
                if checkByte == self.checksums[0] % 255:
                    self.msgByteCount += 1
                else:
                    self.idle = True
                    self.msgLength = 0

            # Validate second checksum byte.
            else:
                checkByte = self.getDataByte(in0, inputIndex)
                inputIndex += 8
                if checkByte == self.checksums[1] % 255:
                    out[outputIndex] = self.msgLength
                    outputIndex += 1
                    self.msgReceived = True
                    self.msgByteCount = 0
                else:
                    self.idle = True
                    self.msgLength = 0

        self.consume_each(inputIndex)
        return outputIndex
