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

class message_reader(Thread):
    def __init__(self, msgFileName, msgQueue):
        Thread.__init__(self)
        self.msgFileName = msgFileName
        self.msgQueue = msgQueue
        self.running = False

    def run(self):
        msgFile = open(self.msgFileName, 'r')
        self.running = True
        while self.running:
            msg = msgFile.readline().rstrip()
            if (msg == ''):
                time.sleep(0.5)
            else:
                self.msgQueue.put(msg)
                while (self.msgQueue.full()):
                    time.sleep(0.5)
        msgFile.close()

    def halt(self):
        self.running = False

class message_source(gr.sync_block):
    """
    docstring for block message_source
    """
    def __init__(self, msgFileName):
        gr.sync_block.__init__(self,
            name="message_source",
            in_sig=None,
            out_sig=[numpy.uint8])
        self.msgFileName = msgFileName
        self.msgQueue = Queue(8)
        self.msgReader = None
        self.msgOffset = 0
        self.msgBuffer = None

    def work(self, input_items, output_items):
        out = output_items[0]
        outputIndex = 0
        if len(out) == 0:
            return 0
        if self.msgBuffer == None:
            if self.msgQueue.empty():
                for i in range(len(out)):
                    out[i] = 0
                return len(out)
            else:
                self.msgOffset = 0
                self.msgBuffer = self.msgQueue.get()
                out[0] = len(self.msgBuffer)
                outputIndex = 1

        while (outputIndex < len(out)) and (self.msgBuffer != None):
            out[outputIndex] = ord(self.msgBuffer[self.msgOffset])
            outputIndex += 1
            self.msgOffset += 1
            if self.msgOffset == len(self.msgBuffer):
                self.msgBuffer = None

        return outputIndex

    def start(self):
        if self.msgReader == None:
            self.msgReader = message_reader(self.msgFileName, self.msgQueue)
            self.msgReader.start()
            return True
        else:
            return False

    def stop(self):
        if self.msgReader != None:
            self.msgReader.halt()
            self.msgReader.join()
            self.msgReader = None
            return True
        else:
            return False
