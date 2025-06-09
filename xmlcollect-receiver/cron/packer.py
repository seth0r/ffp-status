from base import Process
import os
import time
import glob
import zipfile
import gzip

class Packer(Process):
    INTERVAL = 3600
    def run(self):
        stordir = self.kwargs["TMPSTOR"]
        zfs = {}
        dellist = []
        for f in sorted(glob.glob( os.path.join( stordir, ".*", "*", "*" ) ))[:1000000]:
            if time.time() - os.path.getmtime(f) < self.INTERVAL:
                continue
            p,fn2 = os.path.split(f)
            p,fn1 = os.path.split(p)
            zfn = "%s.zip" % p
            fn = zipfile.ZipInfo( os.path.join( fn1,fn2 ), time.gmtime(os.path.getmtime(f))[:6] )
            if zfn not in zfs:
                zfs[zfn] = zipfile.ZipFile(zfn,'a')
            if f.endswith(".gz"):
                fn.filename = fn.filename.rpartition(".")[0]
                with gzip.open(f,"rb") as gzf:
                    buf = gzf.read()
            else:
                with open(f,"rb") as fi:
                    buf = fi.read()
            try:
                with zfs[zfn].open(fn.filename,"r") as fi:
                    same = fi.read() == buf
                if not same:
                    zfs[zfn].writestr( fn, buf )
                    self.logger.info("%s -> %s : %s" % (f,zfn,fn.filename))
                else:
                    self.logger.info("%s already in %s." % (f,zfn))
            except KeyError:
                zfs[zfn].writestr( fn, buf )
                self.logger.info("%s -> %s : %s" % (f,zfn,fn.filename))
            dellist.append(f)
            if len(zfs) > 3:
                first = sorted(zfs.keys())[0]
                zfs[first].close()
                del zfs[first]
        for zf in zfs.values():
            zf.close()
        for f in dellist:
            os.remove(f)
            try:
                os.removedirs(os.path.dirname(f))
            except OSError:
                pass
