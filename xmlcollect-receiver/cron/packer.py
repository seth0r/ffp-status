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
        for f in glob.glob( os.path.join( stordir, ".*", "*", "*" ) ):
            if time.time() - os.path.getmtime(f) < self.INTERVAL:
                continue
            p,fn2 = os.path.split(f)
            p,fn1 = os.path.split(p)
            zfn = "%s.zip" % p
            fn = os.path.join( fn1,fn2 )
            if zfn not in zfs:
                zfs[zfn] = zipfile.ZipFile(zfn,'a')
            if f.endswith(".gz"):
                fn = fn.rpartition(".")[0]
                with gzip.open(f,"rt") as gzf:
                    zfs[zfn].writestr(fn,gzf.read())
            else:
                zfs[zfn].write(f,fn)
            dellist.append(f)
            self.logger.info("%s -> %s : %s" % (f,zfn,fn))
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
