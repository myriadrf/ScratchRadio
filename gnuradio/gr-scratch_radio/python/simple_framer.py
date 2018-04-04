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

class simple_framer(gr.basic_block):
    """
    docstring for block simple_framer
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="simple_framer",
            in_sig=[numpy.uint8],
            out_sig=[numpy.uint8])
        self.set_output_multiple(8)
        self.idle = True
        self.headerIndex = 0
        self.byteCount = 0
        self.checksums = [0, 0]
        self.header = (
            0xA5, 0xF0, 0xA5, 0xF0, 0xA5, 0xF0, 0x7E, 0x81, 0xC3, 0x3C)

    def forecast(self, noutput_items, ninput_items_required):
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items / 8

    def sendDataByte(self, out, offset, byteData):
        byteShift = byteData
        for i in range(8):
            bitValue = byteShift & 1
            byteShift >>= 1
            out[offset+i] = bitValue

    def sendIdleByte(self, out, offset):
        for i in range(8):
            out[offset+i] = 0xFF

    def updateChecksum(self, byteData):
        self.checksums[0] = self.checksums[0] + byteData
        self.checksums[1] = self.checksums[1] + self.checksums[0]

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        inputIndex = 0
        outputIndex = 0
        while (inputIndex < len(in0)) and (outputIndex < len(out)):

            # Process out of frame idle bytes until a size byte is
            # detected, in which case we start generating the header.
            if self.idle:
                thisByte = in0[inputIndex]
                inputIndex += 1
                if thisByte == 0x00:
                    self.sendIdleByte(out, outputIndex)
                    outputIndex += 8
                else:
                    self.idle = False
                    self.sendDataByte(out, outputIndex, self.header[0])
                    self.byteCount = thisByte
                    self.headerIndex = 1
                    outputIndex += 8

            # Perform header insertion.
            elif self.headerIndex < len(self.header):
                self.sendDataByte(out, outputIndex, self.header[self.headerIndex])
                self.headerIndex += 1
                outputIndex += 8

            # Add the length field.
            elif self.headerIndex == len(self.header):
                self.sendDataByte(out, outputIndex, self.byteCount)
                self.checksums = [0, 0]
                self.updateChecksum(self.byteCount)
                self.headerIndex += 1
                outputIndex += 8

            # Transfer the payload data.
            elif self.byteCount > 0:
                thisByte = in0[inputIndex]
                self.sendDataByte(out, outputIndex, thisByte)
                self.updateChecksum(thisByte)
                self.byteCount -= 1
                inputIndex += 1
                outputIndex += 8

            # Append the first checksum byte.
            elif self.headerIndex == len(self.header)+1:
                self.sendDataByte(out, outputIndex, self.checksums[0] % 255)
                self.headerIndex += 1
                outputIndex += 8

            # Append the second checksum byte.
            elif self.headerIndex == len(self.header)+2:
                self.sendDataByte(out, outputIndex, self.checksums[1] % 255)
                self.headerIndex += 1
                outputIndex += 8

            # Insert idle byte at end of frame.
            else:
                self.sendIdleByte(out, outputIndex)
                self.idle = True
                outputIndex += 8

        self.consume_each(inputIndex)
        return outputIndex
