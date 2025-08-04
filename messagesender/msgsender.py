#!/usr/bin/env python3
import threading
import time
import sys
import os
import glob
import configparser
import logging
from logging.handlers import TimedRotatingFileHandler
import jinja2

import querier
import emitter

class MessageSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(self.__class__.__name__)
        loglevel = os.getenv("LOGLEVEL","INFO").upper()
        try:
            loglevel = int(loglevel)
        except ValueError:
            if hasattr(logging, loglevel):
                loglevel = getattr(logging, loglevel)
            else:
                loglevel = logging.INFO
        logformat = '%(asctime)-15s %(levelname)s %(name)s.%(funcName)s: %(message)s'
        loghandlers = [
            logging.StreamHandler( stream = sys.stdout )
        ]
        logging.basicConfig( level = loglevel, format = logformat, handlers = loghandlers )

        self.tplenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader( os.getenv("TPLDIR") ),
            trim_blocks = True,
            lstrip_blocks = True
        )

        self.shouldstop = False
        self.tstart = time.time()
        self.start()

    def stop(self):
        self.shouldstop = True

    def run(self):
        self.querier = {}
        for n,q in querier.__classes__.items():
            self.querier[n] = q( self.logger.getChild( n ) )
        self.emitter = {}
        self.logger.info("Running...")
        while not self.shouldstop:
            for n,q in self.querier.items():
                self.work(n,q)
            for i in range(10):
                if self.shouldstop:
                    break
                time.sleep(1)

    def work(self,name,querier):
        try:
            for msg in querier.query():
                if msg["type"] not in self.emitter and hasattr(emitter,msg["type"]):
                    self.emitter[ msg["type"] ] = getattr(emitter,msg["type"])( self, self.logger.getChild( msg["type"]  ) )
                if msg["type"] in self.emitter:
                    if self.emitter[ msg["type"] ].emit( **msg ):
                        querier.ack_sent( msg )
                    else:
                        self.ogger.error("Error emitting message: %s" % str(msg))
                else:
                    self.logger.error("No emitter for message type %s." % msg["type"])
        except Exception as ex:
            self.logger.exception("Exception while processing %s" % name)

    def render(self, tplnames, **kwargs):
        for tplname in tplnames:
            try:
                tpl = self.tplenv.get_template( "%s.tpl" % tplname )
                break
            except jinja2.exceptions.TemplateNotFound:
                pass
        else:
            raise
        return tpl.render( srv = self, url = os.getenv("URL",""), **kwargs )

if __name__ == "__main__":
    logger = logging.getLogger("__main__")
    try:
        ms = MessageSender()
        ms.join()
    except KeyboardInterrupt:
        ms.stop()
        ms.join()
