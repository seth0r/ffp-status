import cherrypy
from cherrypy._cperror import HTTPRedirect
from cherrypy.lib.static import serve_fileobj, serve_file
import os
import time
import datetime as dt
import math
import random
import json
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.sql.expression import func
from sqlalchemy.orm.session import Session
import tsdb

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km

def getnodeloc(node):
    if node.loc_lon and node.loc_lat:
        return [node.loc_lon,node.loc_lat]
    if node.loc_guess_lon and node.loc_guess_lat:
        return [node.loc_guess_lon,node.loc_guess_lat]
    random.seed(node.nodeid)
    return [
        float(os.getenv("DEFLON","0")) - 0.001 + random.random() * 0.002,
        float(os.getenv("DEFLAT","0")) - 0.001 + random.random() * 0.002,
    ]

def getkindofaddr(addr):
    KINDS = {
        0:"wired",
        1:"wireless",
        2:"unknown_2",
        3:"wired",
        4:"wired",
        5:"wireless",
        6:"unknown_6",
        7:"tunnel",
    }
    return KINDS[ int(addr[-1],16) & 7 ]

class NodeMap:
    def node2gjs(self, node, user = None):
        sess = Session.object_session(node)
        settings = {
            "offline_limits": { "green" : 0, "yellow" : 3, "red" : 24, "grey" : 168 },
        }
        settings.update(node.settings)
        if settings.get("hideinmap",False):
            return
        now = dt.datetime.now(dt.timezone.utc)
        loc = getnodeloc(node)
        nhmac = node.network.get("nexthop",None)
        if nhmac:
            nhmac = sess.get(tsdb.MacAddr, { "mac": nhmac })
        nexthop = nhmac.node if nhmac else None
        offline = (now.timestamp() - node.last_data.timestamp()) // 3600
        color = ([ co[0] for co in
            sorted(
                filter(
                    lambda co: offline <= co[1],
                    settings.get("offline_limits",{}).items()
                ),
                key = lambda co: co[1]
            )
        ] + [None] )[0]
        lang = self.get_lang()
        f = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": loc,
            },
            "properties": {
                "type" : "node",
                "id"   : node.nodeid,
                "popup": self.get_tpl( "map/node_popup.%s.html" % lang, "map/node_popup.html" ).
                    render( node = node, nexthop = nexthop, loc = loc, offline = offline, color = color, now = now, user = user ),
                "info" : self.get_tpl( "map/node_info.%s.html" % lang, "map/node_info.html"  ).
                    render( node = node, nexthop = nexthop, loc = loc, offline = offline, color = color, now = now, user = user ),
            }
        }
        vpn = node.network.get("mesh_vpn",{})
        f["properties"]["uplink"] = vpn.get("enabled",False) and len(vpn.get("peers",[])) > 0
        f["properties"]["host"] = node.hostname
        f["properties"]["offline"] = offline
        f["properties"]["offline_limits"] = settings["offline_limits"]
        return f

    @cherrypy.expose
    def nodes_geojson(self, max_offline_days = 100):
        user = self.get_user()
        gjs = { "type": "FeatureCollection","features": [] }
        
        with tsdb.getSess() as sess:
            for n in sess.execute( select(tsdb.Node)
                .where(tsdb.Node.last_data >= dt.datetime.now(dt.timezone.utc) - dt.timedelta(days = max_offline_days))
                .order_by(tsdb.Node.last_data.desc())
            ).scalars():
                f = self.node2gjs( n, user )
                if f:
                    gjs["features"].append( f )

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return bytes(json.dumps(gjs),"utf-8")

    def get_link_stats(self,thisnode,othernode, alllinks):
        links = []
        for ll in alllinks[ (thisnode.nodeid,othernode.nodeid) ]:
            rl = None
            for l in alllinks[ (othernode.nodeid,thisnode.nodeid) ]:
                if ll.mac == l.remotemac and ll.remotemac == l.mac:
                    rl = l
                    break
            links.append((ll,rl))
        links.sort( key = lambda x: x[0].tq, reverse = True )
        return links

    def get_links(self):
        now = dt.datetime.now(dt.timezone.utc)
        t = now - dt.timedelta(days = 1)
        with tsdb.getSess() as sess:
            nodes = {}
            for n in sess.execute( select(tsdb.Node).where(tsdb.Node.last_data >= t) ).scalars():
                nodes[ n.nodeid ] = n
            dblinks = list( sess.execute( select(tsdb.Link)
                .where(tsdb.Link.last_data >= t)
                .where(tsdb.Link.tq > 0)
            ).scalars() )
            sess.close()
            alllinks = defaultdict(list)
            for l in dblinks:
                l.lastseen += now.timestamp() - l.last_data.timestamp()
                l.kind = getkindofaddr( l.mac )
                alllinks[ (l.nodeid,l.remotenodeid) ].append(l)
            for (nid,rnid) in list(alllinks.keys()):
                thisnode = nodes.get( nid )
                othernode = nodes.get( rnid )
                if None in [thisnode,othernode]:
                    continue
                thisloc  = getnodeloc(thisnode)
                otherloc = getnodeloc(othernode)
                stats = self.get_link_stats( thisnode, othernode, alllinks )
                res = {
                    "link_id": "%s_%s" % (nid,rnid),
                    "nodes": [thisnode,othernode],
                    "stats": stats,
                }
                if any(map( lambda x: x[1], stats )):
                    res["coordinates"] = [thisloc,[ (thisloc[0] + otherloc[0]) / 2, (thisloc[1] + otherloc[1]) / 2 ]]
                else:
                    res["coordinates"] = [thisloc, otherloc]
                if thisloc[0] <= otherloc[0]:
                    res["l"] = 0
                    res["r"] = 1
                else:
                    res["r"] = 0
                    res["l"] = 1
                res["length"] = 1000 * haversine( thisloc[0],thisloc[1], otherloc[0],otherloc[1] )
                res["tq"] = stats[0][0].tq
                res["otq"] = None
                res["lastseen"] = 24*60*60
                for l in stats:
                    if l[1]:
                        if res["otq"] is None or l[1].tq > res["otq"]:
                            res["otq"] = l[1].tq
                    if l[0].lastseen < res["lastseen"]:
                        res["lastseen"] = l[0].lastseen
                yield res

    def link2gjs(self,l):
        lang = self.get_lang()
        f = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": l["coordinates"],
            },
            "properties": {
                "type": "link",
                "id"  : l["link_id"],
                "info": self.get_tpl( "map/link_info.%s.html" % lang, "map/link_info.html"  ).render( link = l ),
                "tq"  : l["tq"] / 255,
                "seen": l["lastseen"],
            }
        }
        return f

    @cherrypy.expose
    def links_geojson(self):
        gjs = { "type": "FeatureCollection","features": [] }

        for l in self.get_links():
            gjs["features"].append( self.link2gjs( l ) )

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return bytes(json.dumps(gjs),"utf-8")
