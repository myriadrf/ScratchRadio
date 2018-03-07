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

import os

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from message_sink import message_sink

class qa_message_sink (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        messages = [
            "This is a sink test message.",
            "This is a second sink test message.",
            "This is a third sink test message."]

        srcData = []
        for message in messages:
            srcData.append(len(message))
            for i in range(len(message)):
                srcData.append(ord(message[i]))
            srcData.append(0)
            srcData.append(0)

        msgFileName = "/tmp/gr-scratch.qa_message_sink.txt"
        open(msgFileName, 'w').close()

        sink = message_sink(msgFileName)
        source = blocks.vector_source_b(srcData)
        self.tb.connect(source, sink)
        self.tb.run ()

        msgFile = open(msgFileName, 'r')
        for message in messages:
            result = msgFile.readline().rstrip()
            self.assertEqual(message, result)
        msgFile.close()

if __name__ == '__main__':
    gr_unittest.run(qa_message_sink, "qa_message_sink.xml")
