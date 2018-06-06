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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import scratch_radio_swig as scratch_radio

class qa_fast_agc_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        srcData = (
            1, 0+1j, -1, 0-1j, 1, 1, -1, -1, 0+1j, 0+1j)
        refData = (
            1, 0+1j, -1, 0-1j, 1, 1, -1, -1, 0+1j, 0+1j)
        source = blocks.vector_source_c(srcData)
        agc = scratch_radio.fast_agc_cc(0.5, 0.94754363, 1.0, 2.0)
        sink = blocks.vector_sink_c()
        self.tb.connect(source, agc)
        self.tb.connect(agc, sink)
        self.tb.run()
        self.assertComplexTuplesAlmostEqual(refData, sink.data())

    def test_002_t (self):
        srcData = (
            1.0, 0+1j, -1.0, 0-1j, 1.0, 1.0, -1.0, -1.0, 0+1j, 0+1j)
        refData = []
        gain = 0.125
        for srcDatapoint in srcData:
            refData.append(srcDatapoint * gain)
            gain += 0.5 * (1 - 0.947543636291 * gain)
        refData = tuple(refData)
        source = blocks.vector_source_c(srcData)
        agc = scratch_radio.fast_agc_cc(0.5, 1, 0.125, 2.0)
        sink = blocks.vector_sink_c()
        self.tb.connect(source, agc)
        self.tb.connect(agc, sink)
        self.tb.run()
        self.assertComplexTuplesAlmostEqual(refData, sink.data())

if __name__ == '__main__':
    gr_unittest.run(qa_fast_agc_cc, "qa_fast_agc_cc.xml")
