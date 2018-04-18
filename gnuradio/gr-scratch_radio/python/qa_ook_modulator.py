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

class qa_ook_modulator (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        srcData = (0, 1, 0, 1, 0, 0)
        refData = (0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
        source = blocks.vector_source_b(srcData)
        modulator = scratch_radio.ook_modulator(2, 8)
        sink = blocks.vector_sink_c()
        self.tb.connect(source, modulator)
        self.tb.connect(modulator, sink)
        self.tb.run()
        self.assertComplexTuplesAlmostEqual(refData, sink.data())

    def test_002_t (self):
        srcData = (0, 1, 0, 1, 0, 0)
        refData = (0.0, 0.0, 0.0, 2.0/3.0, 1.0, 1.0, 2.0/3.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0/3.0, 0.0, 0.0, 0.0)
        source = blocks.vector_source_b(srcData)
        modulator = scratch_radio.ook_modulator(3, 10)
        sink = blocks.vector_sink_c()
        self.tb.connect(source, modulator)
        self.tb.connect(modulator, sink)
        self.tb.run()
        self.assertComplexTuplesAlmostEqual(refData, sink.data())

if __name__ == '__main__':
    gr_unittest.run(qa_ook_modulator, "qa_ook_modulator.xml")
