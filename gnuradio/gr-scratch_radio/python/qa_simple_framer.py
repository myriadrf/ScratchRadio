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

class qa_simple_framer (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()
        self.maxDiff = None

    def tearDown (self):
        self.tb = None

    def byteToBits (self, byteData):
        bitVec = []
        byteShift = byteData
        for i in range(8):
            bitValue = byteShift & 1
            byteShift >>= 1
            bitVec.append (bitValue)
        return bitVec

    def idleByte(self):
        bitVec = []
        for i in range(8):
            bitVec.append (0xFF)
        return bitVec

    def test_001_t (self):
        srcData = (0x00, 0x00, 0x00, 0x04, 0x01, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00)
        refData = []
        refData.extend (self.idleByte ())
        refData.extend (self.byteToBits (0xA5))
        refData.extend (self.byteToBits (0xF0))
        refData.extend (self.byteToBits (0xA5))
        refData.extend (self.byteToBits (0xF0))
        refData.extend (self.byteToBits (0xA5))
        refData.extend (self.byteToBits (0xF0))
        refData.extend (self.byteToBits (0x7E))
        refData.extend (self.byteToBits (0x81))
        refData.extend (self.byteToBits (0xC3))
        refData.extend (self.byteToBits (0x3C))
        refData.extend (self.byteToBits (0x04))
        refData.extend (self.byteToBits (0x01))
        refData.extend (self.byteToBits (0x02))
        refData.extend (self.byteToBits (0x03))
        refData.extend (self.byteToBits (0x04))
        refData.extend (self.byteToBits (0x0E))
        refData.extend (self.byteToBits (0x28))
        refData.extend (self.byteToBits (0xFF))
        refData.extend (self.idleByte ())
        refData.extend (self.idleByte ())
        refData = tuple(refData)

        source = blocks.vector_source_b(srcData)
        framer = scratch_radio.simple_framer()
        sink = blocks.vector_sink_b()
        self.tb.connect(source, framer)
        self.tb.connect(framer, sink)
        self.tb.run()
        self.assertEqual(refData, sink.data())

    def test_002_t (self):
        srcData = (0x00, 0x08, 0x80, 0x91, 0xA2, 0xB3, 0xC4, 0xD5, 0xE6, 0xF7, 0x00)
        refData = []
        refData.extend (self.idleByte ())
        refData.extend (self.byteToBits (0xA5))
        refData.extend (self.byteToBits (0xF0))
        refData.extend (self.byteToBits (0xA5))
        refData.extend (self.byteToBits (0xF0))
        refData.extend (self.byteToBits (0xA5))
        refData.extend (self.byteToBits (0xF0))
        refData.extend (self.byteToBits (0x7E))
        refData.extend (self.byteToBits (0x81))
        refData.extend (self.byteToBits (0xC3))
        refData.extend (self.byteToBits (0x3C))
        refData.extend (self.byteToBits (0x08))
        refData.extend (self.byteToBits (0x80))
        refData.extend (self.byteToBits (0x91))
        refData.extend (self.byteToBits (0xA2))
        refData.extend (self.byteToBits (0xB3))
        refData.extend (self.byteToBits (0xC4))
        refData.extend (self.byteToBits (0xD5))
        refData.extend (self.byteToBits (0xE6))
        refData.extend (self.byteToBits (0xF7))
        refData.extend (self.byteToBits (0xE9))
        refData.extend (self.byteToBits (0xF3))
        refData.extend (self.byteToBits (0xFF))
        refData.extend (self.idleByte ())
        refData.extend (self.idleByte ())
        refData = tuple(refData)

        source = blocks.vector_source_b(srcData)
        framer = scratch_radio.simple_framer()
        sink = blocks.vector_sink_b()
        self.tb.connect(source, framer)
        self.tb.connect(framer, sink)
        self.tb.run()
        self.assertEqual(refData, sink.data())

    def test_003_t (self):
        messages = [
            "Foo.",
            "Foo Bar.",
            "Foo Bar Baz."]

        sourceFileName = "/tmp/gr-scratch.qa_simple_framer.txt"
        sourceFile = open(sourceFileName, 'w')
        refData = []
        for message in messages:
            refData.extend (self.byteToBits (0xA5))
            refData.extend (self.byteToBits (0xF0))
            refData.extend (self.byteToBits (0xA5))
            refData.extend (self.byteToBits (0xF0))
            refData.extend (self.byteToBits (0xA5))
            refData.extend (self.byteToBits (0xF0))
            refData.extend (self.byteToBits (0x7E))
            refData.extend (self.byteToBits (0x81))
            refData.extend (self.byteToBits (0xC3))
            refData.extend (self.byteToBits (0x3C))
            refData.extend (self.byteToBits (len(message)))
            checkSum0 = len(message)
            checkSum1 = len(message)
            for i in range(len(message)):
                dataByte = ord(message[i])
                refData.extend (self.byteToBits (dataByte))
                checkSum0 += dataByte
                checkSum1 += checkSum0
            refData.extend (self.byteToBits (checkSum0 % 255))
            refData.extend (self.byteToBits (checkSum1 % 255))
            refData.extend (self.byteToBits (0xFF))
            refData.extend (self.idleByte ())
            sourceFile.write(message)
            sourceFile.write("\n")
        refData = tuple(refData)
        sourceFile.close()

        # We may need to repeat the test if leading zeros have been
        # inserted due to the read thread being delayed in startup.
        source = scratch_radio.message_source(sourceFileName, 300)
        retry = True
        while retry:
            sink = blocks.vector_sink_b()
            head = blocks.head(1, len(refData))
            framer = scratch_radio.simple_framer()
            self.tb.connect(source, framer)
            self.tb.connect(framer, head)
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
    gr_unittest.run(qa_simple_framer, "qa_simple_framer.xml")
