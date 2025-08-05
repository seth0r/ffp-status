import os
import copy
import datetime
from sqlalchemy import select,between
import tsdb

class TimescaleFeeder:
    def __init__(self):
        self.sess = None
        self.times = None

    def query_Stat(self, stat, **kwargs):
        if self.times and stat.__name__ in self.times:
            ts = kwargs["timestamp"]
            s = None
            if ts in self.times[ stat.__name__ ]:
                s = self.sess.get(stat, kwargs)
                if s and not s.compacted:
                    return
            if not s:
                self.times[ stat.__name__ ].add(ts)
                s = stat( **kwargs )
                self.sess.add(s)
        else:
            s = self.sess.get(stat, kwargs)
            if not s:
                s = stat( **kwargs )
                self.sess.add(s)
            elif not s.compacted:
                return
        s.compacted = False
        return s

    def preprocess(self, host, files):
        if self.sess:
            self.sess.close()
        self.sess = tsdb.getSess()
        self.sess.begin()
        self.times = {}
        self.prepare_times(host,files)

    def prepare_times(self,host,files):
        try:
            first = int(files[0].partition(".")[0])
            last = int(files[-1].partition(".")[0])
        except ValueError:
            return
        self.logger.debug("Loading times from %d to %d..." % (first,last))
        if last - first > 24*60*60:
            first_files = []
            last_files = []
            for f in files:
                try:
                    ft = int(f.partition(".")[0])
                except ValueError:
                    continue
                if abs(ft - first) < abs(last - ft):
                    first_files.append(f)
                else:
                    last_files.append(f)
            self.prepare_times(host,first_files)
            self.prepare_times(host,last_files)
            return
        first = datetime.datetime.utcfromtimestamp( first )
        last = datetime.datetime.utcfromtimestamp( last )
        nids = sorted( self.sess.execute( select( tsdb.Node ).with_only_columns( tsdb.Node.nodeid ).where( tsdb.Node.hostname == host ) ).scalars().all() )
        if len(nids) == 0:
            return
        for stat in tsdb.Stat.__subclasses__():
            if stat.__name__ not in self.times:
                self.times[ stat.__name__ ] = set()
            times = self.times[ stat.__name__ ]
            for nid in nids:
                new = set( self.sess.execute( select( stat )
                    .with_only_columns( stat.timestamp )
                    .where( stat.nodeid == nid )
                    .where( between( stat.timestamp,first,last ) ) 
                ).scalars().all() )
                times.update( new )
                self.logger.debug("%s.%s: %d" % (stat.__name__,nid,len(new)))


    def feed(self,res):
        res = res.todict()
        t = datetime.datetime.utcfromtimestamp( res["time"] )
        nid = res["node_id"]
        self.feedts_nodes(nid,t,res)
        if "statistics" in res:
            self.feedts_statistics(nid,t,res)
        if "conn" in res:
            self.feedts_conn(nid,t,res)
        if "neighbours" in res:
            self.feedts_neighbours(nid,t,res)

    def feedts_nodes(self,nid,t,res):
        host = res["host"]
        macaddrs = set()
        ni = None
        network = None
        software = None
        loc = None
        contact = False
        uptime = None
        if "nodeinfo" in res and "routes" in res:
            ni = copy.deepcopy( res["nodeinfo"] )
            stat = res.get("statistics",{})

            contact = ni.get("owner",{}).get("contact",None)
            loc = ni.get("location",{})

            uptime = stat.get("uptime",None)

            ni["software"]["ffpcollect"] = res.get("scriptver",None)
            software = ni["software"]

            for d,dc in ni["network"]["mesh"].items():
                for i,a in dc.get("interfaces",{}).items():
                    macaddrs |= set(a)
            ni["network"].pop("mesh",None)
            ni["network"]["gateway"] = stat.get("gateway")
            ni["network"]["nexthop"] = stat.get("gateway_nexthop")
            ni["network"]["mesh_vpn"]["peers"] = []
            for p,c in stat.get("mesh_vpn",{}).get("groups",{}).get("backbone",{}).get("peers",{}).items():
                if c is not None and c.get("established",0) > 0:
                    ni["network"]["mesh_vpn"]["peers"].append( p )
            network = ni["network"]
            network["routes"] = res["routes"]

        node = self.sess.get(tsdb.Node, {"nodeid":nid})
        if not node:
            node = tsdb.Node( nodeid=nid, hostname=host )
            self.sess.add(node)
            self.logger.info("New node %s with hostname %s.", nid, host)
        if not node.last_data or t > node.last_data:
            node.last_data = t
            if host != node.hostname:
                self.logger.info("Nodes hostname of %s changed from %s to %s.", nid, node.hostname, host)
                node.hostname = host
            if contact is not False and contact != node.contact:
                node.contact = contact
                node.last_contact_update = t
                node.owners = []
            if loc is not None:
                node.loc_lon = loc.get("longitude")
                node.loc_lat = loc.get("latitude")
            if uptime:
                node.uptime = uptime
            if len(macaddrs) > 0:
                node.macaddrs = []
                for mac in macaddrs:
                    node.macaddrs.append(tsdb.MacAddr(mac=mac))
            if network:
                node.network = network
            if software:
                node.software = software
            if ni and "hardware" in ni:
                node.hw_model = ni["hardware"].get("model")
                node.hw_nproc = ni["hardware"].get("nproc")
            if ni and "system" in ni and "domain_code" in ni["system"]:
                node.domain = ni["system"]["domain_code"]
        if software and "autoupdater" in software and "firmware" in software:
            s = self.sess.get(tsdb.SwStat, {"nodeid":nid,"timestamp":t})
            if s and not s.compacted:
                return
            elif not s:
                s = tsdb.SwStat( nodeid=nid, timestamp=t )
                self.sess.add(s)
            s.compacted = False
            s.domain = ni["system"]["domain_code"]
            s.au_branch = software["autoupdater"]["branch"]
            s.au_enabled = software["autoupdater"]["enabled"]
            s.fw_base = software["firmware"]["base"]
            s.fw_release = software["firmware"]["release"]

    def feedts_neighbours(self,nid,t,res):
        for lmac,neigh in res["neighbours"].items():
            lmacobj = self.sess.get(tsdb.MacAddr, {"mac":lmac})
            if lmacobj is None:
                continue
            lnode = lmacobj.node
            for rmac,attrs in neigh.items():
                rmacobj = self.sess.get(tsdb.MacAddr, {"mac":rmac})
                if rmacobj is None:
                    continue
                rnode = rmacobj.node
                lh = self.query_Stat( tsdb.LinkHist,
                    nodeid = lnode.nodeid,
                    remotenodeid = rnode.nodeid,
                    mac = lmac,
                    remotemac = rmac,
                    timestamp = t )
                if lh:
                    lh.tq = attrs["tq"]
                    lh.lastseen = attrs["lastseen"]
                    lh.best = attrs["best"]
                l = self.sess.get(tsdb.Link, {
                    "nodeid" : lnode.nodeid,
                    "remotenodeid" : rnode.nodeid,
                    "mac" : lmac,
                    "remotemac" : rmac,
                })
                if not l:
                    l = tsdb.Link(
                        nodeid = lnode.nodeid,
                        remotenodeid = rnode.nodeid,
                        mac = lmac,
                        remotemac = rmac
                    )
                    self.sess.add(l)
                if not l.last_data or t > l.last_data:
                    l.last_data = t
                    l.tq = attrs["tq"]
                    l.lastseen = attrs["lastseen"]
                    l.best = attrs["best"]

    def feedts_conn(self,nid,t,res):
        for l3p,conns in res["conn"].items():
            for l4p,num in conns.items():
                s = self.query_Stat( tsdb.ConnStat, nodeid=nid, timestamp=t, l3proto=l3p, l4proto=l4p )
                if s:
                    s.value = num

    def feedts_statistics(self,nid,t,res):
        for sect in ["clients","traffic","memory","stat"]:
            if sect in res["statistics"] and hasattr(self,"feedts_statistics_%s" % sect):
                getattr(self,"feedts_statistics_%s" % sect)(nid,t,res)

    def feedts_statistics_clients(self,nid,t,res):
        s = self.query_Stat( tsdb.ClientStat, nodeid=nid, timestamp=t )
        if s:
            stats = res["statistics"]["clients"]
            s.total  = stats.get("total",0)
            s.wifi   = stats.get("wifi",0)
            s.wifi24 = stats.get("wifi24",0)
            s.wifi5  = stats.get("wifi5",0)
            s.owe    = stats.get("owe",0)
            s.owe24  = stats.get("owe24",0)
            s.owe5   = stats.get("owe5",0)

    def feedts_statistics_traffic(self,nid,t,res):
        s = self.query_Stat( tsdb.TrafficStat, nodeid=nid, timestamp=t )
        if s:
            stats = res["statistics"]["traffic"]
            s.rx_bytes = stats["rx"]["bytes"]
            s.rx_pkgs  = stats["rx"]["packets"]
            s.tx_bytes   = stats["tx"]["bytes"]
            s.tx_pkgs    = stats["tx"]["packets"]
            s.tx_dropped = stats["tx"]["dropped"]
            s.fw_bytes = stats["forward"]["bytes"]
            s.fw_pkgs  = stats["forward"]["packets"]
            s.mgmt_rx_bytes = stats["mgmt_rx"]["bytes"]
            s.mgmt_rx_pkgs  = stats["mgmt_rx"]["packets"]
            s.mgmt_tx_bytes = stats["mgmt_tx"]["bytes"]
            s.mgmt_tx_pkgs  = stats["mgmt_tx"]["packets"]

    def feedts_statistics_memory(self,nid,t,res):
        s = self.query_Stat( tsdb.MemStat, nodeid=nid, timestamp=t )
        if s:
            stat = res["statistics"]["memory"]
            s.total     = stat["total"]
            s.free      = stat["free"]
            s.available = stat["available"]
            s.buffers   = stat["buffers"]
            s.cached    = stat["cached"]

    def feedts_statistics_stat_cpu(self,nid,t,res):
        stat = res["statistics"]["stat"].pop("cpu",None)
        if stat:
            s = self.query_Stat( tsdb.CpuStat, nodeid=nid, timestamp=t )
            if s:
                s.user    = stat["user"]
                s.nice    = stat["nice"]
                s.system  = stat["system"]
                s.idle    = stat["idle"]
                s.iowait  = stat["iowait"]
                s.irq     = stat["irq"]
                s.softirq = stat["softirq"]

    def feedts_statistics_stat(self,nid,t,res):
        self.feedts_statistics_stat_cpu(nid,t,res)
        s = self.query_Stat( tsdb.NodeStat, nodeid=nid, timestamp=t )
        if s:
            s.gateway_tq =   res["statistics"].get("gateway_tq",0)
            s.rootfs_usage = res["statistics"]["rootfs_usage"]
            s.uptime =       res["statistics"]["uptime"]
            s.idletime =     res["statistics"]["idletime"]
            s.loadavg =      res["statistics"]["loadavg"]
            s.proc_running = res["statistics"]["processes"]["running"]
            s.proc_total =   res["statistics"]["processes"]["total"]
            s.other =        res["statistics"]["stat"]

    def postprocess(self, host):
        if self.sess:
            self.sess.commit()
            self.sess.close()
            self.sess = None
            self.times = None
