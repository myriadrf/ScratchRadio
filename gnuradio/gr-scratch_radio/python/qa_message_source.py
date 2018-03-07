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
from message_source import message_source

class qa_message_source (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()
        self.maxDiff = None

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        messages = [
            "This is a source test message.",
            "This is a second source test message.",
            "This is a third source test message."]

        sourceFileName = "/tmp/gr-scratch.qa_message_source.txt"
        sourceFile = open(sourceFileName, 'w')
        refData = []
        for message in messages:
            refData.append(len(message))
            for i in range(len(message)):
                refData.append(ord(message[i]))
            sourceFile.write(message)
            sourceFile.write("\n")
        refData = tuple(refData)
        sourceFile.close()

        # We may need to repeat the test if leading zeros have been
        # inserted due to the read thread being delayed in startup.
        source = message_source(sourceFileName)
        retry = True
        while retry:
            sink = blocks.vector_sink_b()
            head = blocks.head(1, len(refData))
            self.tb.connect(source, head)
            self.tb.connect(head, sink)
            self.tb.run()
            genData = sink.data()
            if genData[0] == 0:
                self.tb.disconnect_all()
                print "Retrying due to delayed read thread startup."
            else:
                retry = False
        self.assertEqual(refData, genData)

if __name__ == '__main__':
    gr_unittest.run(qa_message_source, "qa_message_source.xml")
