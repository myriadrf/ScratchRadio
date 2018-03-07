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
from manc_enc import manc_enc

class qa_manc_enc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        srcData = (0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1)
        refData = (1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 
            0, 1, 1, 0, 1, 0, 0, 1, 0, 1)
        source = blocks.vector_source_b(srcData)
        encoder = manc_enc(False)
        sink = blocks.vector_sink_b()
        self.tb.connect(source, encoder)
        self.tb.connect(encoder, sink)
        self.tb.run()
        self.assertEqual(refData, sink.data())

    def test_002_t (self):
        srcData = (1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0)
        refData = (1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 
            0, 1, 1, 0, 1, 0, 0, 1, 0, 1)
        source = blocks.vector_source_b(srcData)
        encoder = manc_enc(True)
        sink = blocks.vector_sink_b()
        self.tb.connect(source, encoder)
        self.tb.connect(encoder, sink)
        self.tb.run()
        self.assertEqual(refData, sink.data())

if __name__ == '__main__':
    gr_unittest.run(qa_manc_enc, "qa_manc_enc.xml")
