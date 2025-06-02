#!/usr/bin/env python3
import multiprocessing
import queue
import collections
import time
import os
import string
from base import Process

class Scheduler(Process):
    def __init__( self, waittime ):
        super().__init__()
        self.waittime = waittime
        self.inq = multiprocessing.Queue()
        self.outq = multiprocessing.Queue()
        self.doneq = multiprocessing.Queue()
        self.processing = set()
        self.files = collections.defaultdict(set)
        self.lastfile = collections.defaultdict(float)
        self.start()

    def run(self):
        lastmsg = 0
        while not self.shouldstop():
            now = time.time()
            if now - lastmsg > 60:
                self.logger.info("%s alive, inQueue: %d, outQueue: %d" % (self.__class__.__name__, self.inq.qsize(), self.outq.qsize()))
                lastmsg = now
            try:
                for i in range(1000):
                    ts,hostname,filename = self.inq.get(timeout=0.01)
                    self.files[hostname].add(filename)
                    self.lastfile[hostname] = max( self.lastfile[hostname], ts )
            except queue.Empty:
                pass
            try:
                for i in range(10):
                    host = self.doneq.get(timeout=0.01)
                    self.processing.discard(host)
            except queue.Empty:
                pass
            now = time.time()
            for h in list(self.files.keys()):
                ts = self.lastfile[h]
                if h not in self.processing and now - ts > self.waittime:
                    self.processing.add(h)
                    self.outq.put(( h, list(sorted(self.files[h])) ))
                    del self.lastfile[h]
                    del self.files[h]

    def put(self, ts, hostname, filename):
        self.inq.put((ts,hostname,filename))

    def get(self,*args,**kwargs):
        return self.outq.get(*args,**kwargs)

    def done(self,host):
        self.doneq.put(host)
