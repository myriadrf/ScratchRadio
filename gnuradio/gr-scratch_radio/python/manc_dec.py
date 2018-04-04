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

class manc_dec(gr.basic_block):
    """
    docstring for block manc_dec
    """
    def __init__(self, invert):
        gr.basic_block.__init__(self,
            name="manc_dec",
            in_sig=[numpy.uint8],
            out_sig=[numpy.uint8])
        self.invert = invert
        self.outOfSync = True
        self.doDecode = False
        self.startBit = -1

    def forecast(self, noutput_items, ninput_items_required):
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = 2 * noutput_items

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        outputIndex = 0
        numInputs = min(len(in0), 2*len(out))
        for i in xrange(numInputs):
            inputBit = in0[i]

            # If the decoder is out of sync, search for a transition.
            if self.outOfSync:
                if self.startBit < 0:
                    self.startBit = inputBit
                elif self.startBit != inputBit:
                    self.outOfSync = False
                    self.doDecode = False

            # Store the first bit of each coding pair.
            elif not self.doDecode:
                self.doDecode = True
                self.startBit = inputBit

            # Slip the decoder on invalid bit pairs.
            elif self.startBit == inputBit:
                self.outOfSync = True
                self.startBit = -1

            # Store the decoded bit to the output buffer. Default is to
            # decode a rising edge as '1'.
            else:
                if not self.invert:
                    out[outputIndex] = inputBit
                else:
                    out[outputIndex] = self.startBit
                self.doDecode = False
                outputIndex += 1

        self.consume_each(numInputs)
        return outputIndex
