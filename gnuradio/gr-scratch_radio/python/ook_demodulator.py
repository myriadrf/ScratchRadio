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

class ook_demodulator(gr.sync_block):
    """
    docstring for block ook_demodulator
    """
    def __init__(self, baudRate, sampleRate):
        gr.sync_block.__init__(self,
            name="ook_demodulator",
            in_sig=[numpy.complex64],
            out_sig=[numpy.float32])
        self.symbolAvgPeriod = int ((3.0*sampleRate) / (4.0*baudRate))
        self.offsetAvgPeriod = self.symbolAvgPeriod * 10
        self.symbolAccValue = 0.0
        self.offsetAccValue = 0.0
        self.set_history(self.symbolAvgPeriod + self.offsetAvgPeriod + 1)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        for i in range(len(in0) - (self.symbolAvgPeriod + self.offsetAvgPeriod)):
            oldOffsetIndex = i
            oldSampleIndex = oldOffsetIndex + self.offsetAvgPeriod
            newSampleIndex = oldSampleIndex + self.symbolAvgPeriod

            absInputSample = abs(in0[newSampleIndex])
            absOldSymbolSample = abs(in0[oldSampleIndex])
            absOldOffsetSample = abs(in0[oldOffsetIndex])

            self.symbolAccValue += absInputSample - absOldSymbolSample
            self.offsetAccValue += absOldSymbolSample - absOldOffsetSample

            symbolValue = self.symbolAccValue / self.symbolAvgPeriod
            symbolValue -= self.offsetAccValue / self.offsetAvgPeriod
            out[i] = symbolValue

        return len(out)
