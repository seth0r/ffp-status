from base import Process
import queue
import os
import time
import gzip
import itertools
from copy import deepcopy
from xml.etree import ElementTree as ET
import parser
from collections import defaultdict

class defdict(defaultdict):
    def __init__(self,*args):
        super().__init__(self.__class__)

    def todict(self):
        res = {}
        for k,v in self.items():
            if isinstance(v,defdict):
                res[k] = v.todict()
            else:
                res[k] = v
        return res

class Parser( Process, parser.ffgParser, parser.InfluxFeeder, parser.MongoFeeder, parser.TimescaleFeeder ):
    BATCHSIZE = 1000        # split into smaller batches of this many files
    MAXAGE = 35*24*60*60    # max age of files to parse
    HISTAGE = 30*24*60*60   # age of a file when it is considered historical and the above limit is ignored

    def __init__( self, stordir, scheduler = None ):
        for cls in self.__class__.__bases__:
            if hasattr(cls,"__init__"):
                getattr(cls,"__init__")(self)
        self.scheduler = scheduler
        self.stordir = stordir
        self.start()

    def run(self):
        self.logger.info("Started...")
        while not self.shouldstop():
            try:
                now = time.time()
                host, all_files = self.scheduler.get(timeout=1)
                self.logger.info("Parsing %d files from %s..." % (len(all_files),host))
                for files in itertools.batched(sorted(all_files),self.BATCHSIZE):
                    self.preprocess(host, files)
                    for f in files:
                        fp = os.path.join( self.stordir, host, f )
                        try:
                            t = int(f.partition(".")[0])
                            if now - t < self.MAXAGE or now - os.path.getmtime(fp) > self.HISTAGE:
                                self.parse( host, f )
                            else:
                                self.logger.warning("Ignoring %s, too old." % f)
                        except ValueError:
                            self.logger.warning("Ignoring %s." % f)
                    self.postprocess( host )
                    for f in files:
                        fp = os.path.join( self.stordir, host, f )
                        try:
                            t = int(f.partition(".")[0])
                            if now - t < self.MAXAGE or now - os.path.getmtime(fp) > self.HISTAGE:
                                mvdir = os.path.join( self.stordir, "." + time.strftime("%Y-%m-%d",time.gmtime(t)), host )
                            else:
                                mvdir = os.path.join( self.stordir, ".old", host )
                        except ValueError:
                            mvdir = os.path.join( self.stordir, ".err", host )
                        os.makedirs( mvdir, exist_ok = True)
                        os.replace( fp, os.path.join( mvdir, f ) )
                diff = time.time() - now
                self.logger.info("Parsed %d files from %s in %.3f seconds (%.1f/s)" % (len(all_files), host, diff, len(all_files) / diff ))
                try:
                    os.removedirs( os.path.join( self.stordir, host ) )
                except OSError:
                    pass
                self.scheduler.done(host)
            except queue.Empty:
                pass
        self.logger.info("Stopped.")

    def parse(self,host,fname):
        fp = os.path.join( self.stordir, host, fname )
        if not os.path.isfile(fp):
            self.logger.warning("%s from %s not found.",fname,host)
            return
        self.logger.debug("Parsing %s from %s...",fname,host)
        try:
            if fname.endswith(".gz"):
                with gzip.open(fp,"rt") as fo:
                    self.parse_xml( fo, host )
            elif fname.endswith(".xml"):
                with open(fp,"rt") as fo:
                    self.parse_xml( fo, host )
            else:
                self.logger.warning("Parsing of %s from %s not implemented.", fname, host)
        except Exception as ex:
            self.logger.exception("Error parsing %s from %s.", fname, host)

    def parse_xml(self, fo, host):
        res = defdict()
        for evt,elem in ET.iterparse(fo, ["start","end"]):
            fnk = "%s_%s" % (elem.tag,evt)
            if hasattr(self,fnk):
                getattr(self,fnk)( elem, res, host )
            else:
                self.logger.warning("No method %s.",fnk)
        self.feed(res)

    def preprocess(self, host, files):
        for cls in self.__class__.__bases__:
            if hasattr(cls,"preprocess"):
                getattr(cls,"preprocess")(self,host,files)

    def feed(self, res):
        for cls in self.__class__.__bases__:
            if hasattr(cls,"feed"):
                getattr(cls,"feed")(self,deepcopy(res))

    def postprocess(self, host):
        for cls in self.__class__.__bases__:
            if hasattr(cls,"postprocess"):
                getattr(cls,"postprocess")(self,host)
