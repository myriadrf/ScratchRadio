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

class symbol_sync(gr.basic_block):
    """
    docstring for block symbol_sync
    """
    def __init__(self, baudRate, sampleRate):
        gr.basic_block.__init__(self,
            name="symbol_sync",
            in_sig=[numpy.float32],
            out_sig=[numpy.uint8])
        self.baudRate = int(baudRate)
        self.sampleRate = int(sampleRate)
        self.sampleRatio = int(1 + sampleRate / baudRate)
        self.ncoCount = int(sampleRate)
        self.symbolReq = True
        self.set_history(2)

    def forecast(self, noutput_items, ninput_items_required):
        numInputs = noutput_items * self.sampleRatio
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = numInputs

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        inputIndex = 1
        outputIndex = 0
        while (inputIndex < len(in0)) and (outputIndex < len(out)):

            # Detect zero crossings when successive samples have a
            # negative product.
            thisSample = in0[inputIndex]
            lastSample = in0[inputIndex-1]
            if thisSample * lastSample <= 0:
                nextNcoCount = self.baudRate / 2
                self.symbolReq = True
            else:
                nextNcoCount = self.ncoCount + self.baudRate
            inputIndex += 1

            # Sample data at half the symbol period after detecting a
            # zero crossing and full symbol periods thereafter.
            if nextNcoCount >= self.sampleRate:
                nextNcoCount -= self.sampleRate
                self.symbolReq = True
            elif self.symbolReq and (nextNcoCount >= self.sampleRate / 2):
                if thisSample < 0:
                    out[outputIndex] = 0
                else:
                    out[outputIndex] = 1
                outputIndex += 1
                self.symbolReq = False
            self.ncoCount = nextNcoCount

        self.consume_each(inputIndex-1)
        return outputIndex
