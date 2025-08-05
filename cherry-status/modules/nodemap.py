import cherrypy
from cherrypy._cperror import HTTPRedirect
from cherrypy.lib.static import serve_fileobj, serve_file
import os
import time
import datetime as dt
import math
import random
import json
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
        if user:
            return self.make_nodes_geojson( max_offline_days )
        else:
            return self.cache("nodes_geojson",self.make_nodes_geojson,(max_offline_days,), cachetime=120)

    def make_nodes_geojson(self, max_offline_days ):
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

    def get_link_stats(self,thisnode,othernode, now):
        sess = Session.object_session(thisnode)
        links = []
        for l in sess.execute( select(tsdb.Link)
            .where(tsdb.Link.nodeid == thisnode.nodeid)
            .where(tsdb.Link.remotenodeid == othernode.nodeid)
            .where(tsdb.Link.last_data >= now - dt.timedelta(days = 1))
            .where(tsdb.Link.tq > 0)
        ).scalars():
            sess.expunge(l)
            l.lastseen += now.timestamp() - l.last_data.timestamp()
            l.kind = getkindofaddr( l.mac )
            rl = sess.execute( select(tsdb.Link)
                .where(tsdb.Link.nodeid == l.remotenodeid)
                .where(tsdb.Link.remotenodeid == l.nodeid)
                .where(tsdb.Link.mac == l.remotemac)
                .where(tsdb.Link.remotemac == l.mac)
                .where(tsdb.Link.last_data >= now - dt.timedelta(days = 1))
                .where(tsdb.Link.tq > 0)
            ).scalar_one_or_none()
            if rl:
                sess.expunge(rl)
                rl.lastseen += now.timestamp() - rl.last_data.timestamp()
                rl.kind = getkindofaddr( rl.mac )
            links.append((l,rl))
        links.sort( key = lambda x: x[0].tq, reverse = True )
        return links

    def get_links(self):
        now = dt.datetime.now(dt.timezone.utc)
        alllinks = []
        with tsdb.getSess() as sess:
            for (nid,rnid) in sess.execute( select(tsdb.Link.nodeid,tsdb.Link.remotenodeid)
                .distinct()
                .where(tsdb.Link.last_data >= now - dt.timedelta(days = 1))
                .where(tsdb.Link.tq > 0)
            ):
                thisnode = sess.get(tsdb.Node, {"nodeid":nid})
                othernode = sess.get(tsdb.Node, {"nodeid":rnid})
                if None in [thisnode,othernode]:
                    continue
                ids = (nid,rnid)
                if ids in alllinks:
                    continue
                alllinks.append(ids)
                thisloc  = getnodeloc(thisnode)
                otherloc = getnodeloc(othernode)
                stats = self.get_link_stats( thisnode, othernode, now )
                res = {
                    "link_id": "%s_%s" % ids,
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
        return self.cache("links_geojson",self.make_links_geojson, cachetime=300)

    def make_links_geojson(self):
        gjs = { "type": "FeatureCollection","features": [] }

        for l in self.get_links():
            gjs["features"].append( self.link2gjs( l ) )

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return bytes(json.dumps(gjs),"utf-8")
