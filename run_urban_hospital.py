#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from urban_hospital_topology import UrbanHospitalTopo

# Start  Topology
net = Mininet(topo=UrbanHospitalTopo(), controller=Controller)
net.start()

# Get Routers
r_core = net.get('r-core')
r_clinic = net.get('r-clinic')
rA1 = net.get('wan-r1a')
rA2 = net.get('wan-r2a')
rA3 = net.get('wan-r3a')
rB1 = net.get('wan-r1b')
rB2 = net.get('wan-r2b')
rB3 = net.get('wan-r3b')

# LAN-side Interfaces
# r-core LAN Interfaces
r_core.setIP("10.10.10.1/24", intf="r-core-eth0")
r_core.setIP("10.10.20.1/24", intf="r-core-eth1")
r_core.setIP("10.10.30.1/24", intf="r-core-eth2")
r_core.setIP("10.10.40.1/24", intf="r-core-eth3")
r_core.setIP("10.10.50.1/24", intf="r-core-eth4")
r_core.setIP("10.10.60.1/24", intf="r-core-eth5")

# r-clinic LAN Interface
r_clinic.setIP("10.20.10.1/24", intf="r-clinic-eth0")

# Assign Path A Router Interfaces
r_core.setIP("192.168.1.2/24", intf="r-core-eth6")
rA1.setIP("192.168.1.1/24", intf="wan-r1a-eth0")
rA1.setIP("192.168.2.1/24", intf="wan-r1a-eth1")
rA2.setIP("192.168.2.2/24", intf="wan-r2a-eth0")
rA2.setIP("192.168.3.1/24", intf="wan-r2a-eth1")
rA3.setIP("192.168.3.2/24", intf="wan-r3a-eth0")
rA3.setIP("192.168.4.1/24", intf="wan-r3a-eth1")
r_clinic.setIP("192.168.4.2/24", intf="r-clinic-eth1")

# Assign Path B Router Interfaces
r_core.setIP("192.168.11.2/24", intf="r-core-eth7")
rB1.setIP("192.168.11.1/24", intf="wan-r1b-eth0")
rB1.setIP("192.168.12.1/24", intf="wan-r1b-eth1")
rB2.setIP("192.168.12.2/24", intf="wan-r2b-eth0")
rB2.setIP("192.168.13.1/24", intf="wan-r2b-eth1")
rB3.setIP("192.168.13.2/24", intf="wan-r3b-eth0")
rB3.setIP("192.168.14.1/24", intf="wan-r3b-eth1")
r_clinic.setIP("192.168.14.2/24", intf="r-clinic-eth2")

# Routes From r_core To r-clinic Subnets via Path A And Path B
r_core.cmd("ip route add 10.20.10.0/24 via 192.168.1.1")
r_core.cmd("ip route add 10.20.10.0/24 via 192.168.11.1")

rA1.cmd("ip route add 10.20.10.0/24 via 192.168.2.2")
rA2.cmd("ip route add 10.20.10.0/24 via 192.168.3.2")
rA3.cmd("ip route add 10.20.10.0/24 via 192.168.4.2")

rB1.cmd("ip route add 10.20.10.0/24 via 192.168.12.2")
rB2.cmd("ip route add 10.20.10.0/24 via 192.168.13.2")
rB3.cmd("ip route add 10.20.10.0/24 via 192.168.14.2")

# Routes From r-clinic to r-core Subnets via Path A and Path B
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
