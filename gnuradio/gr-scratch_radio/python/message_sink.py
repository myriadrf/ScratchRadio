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
import os
import time

from gnuradio import gr
from threading import Thread
from Queue import Queue

class message_writer(Thread):
    def __init__(self, msgFileName, msgQueue):
        Thread.__init__(self)
        self.msgFileName = msgFileName
        self.msgQueue = msgQueue
        self.running = False

    def run(self):
        msgFile = open(self.msgFileName, 'w')
        msgLength = 0
        self.running = True
        while self.running:
            time.sleep(0.5)
            while not self.msgQueue.empty():
                msg = self.msgQueue.get()
                for msgByte in msg:
                    if msgLength == 0:
                        msgLength = msgByte
                    else:
                        msgFile.write(chr(msgByte))
                        msgLength -= 1
                        if msgLength == 0:
                            msgFile.write('\n')
                            msgFile.flush()
        msgFile.close()

    def halt(self):
        self.running = False

class message_sink(gr.sync_block):
    """
    docstring for block message_sink
    """
    def __init__(self, msgFileName):
        gr.sync_block.__init__(self,
            name="message_sink",
            in_sig=[numpy.uint8],
            out_sig=None)

        # Creates the message pipe FIFO if not already present.
        msgPipePath = os.path.dirname(msgFileName)
        if not os.path.exists(msgPipePath):
            os.makedirs(msgPipePath)
        if not os.path.exists(msgFileName):
            os.mkfifo(msgFileName)

        self.msgFileName = msgFileName
        self.msgQueue = Queue(32)
        self.msgWriter = None

    def work(self, input_items, output_items):
        if self.msgQueue.full():
            return 0
        else:
            in0 = input_items[0]
            self.msgQueue.put(in0)
            return len(input_items[0])

    def start(self):
        if self.msgWriter == None:
            self.msgWriter = message_writer(self.msgFileName, self.msgQueue)
            self.msgWriter.start()
            return True
        else:
            return False

    def stop(self):
        if self.msgWriter != None:
            self.msgWriter.halt()
            self.msgWriter.join()
            self.msgWriter = None
            return True
        else:
            return False
