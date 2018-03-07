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

class manc_enc(gr.interp_block):
    """
    docstring for block manc_enc
    """
    def __init__(self, invert):
        gr.interp_block.__init__(self,
            name="manc_enc",
            in_sig=[numpy.uint8],
            out_sig=[numpy.uint8], interp=2)
        self.invert = invert

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        for i in xrange(len(in0)):

            # Insert idle bits if required.
            if in0[i] == 0xFF:
                out[2*i]   = 0xFF
                out[2*i+1] = 0xFF

            # Default is to encode '1' as a rising edge.
            elif not self.invert:
                if in0[i] > 0:
                    out[2*i]   = 0
                    out[2*i+1] = 1
                else:
                    out[2*i]   = 1
                    out[2*i+1] = 0
            else:
                if in0[i] > 0:
                    out[2*i]   = 1
                    out[2*i+1] = 0
                else:
                    out[2*i]   = 0
                    out[2*i+1] = 1

        return len(output_items[0])
