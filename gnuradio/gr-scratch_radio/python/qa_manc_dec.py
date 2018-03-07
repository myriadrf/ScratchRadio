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
from manc_dec import manc_dec

class qa_manc_dec (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        srcData = (1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 
            0, 1, 1, 0, 1, 0, 0, 1, 0, 1)
        refData = (1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1)
        source = blocks.vector_source_b(srcData)
        decoder = manc_dec(False)
        sink = blocks.vector_sink_b()
        self.tb.connect(source, decoder)
        self.tb.connect(decoder, sink)
        self.tb.run()
        self.assertEqual(refData, sink.data())

    def test_002_t (self):
        srcData = (1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 
            0, 1, 1, 0, 1, 0, 0, 1, 0, 1)
        refData = (0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0)
        source = blocks.vector_source_b(srcData)
        encoder = manc_dec(True)
        sink = blocks.vector_sink_b()
        self.tb.connect(source, encoder)
        self.tb.connect(encoder, sink)
        self.tb.run()
        self.assertEqual(refData, sink.data())

if __name__ == '__main__':
    gr_unittest.run(qa_manc_dec, "qa_manc_dec.xml")
