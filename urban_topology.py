#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Controller, Node
from mininet.cli import CLI
from mininet.topo import Topo
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
        r_core = self.addNode("rcore", cls=LinuxRouter)

        # Clinic Router
        r_clinic = self.addNode("rclinic", cls=LinuxRouter)

        # WAN Routers (Path A)
        rA1 = self.addNode("wanr1a", cls=LinuxRouter)
        rA2 = self.addNode("wanr2a", cls=LinuxRouter)
        rA3 = self.addNode("wanr3a", cls=LinuxRouter)

        # WAN Routers (Path B)
        rB1 = self.addNode("wanr1b", cls=LinuxRouter)
        rB2 = self.addNode("wanr2b", cls=LinuxRouter)
        rB3 = self.addNode("wanr3b", cls=LinuxRouter)

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
        adm1 = self.addHost("admin1", ip="10.10.10.11/24", defaultRoute="via 10.10.10.1")
        adm2 = self.addHost("admin2", ip="10.10.10.12/24", defaultRoute="via 10.10.10.1")
        self.addLink(adm1, s_admin, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(adm2, s_admin, cls=TCLink, bw=1000, delay="2ms")

        # Urban Clinic Network Client Host Creation and Client to Switch Links
        clin1 = self.addHost("client1", ip="10.10.20.21/24", defaultRoute="via 10.10.20.1")
        clin2 = self.addHost("client2", ip="10.10.20.22/24", defaultRoute="via 10.10.20.1")
        clin3 = self.addHost("client3", ip="10.10.20.23/24", defaultRoute="via 10.10.20.1")
        self.addLink(clin1, s_clin, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clin2, s_clin, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clin3, s_clin, cls=TCLink, bw=1000, delay="2ms")

        # Urban Hospital IoT Host Creation and IoT to Switch Link
        """Patient monitors don't need as much bandwidth"""
        iot1 = self.addHost("iot1", ip="10.10.30.31/24", defaultRoute="via 10.10.30.1")
        self.addLink(iot1, s_iot, cls=TCLink, bw=100, delay="8ms")

        # Urban Hospital Voice Host Creation and Voice to Switch Link
        """Nurse station phones dont need as much bandwidth"""
        voip1 = self.addHost("voice1", ip="10.10.40.41/24", defaultRoute="via 10.10.40.1")
        self.addLink(voip1, s_voice, cls=TCLink, bw=10, delay="2ms")

        # Urban Hospital Guest Host Creation and Guest to Switch Link
        guest1 = self.addHost("guest1", ip="10.10.50.51/24", defaultRoute="via 10.10.50.1")
        self.addLink(guest1, s_guest, cls=TCLink, bw=50, delay="15ms", loss=1)

        # Urban Hospital Server Host Creation and Server to Switch Link
        ehr = self.addHost("server1", ip="10.10.60.61/24", defaultRoute="via 10.10.60.1")
        self.addLink(ehr, s_server, cls=TCLink, bw=1000, delay="1ms")

        # Urban Clinic Client Host Creation and Clinic Client to Switch Link
        clinic_pc1 = self.addHost("clinic1", ip="10.20.10.10/24", defaultRoute="via 10.20.10.1")
        clinic_pc2 = self.addHost("clinic2", ip="10.20.10.11/24", defaultRoute="via 10.20.10.1")
        self.addLink(r_clinic, s_remote, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clinic_pc1, s_remote, cls=TCLink, bw=1000, delay="2ms")
        self.addLink(clinic_pc2, s_remote, cls=TCLink, bw=1000, delay="2ms")

        # Urban WAN Link, Hospital Router to Clinic Router
        """Wan Side Values: Bandwidth = 1-10gb, Latency = 10-30ms,
        Packet Loss = 0.1%, Jitter = 5ms"""

        # WAN Path A
        self.addLink(r_core, rA1, cls=TCLink, bw=5000, delay="20ms", loss=0.1)
        self.addLink(rA1, rA2, cls=TCLink, bw=5000, delay="20ms", loss=0.1)
        self.addLink(rA2, rA3, cls=TCLink, bw=5000, delay="20ms", loss=0.1)
        self.addLink(rA3, r_clinic, cls=TCLink, bw=5000, delay="20ms", loss=0.1)

        # WAN Path B
        self.addLink(r_core, rB1, cls=TCLink, bw=5000, delay="20ms", loss=0.1)
        self.addLink(rB1, rB2, cls=TCLink, bw=5000, delay="20ms", loss=0.1)
        self.addLink(rB2, rB3, cls=TCLink, bw=5000, delay="20ms", loss=0.1)
        self.addLink(rB3, r_clinic, cls=TCLink, bw=5000, delay="20ms", loss=0.1)

# Create network, assing subnets, wan pathways, routes
if __name__ == "__main__":

    # Start  Topology
    net = Mininet(topo=UrbanHospitalTopo(), controller=Controller)
    net.start()

    # Get Routers
    r_core = net.get('rcore')
    r_clinic = net.get('rclinic')
    rA1 = net.get('wanr1a')
    rA2 = net.get('wanr2a')
    rA3 = net.get('wanr3a')
    rB1 = net.get('wanr1b')
    rB2 = net.get('wanr2b')
    rB3 = net.get('wanr3b')

    # LAN-side Interfaces
    # r-core LAN Interfaces
    r_core.setIP("10.10.10.1/24", intf="rcore-eth0")
    r_core.setIP("10.10.20.1/24", intf="rcore-eth1")
    r_core.setIP("10.10.30.1/24", intf="rcore-eth2")
    r_core.setIP("10.10.40.1/24", intf="rcore-eth3")
    r_core.setIP("10.10.50.1/24", intf="rcore-eth4")
    r_core.setIP("10.10.60.1/24", intf="rcore-eth5")

    # r-clinic LAN Interface
    r_clinic.setIP("10.20.10.1/24", intf="rclinic-eth0")

    # Assign Path A Router Interfaces
    r_core.setIP("192.168.1.2/24", intf="rcore-eth6")
    rA1.setIP("192.168.1.1/24", intf="wanr1a-eth0")
    rA1.setIP("192.168.2.1/24", intf="wanr1a-eth1")
    rA2.setIP("192.168.2.2/24", intf="wanr2a-eth0")
    rA2.setIP("192.168.3.1/24", intf="wanr2a-eth1")
    rA3.setIP("192.168.3.2/24", intf="wanr3a-eth0")
    rA3.setIP("192.168.4.1/24", intf="wanr3a-eth1")
    r_clinic.setIP("192.168.4.2/24", intf="rclinic-eth1")

    # Assign Path B Router Interfaces
    r_core.setIP("192.168.11.2/24", intf="rcore-eth7")
    rB1.setIP("192.168.11.1/24", intf="wanr1b-eth0")
    rB1.setIP("192.168.12.1/24", intf="wanr1b-eth1")
    rB2.setIP("192.168.12.2/24", intf="wanr2b-eth0")
    rB2.setIP("192.168.13.1/24", intf="wanr2b-eth1")
    rB3.setIP("192.168.13.2/24", intf="wanr3b-eth0")
    rB3.setIP("192.168.14.1/24", intf="wanr3b-eth1")
    r_clinic.setIP("192.168.14.2/24", intf="rclinic-eth2")

    # Routes From rcore To rclinic Subnets via Path A And Path B
    r_core.cmd("ip route add 10.20.10.0/24 via 192.168.1.1")
    r_core.cmd("ip route add 10.20.10.0/24 via 192.168.11.1")
    rA1.cmd("ip route add 10.20.10.0/24 via 192.168.2.2")
    rA2.cmd("ip route add 10.20.10.0/24 via 192.168.3.2")
    rA3.cmd("ip route add 10.20.10.0/24 via 192.168.4.2")
    rB1.cmd("ip route add 10.20.10.0/24 via 192.168.12.2")
    rB2.cmd("ip route add 10.20.10.0/24 via 192.168.13.2")
    rB3.cmd("ip route add 10.20.10.0/24 via 192.168.14.2")

    # Routes From rclinic to rcore Subnets via Path A and Path B
    rA1.cmd("ip route add 10.10.0.0/16 via 192.168.1.2")
    rA2.cmd("ip route add 10.10.0.0/16 via 192.168.2.1")
    rA3.cmd("ip route add 10.10.0.0/16 via 192.168.3.1")
    rB1.cmd("ip route add 10.10.0.0/16 via 192.168.11.2")
    rB2.cmd("ip route add 10.10.0.0/16 via 192.168.12.1")
    rB3.cmd("ip route add 10.10.0.0/16 via 192.168.13.1")
    r_clinic.cmd("ip route add 10.10.0.0/16 via 192.168.4.1")
    r_clinic.cmd("ip route add 10.10.0.0/16 via 192.168.14.1")

    # Start CLI
    CLI(net)

    net.stop()