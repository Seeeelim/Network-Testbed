#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.node import Node
from mininet.link import TCLink

# Router Creation, routers do not exist in mininet so need their own class
class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()

# Topology
class UrbanHospitalTopo(Topo):
    def build(self):

        # Hospital Switches
        s_admin = self.addSwitch("s_admin", dpid="0000000000000001")
        s_clin = self.addSwitch("s_clin", dpid="0000000000000002")
        s_iot = self.addSwitch("s_iot", dpid="0000000000000003")
        s_voice = self.addSwitch("s_voice", dpid="0000000000000004")
        s_guest = self.addSwitch("s_guest", dpid="0000000000000005")
        s_server = self.addSwitch("s_server", dpid="0000000000000006")

        # Clinic Switch
        s_remote = self.addSwitch("s_remote", dpid="0000000000000007")

        # Hospital Router
        r_core = self.addNode("r-core", cls=LinuxRouter)

        # Clinic Router
        r_clinic = self.addNode("r-clinic", cls=LinuxRouter)

        # Urban Hospital Switch to Router Links
        """Lan Side Values: Bandwidth = 10-40gb, Latency = 1-2ms,
        Packet Loss = 0.01%, Jitter = 1ms"""
        self.addLink(r_core, s_admin, cls=TCLink, bw=10000, delay="2ms")
        self.addLink(r_core, s_clin, cls=TCLink, bw=10000, delay="2ms")
        self.addLink(r_core, s_iot, cls=TCLink, bw=10000, delay="2ms")
        self.addLink(r_core, s_voice, cls=TCLink, bw=10000, delay="2ms")
        self.addLink(r_core, s_guest, cls=TCLink, bw=10000, delay="2ms")
        self.addLink(r_core, s_server, cls=TCLink, bw=10000, delay="2ms")

        # Urban Hospital Admin Host Creation and Admin to Switch Links
        adm1 = self.addHost("admin-1", ip="10.10.10.11/24", defaultRoute="via 10.10.10.1")
        adm2 = self.addHost("admin-2", ip="10.10.10.12/24", defaultRoute="via 10.10.10.1")
        self.addLink(adm1, s_admin, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(adm2, s_admin, cls=TCLink, bw=1000, delay="2ms")

        # Urban Clinic Network Client Host Creation and Client to Switch Links
        clin1 = self.addHost("client-1", ip="10.10.20.21/24", defaultRoute="via 10.10.20.1")
        clin2 = self.addHost("client-2", ip="10.10.20.22/24", defaultRoute="via 10.10.20.1")
        clin3 = self.addHost("client-3", ip="10.10.20.23/24", defaultRoute="via 10.10.20.1")
        self.addLink(clin1, s_clin, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clin2, s_clin, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clin3, s_clin, cls=TCLink, bw=1000, delay="2ms")

        # Urban Hospital IoT Host Creation and IoT to Switch Link
        """Patient monitors don't need as much bandwidth"""
        iot1 = self.addHost("iot-1", ip="10.10.30.31/24", defaultRoute="via 10.10.30.1")
        self.addLink(iot1, s_iot, cls=TCLink, bw=100, delay="8ms")

        # Urban Hospital Voice Host Creation and Voice to Switch Link
        """Nurse station phones dont need as much bandwidth"""
        voip1 = self.addHost("voice-1", ip="10.10.40.41/24", defaultRoute="via 10.10.40.1")
        self.addLink(voip1, s_voice, cls=TCLink, bw=10, delay="2ms")

        # Urban Hospital Guest Host Creation and Guest to Switch Link
        guest1 = self.addHost("guest-1", ip="10.10.50.51/24", defaultRoute="via 10.10.50.1")
        self.addLink(guest1, s_guest, cls=TCLink, bw=50, delay="15ms", loss=1)

        # Urban Hospital Server Host Creation and Server to Switch Link
        ehr = self.addHost("server-1", ip="10.10.60.61/24", defaultRoute="via 10.10.60.1")
        self.addLink(ehr, s_dc, cls=TCLink, bw=1000, delay="1ms")

        # Urban Clinic Client Host Creation and Clinic Client to Switch Link
        clinic_pc1 = self.addHost("client-clinic-1", ip="10.20.10.10/24", defaultRoute="via 10.20.10.1")
        clinic_pc2 = self.addHost("clinic-clinic-2", ip="10.20.10.11/24", defaultRoute="via 10.20.10.1")
        self.addLink(r_clinic, s_remote, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clinic_pc1, s_remote, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clinic_pc2, s_remote, cls=TCLink, bw=1000, delay="2ms")

        # Urban WAN Link, Hospital Router to Clinic Router
        """Lan Side Values: Bandwidth = 1-10gb, Latency = 10-30ms,
        Packet Loss = 0.1%, Jitter = 5ms"""
        self.addLink(r_core, r_clinic, cls=TCLink, bw=5000, delay="20ms", loss=0.1)

# Required for mn --custom from cmdline
topos = {
    "urbanhospital": UrbanHospitalTopo
}

# to run in commandline for mininet
"""sudo mn --customer urban_hospital_topology.py --topo urbanhospital
 --controller remote"""