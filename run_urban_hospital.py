#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from urban_hospital_topology import UrbanHospitalTopo

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
