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

class ook_modulator(gr.basic_block):
    """
    docstring for block ook_modulator
    """
    def __init__(self, baudRate, sampleRate):
        gr.basic_block.__init__(self,
            name="ook_modulator",
            in_sig=[numpy.uint8],
            out_sig=[numpy.complex64])
        self.baudRate = int(baudRate)
        self.sampleRate = int(sampleRate)
        self.ncoCount = int(sampleRate)
        self.currentSample = 0.0

    def forecast(self, noutput_items, ninput_items_required):
        reqd = noutput_items * self.baudRate / self.sampleRate + 1
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = reqd

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        inputIndex = 0
        outputIndex = 0
        while (inputIndex < len(in0)) and (outputIndex < len(out)):
            nextNcoCount = self.ncoCount + self.baudRate
            if nextNcoCount < self.sampleRate:
                out[outputIndex] = complex(self.currentSample)
                outputIndex += 1
            else:
                oldSample = self.currentSample
                if in0[inputIndex] == 1:
                    self.currentSample = 1.0
                else:
                    self.currentSample = 0.0
                inputIndex +=1
                nextNcoCount -= self.sampleRate
                interpValue = (self.currentSample * nextNcoCount +
                    oldSample * (self.baudRate - nextNcoCount)) / self.baudRate
                out[outputIndex] = complex(interpValue)
                outputIndex += 1
            self.ncoCount = nextNcoCount

        self.consume_each(inputIndex)
        return outputIndex

