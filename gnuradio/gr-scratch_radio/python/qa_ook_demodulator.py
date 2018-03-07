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
from ook_demodulator import ook_demodulator

class qa_ook_demodulator (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        srcData = (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
        refData = (0.0, 0.0, 0.0, 0.0, 0.0, 0.30000001192092896, 
            0.6000000238418579, 0.8999999761581421, 0.8666666746139526, 
            0.5333333611488342, 0.20000000298023224, -0.13333334028720856, 
            -0.13333334028720856, 0.1666666716337204, 0.46666666865348816, 
            0.7666666507720947, 0.7333333492279053, 0.4000000059604645, 
            0.06666667014360428, -0.2666666805744171, -0.2666666805744171, 
            -0.2666666805744171, -0.2666666805744171, -0.2666666805744171, 
            -0.2666666805744171, 0.03333333507180214, 0.3333333432674408, 
            0.6333333253860474, 0.6000000238418579, 0.2666666805744171, 
            -0.06666667014360428, -0.4000000059604645, -0.4000000059604645, 
            -0.10000000149011612, 0.20000000298023224, 0.5333333611488342, 
            0.5333333611488342, 0.23333333432674408, -0.06666667014360428, 
            -0.4000000059604645, -0.4000000059604645)
        source = blocks.vector_source_c(srcData)
        demodulator = ook_demodulator(2, 8)
        sink = blocks.vector_sink_f()
        self.tb.connect(source, demodulator)
        self.tb.connect(demodulator, sink)
        self.tb.run()
        self.assertFloatTuplesAlmostEqual(refData, sink.data())

if __name__ == '__main__':
    gr_unittest.run(qa_ook_demodulator, "qa_ook_demodulator.xml")
