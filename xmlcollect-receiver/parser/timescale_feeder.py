import os
import copy
import datetime
import tsdb

class TimescaleFeeder:
    def __init__(self):
        self.sess = None

    def feed(self,res):
        if not self.sess:
            self.sess = tsdb.getSess()
            self.sess.begin()
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
        if "nodeinfo" in res and "routes" in res:
            ni = copy.deepcopy( res["nodeinfo"] )
            stat = res.get("statistics",{})

            contact = ni.get("owner",{}).get("contact",None)
            loc = ni.get("location",{})

            ni["software"]["ffpcollect"] = res.get("scriptver",None)
            software = ni["software"]

            for d,dc in ni["network"]["mesh"].items():
                for i,a in dc.get("interfaces",{}).items():
                    macaddrs |= set(a)
            ni["network"].pop("mesh",None)
            ni["network"]["gateway"] = stat.get("gateway",None)
            ni["network"]["nexthop"] = stat.get("gateway_nexthop",None)
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
                node.loc_lon = loc.get("longitude",None)
                node.loc_lat = loc.get("latitude",None)
            if len(macaddrs) > 0:
                node.macaddrs = []
                for mac in macaddrs:
                    node.macaddrs.append(tsdb.MacAddr(mac=mac))
            if network:
                node.network = network
            if software:
                node.software = software
            if ni and "hardware" in ni:
                node.hw_model = ni["hardware"].get("model",None)
                node.hw_nproc = ni["hardware"].get("nproc",None)
        if software and "autoupdater" in software and "firmware" in software:
            s = self.sess.get(tsdb.SwStat, {"nodeid":nid,"timestamp":t})
            if not s:
                s = tsdb.SwStat( nodeid=nid, timestamp=t )
                self.sess.add(s)
            s.domain = ni.get("system",{}).get("domain_code",None)
            s.au_branch = software["autoupdater"].get("branch",None)
            s.au_enabled = software["autoupdater"].get("enabled",None)
            s.fw_base = software["firmware"].get("base",None)
            s.fw_release = software["firmware"].get("release",None)

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
                idattr = {
                    "lnodeid":lnode.nodeid,
                    "rnodeid":rnode.nodeid,
                    "lmac":lmac,
                    "rmac":rmac,
                    "timestamp":t
                }
                l = self.sess.get(tsdb.Link, idattr)
                if not l:
                    l = tsdb.Link( **idattr )
                    self.sess.add(l)
                l.tq = attrs.get("tq",None)
                l.lastseen = attrs.get("lastseen",None)
                l.best = attrs.get("best",None)

    def feedts_conn(self,nid,t,res):
        for l3p,conns in res["conn"].items():
            for l4p,num in conns.items():
                s = self.sess.get(tsdb.ConnStat, {"nodeid":nid,"timestamp":t, "l3proto":l3p, "l4proto": l4p})
                if not s:
                    s = tsdb.ConnStat( nodeid=nid, timestamp=t, l3proto=l3p, l4proto=l4p )
                    self.sess.add(s)
                s.value = num

    def feedts_statistics(self,nid,t,res):
        for sect in ["clients","traffic","memory","stat"]:
            if sect in res["statistics"] and hasattr(self,"feedts_statistics_%s" % sect):
                getattr(self,"feedts_statistics_%s" % sect)(nid,t,res)

    def feedts_statistics_clients(self,nid,t,res):
        s = self.sess.get(tsdb.ClientStat, {"nodeid":nid,"timestamp":t})
        if not s:
            s = tsdb.ClientStat( nodeid=nid, timestamp=t )
            self.sess.add(s)
        stats = res["statistics"]["clients"]
        s.total  = stats.get("total",0)
        s.wifi   = stats.get("wifi",0)
        s.wifi24 = stats.get("wifi24",0)
        s.wifi5  = stats.get("wifi5",0)
        s.owe    = stats.get("owe",0)
        s.owe24  = stats.get("owe24",0)
        s.owe5   = stats.get("owe5",0)

    def feedts_statistics_traffic(self,nid,t,res):
        s = self.sess.get(tsdb.TrafficStat, {"nodeid":nid,"timestamp":t})
        if not s:
            s = tsdb.TrafficStat( nodeid=nid, timestamp=t )
            self.sess.add(s)
        stats = res["statistics"]["traffic"]
        s.rx_bytes = stats.get("rx",{}).get("bytes",None)
        s.rx_pkgs  = stats.get("rx",{}).get("packets",None)
        s.tx_bytes   = stats.get("tx",{}).get("bytes",None)
        s.tx_pkgs    = stats.get("tx",{}).get("packets",None)
        s.tx_dropped = stats.get("tx",{}).get("dropped",None)
        s.fw_bytes = stats.get("forward",{}).get("bytes",None)
        s.fw_pkgs  = stats.get("forward",{}).get("packets",None)
        s.mgmt_rx_bytes = stats.get("mgmt_rx",{}).get("bytes",None)
        s.mgmt_rx_pkgs  = stats.get("mgmt_rx",{}).get("packets",None)
        s.mgmt_tx_bytes = stats.get("mgmt_tx",{}).get("bytes",None)
        s.mgmt_tx_pkgs  = stats.get("mgmt_tx",{}).get("packets",None)

    def feedts_statistics_memory(self,nid,t,res):
        s = self.sess.get(tsdb.MemStat, {"nodeid":nid,"timestamp":t})
        if not s:
            s = tsdb.MemStat( nodeid=nid, timestamp=t )
            self.sess.add(s)
        stat = res["statistics"]["memory"]
        s.total     = stat.get("total",None)
        s.free      = stat.get("free",None)
        s.available = stat.get("available",None)
        s.buffers   = stat.get("buffers",None)
        s.cached    = stat.get("cached",None)

    def feedts_statistics_stat(self,nid,t,res):
        stat = res["statistics"]["stat"].pop("cpu",None)
        if stat:
            s = self.sess.get(tsdb.CpuStat, {"nodeid":nid,"timestamp":t})
            if not s:
                s = tsdb.CpuStat( nodeid=nid, timestamp=t )
                self.sess.add(s)
            s.user    = stat.get("user",None)
            s.nice    = stat.get("nice",None)
            s.system  = stat.get("system",None)
            s.idle    = stat.get("idle",None)
            s.iowait  = stat.get("iowait",None)
            s.irq     = stat.get("irq",None)
            s.softirq = stat.get("softirq",None)
        s = self.sess.get(tsdb.NodeStat, {"nodeid":nid,"timestamp":t})
        if not s:
            s = tsdb.NodeStat( nodeid=nid, timestamp=t )
            self.sess.add(s)
        s.gateway_tq =   res["statistics"].get("gateway_tq",None)
        s.rootfs_usage = res["statistics"].get("rootfs_usage",None)
        s.uptime =       res["statistics"].get("uptime",None)
        s.idletime =     res["statistics"].get("idletime",None)
        s.loadavg =      res["statistics"].get("loadavg",None)
        s.proc_running = res["statistics"].get("processes",{}).get("running",None)
        s.proc_total =   res["statistics"].get("processes",{}).get("total",None)
        s.other =        res["statistics"]["stat"]

    def postprocess(self, host):
        if self.sess:
            self.sess.commit()
            self.sess.close()
            self.sess = None
