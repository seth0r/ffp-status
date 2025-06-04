#!/usr/bin/env python3
import sys
from sqlalchemy import select,delete
from sqlalchemy.sql.expression import func
import datetime as dt
import tsdb

stats = tsdb.Stat.__subclasses__()

sess = tsdb.getSess()
sess.begin()

if len(sys.argv) > 3:
    t = dt.datetime(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
elif len(sys.argv) > 2:
    t = dt.datetime(int(sys.argv[1]),int(sys.argv[2]),1)
elif len(sys.argv) > 1:
    t = dt.datetime(int(sys.argv[1]),1,1)
else:
    sys.exit()

for (n,) in sess.execute( select(tsdb.Node) ):
    for stat in stats:
        cnt = sess.execute( select(stat).with_only_columns(func.count()).where(stat.nodeid == n.nodeid).where(stat.timestamp < t) ).scalar()
        if cnt > 0:
            res = sess.execute( delete(stat).where(stat.nodeid == n.nodeid).where(stat.timestamp < t) )
            print(n.hostname, stat.__name__, cnt, res.rowcount)
            
sess.commit()
sess.close()
