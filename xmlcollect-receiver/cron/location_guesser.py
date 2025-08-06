from base import Process
import os
import datetime as dt
import math
import random
from collections import defaultdict
from sqlalchemy import select, or_, and_
import tsdb
from sympy import symbols, solve, solve_poly_system, Eq

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km * 1000

class LocationGuesser(Process):
    INTERVAL = 3600
    def run(self):
        sess = tsdb.getSess()
        now = dt.datetime.now( dt.timezone.utc )
        t = now - dt.timedelta( days = 1 )
        for node in sess.execute( select( tsdb.Node ).where( and_(
            tsdb.Node.last_data >= t,
            or_( tsdb.Node.loc_lon == None, tsdb.Node.loc_lat == None )
        ))).scalars():
            random.seed(node.nodeid)
            for h in range(1,25):
                neigh = {}
                ntqs = defaultdict(list)
                for l in sess.execute( select( tsdb.Link )
                    .where(tsdb.Link.nodeid == node.nodeid)
                    .where(tsdb.Link.tq > 0)
                    .where(tsdb.Link.last_data >= now - dt.timedelta(hours = h))
                ).scalars():
                    if l.remotenode.loc_lon and l.remotenode.loc_lat:
                        neigh[ l.remotenodeid ] = l.remotenode
                        ntqs[  l.remotenodeid ].append( l.tq / 255 )
                for l in sess.execute( select( tsdb.Link )
                    .where(tsdb.Link.remotenodeid == node.nodeid)
                    .where(tsdb.Link.tq > 0)
                    .where(tsdb.Link.last_data >= now - dt.timedelta(hours = h))
                ).scalars():
                    if l.node.loc_lon and l.node.loc_lat:
                        neigh[ l.nodeid ] = l.node
                        ntqs[  l.nodeid ].append( l.tq / 255 )
                if len(neigh) >= 3:
                    break
            if len(neigh) == 0:
                continue
            for nid,tqs in list(ntqs.items()):
                ntqs[nid] = sum(tqs) / len(tqs)
            ntqs = sorted( ntqs.items(), key=lambda ntq: ntq[1], reverse=True )
            self.logger.info("%s has %d neighbours.", node.hostname, len(neigh) )
            for nid,tq in ntqs:
                self.logger.info("  %s: %f using %f as pseudo distance", neigh[nid].hostname, tq, 1 / (tq**2) )
            x,y = self.guess_location( neigh, ntqs )
            if x and y:
                node.loc_guess_lon = x
                node.loc_guess_lat = y
                sess.commit()
                self.logger.info("  Guessed location of %s: %f : %f", node.hostname, x, y)

    def guess_location(self, neigh, ntqs ):
        try:
            if len(neigh) >= 3:
                self.logger.info("  Guessing location based on three neighbour nodes...")
                res = self.trilaterate( neigh, ntqs )
                if res: return res
            if len(neigh) >= 2:
                self.logger.info("  Guessing location based on two neighbour nodes and some random value...")
                res = self.bilaterate_rnd( neigh, ntqs )
                if res: return res
            if len(neigh) >= 1:
                self.logger.info("  Guessing random location around neighbour node...")
                return self.near_rnd( neigh, ntqs )
        except:
            self.logger.exception("Guessing failed.")
        return None,None

    def trilaterate(self, neighbours, tqs):
        x,y,f = symbols('x y f', real=True)
        eqs = []
        for nid,tq in tqs[:3]:
            xn = int(neighbours[nid].loc_lon*1000000)
            yn = int(neighbours[nid].loc_lat*1000000)
            d = int(1/(tq**2)*1000000)
            eqs.append( Eq( (x-xn)**2 + (y-yn)**2, (f*d)**2 ) )
        res = solve(eqs, (x, y, f))
        if res:
            x,y,f = sorted(filter(lambda r: r[2]>0, res), key = lambda r: r[2])[0]
            return float(x)/1000000,float(y)/1000000

    def bilaterate_rnd(self, neighbours, tqs):
        x,y,f = symbols('x y f', real=True)
        x1 = int(neighbours[ tqs[0][0] ].loc_lon * 1000000)
        y1 = int(neighbours[ tqs[0][0] ].loc_lat * 1000000)
        d1 = int( 1 / ( tqs[0][1] ** 2 ) * 1000000 )
        x2 = int(neighbours[ tqs[1][0] ].loc_lon * 1000000)
        y2 = int(neighbours[ tqs[1][0] ].loc_lat * 1000000)
        d2 = int( 1 / ( tqs[1][1] ** 2 ) * 1000000 )
        minf = (((x1 - x2)**2 + (y1-y2)**2)**0.5) / (d1 + d2)
        maxf = (((x1 - x2)**2 + (y1-y2)**2)**0.5) / abs(d1 - d2)
        eq1 = Eq( (x-x1)**2 + (y-y1)**2, (f*d1)**2 )
        eq2 = Eq( (x-x2)**2 + (y-y2)**2, (f*d2)**2 )
        xv,yv = random.choice( solve((eq1,eq2), (x, y)) )
        fv = minf + (maxf-minf) * random.random()
        self.logger.info(str([minf,maxf,fv]))
        xv = xv.subs(f,fv)
        yv = yv.subs(f,fv)
        return float(xv)/1000000,float(yv)/1000000

    def near_rnd(self, neighbours, tqs):
        x = neighbours[tqs[0][0]].loc_lon - 0.001 + random.random() * 0.002
        y = neighbours[tqs[0][0]].loc_lat - 0.001 + random.random() * 0.002
        return x,y
