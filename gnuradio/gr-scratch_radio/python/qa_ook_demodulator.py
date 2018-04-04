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

class qa_ook_demodulator (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        srcData = (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
        refData = (0.0, 0.0, 0.0, 0.0, 0.0, 0.3333333,
            0.6666667, 1.0000000, 0.9666666, 0.6000000,
            0.2333333, -0.1333333, -0.1333333,
            0.2000000, 0.5333334, 0.8666667,
            0.8333333, 0.4666667, 0.1000000,
            -0.2666667, -0.2666667, -0.2666667,
            -0.2666667, -0.2666667, -0.2666667,
            0.0666667, 0.4000000, 0.7333333,
            0.7000000, 0.3333333, -0.0333333,
            -0.4000000, -0.4000000, -0.0666667,
            0.2666667, 0.6000000, 0.5666667,
            0.2000000, -0.1333333, -0.4666667,
            -0.4333333, -0.4000000, -0.4000000,
            -0.4000000, -0.4000000, -0.0666667,
            0.3000000, 0.6666666, 0.6666666,
            0.6666666, 0.6333333, 0.6000000,
            0.5666667, 0.2000000, -0.1666667,
            -0.5333334, -0.5333334, -0.5333334,
            -0.5000000, -0.4666667, -0.4333333,
            -0.0666667, 0.2666667, 0.6000000,
            0.5666667, 0.2000000, -0.1333333,
            -0.4666667, -0.4333333)
        source = blocks.vector_source_c(srcData)
        demodulator = scratch_radio.ook_demodulator(2, 8)
        sink = blocks.vector_sink_f()
        self.tb.connect(source, demodulator)
        self.tb.connect(demodulator, sink)
        self.tb.run()
        self.assertFloatTuplesAlmostEqual(refData, sink.data())

if __name__ == '__main__':
    gr_unittest.run(qa_ook_demodulator, "qa_ook_demodulator.xml")
