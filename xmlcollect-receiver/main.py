#!/usr/bin/env python3
import os
import sys
import time
import glob
import logging
try:
    os.setgid(int(os.getenv("GID",os.getgid())))
    os.setuid(int(os.getenv("UID",os.getuid())))
except PermissionError:
    pass

loglevel = os.getenv("LOGLEVEL","INFO").upper()
try:
    loglevel = int(loglevel)
except ValueError:
    if hasattr(logging, loglevel):
        loglevel = getattr(logging, loglevel)
    else:
        loglevel = logging.INFO
logformat = '%(asctime)-15s %(levelname)s %(name)s[%(process)d].%(funcName)s: %(message)s'
loghandlers = [
    logging.StreamHandler( stream = sys.stdout )
]
logging.basicConfig( level = loglevel, format = logformat, handlers = loghandlers )

TMPSTOR = os.getenv("TMPSTOR", "./tmpstor")

procs = []

from sched import Scheduler
scheduler = Scheduler( int(os.getenv("WAITPARSE", 30)) )
procs.append( scheduler )

for d in glob.glob( os.path.join( TMPSTOR, "*" ) ):
    try:
        os.rmdir( d )
    except:
        pass

now = time.time()
for fp in glob.glob( os.path.join( TMPSTOR, "*","*" ) ):
    if not os.path.isfile(fp):
        continue
    fn = os.path.basename(fp)
    hn = os.path.basename(os.path.dirname(fp))
    scheduler.put( now, hn, fn )

from recv import Receiver
procs.append( Receiver( TMPSTOR, int(os.getenv("PORT", 17485)), int(os.getenv("RECVTHREADS", 128)), scheduler ) )

from parser import Parser
for i in range(4):
    procs.append( Parser( TMPSTOR, scheduler ) )

from cron import Cron
procs.append( Cron( TMPSTOR=TMPSTOR ) )

try:
    while True:
        for p in procs:
            if not p.is_alive():
                break
        else:
            time.sleep(1)
            continue
        break
except KeyboardInterrupt:
    pass
finally:
    for p in procs:
        p.stop()
    fin = time.time() + 10
    for p in procs:
        p.join(max(1, fin - time.time()))
    if any([ p.is_alive() for p in procs ]):
        for p in procs:
            if p.is_alive():
                p.terminate()
        time.sleep(1)
        for p in procs:
            if p.is_alive():
                p.kill()
