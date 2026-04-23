#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, Host, Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, TCIntf

import argparse


TCIntf.bwParamMax = 100000

class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()


def parse_args():
    p = argparse.ArgumentParser(description='Urban Hospital <-> Urban Clinic Mininet Topology')

    # Hospital LAN (rcore <-> hospital switches, admin/clinical hosts)
    p.add_argument('--hlan-bw', type=float, default=10.0, help='Hospital LAN bandwidth (Gbps)')
    p.add_argument('--hlan-delay', default='2ms', help='Hospital LAN latency')
    p.add_argument('--hlan-jitter', default='1ms', help='Hospital LAN jitter')
    p.add_argument('--hlan-loss', type=float, default=0.01, help='Hospital LAN packet loss (%%)')

    # WAN Path A
    p.add_argument('--wan-a-bw', type=float, default=5.0, help='WAN Path A bandwidth (Gbps)')
    p.add_argument('--wan-a-delay', default='20ms', help='WAN Path A latency')
    p.add_argument('--wan-a-jitter', default='5ms', help='WAN Path A jitter')
    p.add_argument('--wan-a-loss', type=float, default=0.1, help='WAN Path A packet loss (%%)')

    # WAN Path B
    p.add_argument('--wan-b-bw', type=float, default=5.0, help='WAN Path B bandwidth (Gbps)')
    p.add_argument('--wan-b-delay', default='20ms', help='WAN Path B latency')
    p.add_argument('--wan-b-jitter', default='5ms', help='WAN Path B jitter')
    p.add_argument('--wan-b-loss', type=float, default=0.1, help='WAN Path B packet loss (%%)')

    # Clinic LAN (rclinic <-> s_remote <-> clinic hosts)
    p.add_argument('--clan-bw', type=float, default=1.0, help='Clinic LAN bandwidth (Gbps)')
    p.add_argument('--clan-delay', default='2ms', help='Clinic LAN latency')
    p.add_argument('--clan-jitter', default='1ms', help='Clinic LAN jitter')
    p.add_argument('--clan-loss', type=float, default=0.01, help='Clinic LAN packet loss (%%)')

    # IoT segment (patient monitors)
    p.add_argument('--iot-bw', type=float, default=0.1, help='IoT bandwidth (Gbps)')
    p.add_argument('--iot-delay', default='8ms', help='IoT latency')
    p.add_argument('--iot-jitter', default='2ms', help='IoT jitter')
    p.add_argument('--iot-loss', type=float, default=0.01, help='IoT packet loss (%%)')

    # VoIP segment (nurse station phones)
    p.add_argument('--voice-bw', type=float, default=0.01, help='VoIP bandwidth (Gbps)')
    p.add_argument('--voice-delay', default='2ms', help='VoIP latency')
    p.add_argument('--voice-jitter', default='1ms', help='VoIP jitter')
    p.add_argument('--voice-loss', type=float, default=0.01, help='VoIP packet loss (%%)')

    # Guest segment
    p.add_argument('--guest-bw', type=float, default=0.05, help='Guest bandwidth (Gbps)')
    p.add_argument('--guest-delay', default='15ms', help='Guest latency')
    p.add_argument('--guest-jitter', default='5ms', help='Guest jitter')
    p.add_argument('--guest-loss', type=float, default=1.0, help='Guest packet loss (%%)')

    # Server segment (EHR server)
    p.add_argument('--server-bw', type=float, default=1.0, help='Server bandwidth (Gbps)')
    p.add_argument('--server-delay', default='1ms', help='Server latency')
    p.add_argument('--server-jitter', default='1ms', help='Server jitter')
    p.add_argument('--server-loss', type=float, default=0.01, help='Server packet loss (%%)')

    args = p.parse_args()

    # Convert Gbps → Mbps for Mininet
    args.hlan_bw *= 1000.0
    args.wan_a_bw *= 1000.0
    args.wan_b_bw *= 1000.0
    args.clan_bw *= 1000.0
    args.iot_bw *= 1000.0
    args.voice_bw *= 1000.0
    args.guest_bw *= 1000.0
    args.server_bw *= 1000.0

    return args


def myNetwork():
    args = parse_args()

    net = Mininet(topo=None, build=False, ipBase='10.0.0.0/8')

    info('*** Adding controller\n')
    c0 = net.addController(name='c0', controller=Controller,
                           protocol='tcp', port=6633)

    info('*** Adding switches\n')
    s_admin = net.addSwitch('s_admin', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000001')
    s_clin = net.addSwitch('s_clin', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000002')
    s_iot = net.addSwitch('s_iot', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000003')
    s_voice = net.addSwitch('s_voice', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000004')
    s_guest = net.addSwitch('s_guest', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000005')
    s_server = net.addSwitch('s_server', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000006')
    s_remote = net.addSwitch('s_remote', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000007')

    # ── Routers ───────────────────────────────────────────────────────────────
    info('*** Adding routers\n')
    rcore = net.addHost('rcore', cls=LinuxRouter, ip='0.0.0.0')
    rclinic = net.addHost('rclinic', cls=LinuxRouter, ip='0.0.0.0')

    # WAN Path A
    wanr1a = net.addHost('wanr1a', cls=LinuxRouter, ip='0.0.0.0')
    wanr2a = net.addHost('wanr2a', cls=LinuxRouter, ip='0.0.0.0')
    wanr3a = net.addHost('wanr3a', cls=LinuxRouter, ip='0.0.0.0')

    # WAN Path B
    wanr1b = net.addHost('wanr1b', cls=LinuxRouter, ip='0.0.0.0')
    wanr2b = net.addHost('wanr2b', cls=LinuxRouter, ip='0.0.0.0')
    wanr3b = net.addHost('wanr3b', cls=LinuxRouter, ip='0.0.0.0')

    info('*** Adding hosts\n')
    admin1 = net.addHost('admin1', cls=Host, ip='10.10.10.11/24', defaultRoute='via 10.10.10.1')
    admin2 = net.addHost('admin2', cls=Host, ip='10.10.10.12/24', defaultRoute='via 10.10.10.1')
    client1 = net.addHost('client1', cls=Host, ip='10.10.20.21/24', defaultRoute='via 10.10.20.1')
    client2 = net.addHost('client2', cls=Host, ip='10.10.20.22/24', defaultRoute='via 10.10.20.1')
    client3 = net.addHost('client3', cls=Host, ip='10.10.20.23/24', defaultRoute='via 10.10.20.1')
    iot1 = net.addHost('iot1', cls=Host, ip='10.10.30.31/24', defaultRoute='via 10.10.30.1')
    voice1 = net.addHost('voice1', cls=Host, ip='10.10.40.41/24', defaultRoute='via 10.10.40.1')
    guest1 = net.addHost('guest1', cls=Host, ip='10.10.50.51/24', defaultRoute='via 10.10.50.1')
    server1 = net.addHost('server1', cls=Host, ip='10.10.60.61/24', defaultRoute='via 10.10.60.1')

    # Clinic Hosts
    clinic1 = net.addHost('clinic1', cls=Host, ip='10.20.10.10/24', defaultRoute='via 10.20.10.1')
    clinic2 = net.addHost('clinic2', cls=Host, ip='10.20.10.11/24', defaultRoute='via 10.20.10.1')

    info('*** Adding links\n')

    # rcore → hospital switches (determines rcore-eth0 through rcore-eth5)
    net.addLink(rcore, s_admin, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(rcore, s_clin, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(rcore, s_iot, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(rcore, s_voice, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(rcore, s_guest, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(rcore, s_server, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)

    # rcore → WAN Path A (rcore-eth6), rcore → WAN Path B (rcore-eth7)
    net.addLink(rcore, wanr1a, cls=TCLink, bw=args.wan_a_bw, delay=args.wan_a_delay, jitter=args.wan_a_jitter, loss=args.wan_a_loss)
    net.addLink(rcore, wanr1b, cls=TCLink, bw=args.wan_b_bw, delay=args.wan_b_delay, jitter=args.wan_b_jitter, loss=args.wan_b_loss)

    # WAN Path A chain: wanr1a-eth1 → wanr2a-eth0 → wanr3a-eth0 → rclinic-eth0
    net.addLink(wanr1a, wanr2a, cls=TCLink, bw=args.wan_a_bw, delay=args.wan_a_delay, jitter=args.wan_a_jitter, loss=args.wan_a_loss)
    net.addLink(wanr2a, wanr3a, cls=TCLink, bw=args.wan_a_bw, delay=args.wan_a_delay, jitter=args.wan_a_jitter, loss=args.wan_a_loss)
    net.addLink(wanr3a, rclinic, cls=TCLink, bw=args.wan_a_bw, delay=args.wan_a_delay, jitter=args.wan_a_jitter, loss=args.wan_a_loss)

    # WAN Path B chain: wanr1b-eth1 → wanr2b-eth0 → wanr3b-eth0 → rclinic-eth1
    net.addLink(wanr1b, wanr2b, cls=TCLink, bw=args.wan_b_bw, delay=args.wan_b_delay, jitter=args.wan_b_jitter, loss=args.wan_b_loss)
    net.addLink(wanr2b, wanr3b, cls=TCLink, bw=args.wan_b_bw, delay=args.wan_b_delay, jitter=args.wan_b_jitter, loss=args.wan_b_loss)
    net.addLink(wanr3b, rclinic, cls=TCLink, bw=args.wan_b_bw, delay=args.wan_b_delay, jitter=args.wan_b_jitter, loss=args.wan_b_loss)

    # rclinic → clinic LAN switch (rclinic-eth2)
    net.addLink(rclinic, s_remote, cls=TCLink, bw=args.clan_bw, delay=args.clan_delay, jitter=args.clan_jitter, loss=args.clan_loss)

    # Hospital hosts → switches
    net.addLink(s_admin, admin1, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(s_admin, admin2, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(s_clin, client1, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(s_clin, client2, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(s_clin, client3, cls=TCLink, bw=args.hlan_bw, delay=args.hlan_delay, jitter=args.hlan_jitter, loss=args.hlan_loss)
    net.addLink(s_iot, iot1, cls=TCLink, bw=args.iot_bw, delay=args.iot_delay, jitter=args.iot_jitter, loss=args.iot_loss)
    net.addLink(s_voice, voice1, cls=TCLink, bw=args.voice_bw,delay=args.voice_delay, jitter=args.voice_jitter, loss=args.voice_loss)
    net.addLink(s_guest, guest1, cls=TCLink, bw=args.guest_bw,delay=args.guest_delay, jitter=args.guest_jitter, loss=args.guest_loss)
    net.addLink(s_server, server1, cls=TCLink, bw=args.server_bw, delay=args.server_delay, jitter=args.server_jitter, loss=args.server_loss)

    # Clinic hosts → s_remote
    net.addLink(s_remote, clinic1, cls=TCLink, bw=args.clan_bw, delay=args.clan_delay, jitter=args.clan_jitter, loss=args.clan_loss)
    net.addLink(s_remote, clinic2, cls=TCLink, bw=args.clan_bw, delay=args.clan_delay, jitter=args.clan_jitter, loss=args.clan_loss)

    info('*** Starting network\n')
    net.build()

    info('*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info('*** Starting switches\n')
    net.get('s_admin').start([])
    net.get('s_clin').start([])
    net.get('s_iot').start([])
    net.get('s_voice').start([])
    net.get('s_guest').start([])
    net.get('s_server').start([])
    net.get('s_remote').start([])

    info('*** Configuring router interfaces\n')

    # rcore — LAN interfaces (eth0–eth5) and WAN interfaces (eth6–eth7)
    for i in range(8):
        rcore.cmd(f'ip addr flush dev rcore-eth{i}')
    rcore.cmd('ip addr add 10.10.10.1/24 dev rcore-eth0')
    rcore.cmd('ip addr add 10.10.20.1/24 dev rcore-eth1')
    rcore.cmd('ip addr add 10.10.30.1/24 dev rcore-eth2')
    rcore.cmd('ip addr add 10.10.40.1/24 dev rcore-eth3')
    rcore.cmd('ip addr add 10.10.50.1/24 dev rcore-eth4')
    rcore.cmd('ip addr add 10.10.60.1/24 dev rcore-eth5')
    rcore.cmd('ip addr add 192.168.1.2/24 dev rcore-eth6')  # WAN Path A
    rcore.cmd('ip addr add 192.168.11.2/24 dev rcore-eth7')  # WAN Path B

    # WAN Path A routers
    wanr1a.cmd('ip addr flush dev wanr1a-eth0')
    wanr1a.cmd('ip addr flush dev wanr1a-eth1')
    wanr1a.cmd('ip addr add 192.168.1.1/24 dev wanr1a-eth0')
    wanr1a.cmd('ip addr add 192.168.2.1/24 dev wanr1a-eth1')

    wanr2a.cmd('ip addr flush dev wanr2a-eth0')
    wanr2a.cmd('ip addr flush dev wanr2a-eth1')
    wanr2a.cmd('ip addr add 192.168.2.2/24 dev wanr2a-eth0')
    wanr2a.cmd('ip addr add 192.168.3.1/24 dev wanr2a-eth1')

    wanr3a.cmd('ip addr flush dev wanr3a-eth0')
    wanr3a.cmd('ip addr flush dev wanr3a-eth1')
    wanr3a.cmd('ip addr add 192.168.3.2/24 dev wanr3a-eth0')
    wanr3a.cmd('ip addr add 192.168.4.1/24 dev wanr3a-eth1')

    # WAN Path B routers
    wanr1b.cmd('ip addr flush dev wanr1b-eth0')
    wanr1b.cmd('ip addr flush dev wanr1b-eth1')
    wanr1b.cmd('ip addr add 192.168.11.1/24 dev wanr1b-eth0')
    wanr1b.cmd('ip addr add 192.168.12.1/24 dev wanr1b-eth1')

    wanr2b.cmd('ip addr flush dev wanr2b-eth0')
    wanr2b.cmd('ip addr flush dev wanr2b-eth1')
    wanr2b.cmd('ip addr add 192.168.12.2/24 dev wanr2b-eth0')
    wanr2b.cmd('ip addr add 192.168.13.1/24 dev wanr2b-eth1')

    wanr3b.cmd('ip addr flush dev wanr3b-eth0')
    wanr3b.cmd('ip addr flush dev wanr3b-eth1')
    wanr3b.cmd('ip addr add 192.168.13.2/24 dev wanr3b-eth0')
    wanr3b.cmd('ip addr add 192.168.14.1/24 dev wanr3b-eth1')

    # rclinic — eth0/eth1 = WAN A/B ingress, eth2 = clinic LAN
    for i in range(3):
        rclinic.cmd(f'ip addr flush dev rclinic-eth{i}')
    rclinic.cmd('ip addr add 192.168.4.2/24 dev rclinic-eth0')  # WAN Path A
    rclinic.cmd('ip addr add 192.168.14.2/24 dev rclinic-eth1')  # WAN Path B
    rclinic.cmd('ip addr add 10.20.10.1/24 dev rclinic-eth2')  # Clinic LAN

    info('*** Configuring static routes\n')

    # rcore → clinic subnet via both WAN paths (ECMP)
    rcore.cmd('ip route add 10.20.10.0/24 via 192.168.1.1')
    rcore.cmd('ip route add 10.20.10.0/24 via 192.168.11.1')

    # WAN Path A — forward to clinic
    wanr1a.cmd('ip route add 10.20.10.0/24 via 192.168.2.2')
    wanr2a.cmd('ip route add 10.20.10.0/24 via 192.168.3.2')
    wanr3a.cmd('ip route add 10.20.10.0/24 via 192.168.4.2')

    # WAN Path B — forward to clinic
    wanr1b.cmd('ip route add 10.20.10.0/24 via 192.168.12.2')
    wanr2b.cmd('ip route add 10.20.10.0/24 via 192.168.13.2')
    wanr3b.cmd('ip route add 10.20.10.0/24 via 192.168.14.2')

    # WAN Path A — return to hospital
    wanr1a.cmd('ip route add 10.10.0.0/16 via 192.168.1.2')
    wanr2a.cmd('ip route add 10.10.0.0/16 via 192.168.2.1')
    wanr3a.cmd('ip route add 10.10.0.0/16 via 192.168.3.1')

    # WAN Path B — return to hospital
    wanr1b.cmd('ip route add 10.10.0.0/16 via 192.168.11.2')
    wanr2b.cmd('ip route add 10.10.0.0/16 via 192.168.12.1')
    wanr3b.cmd('ip route add 10.10.0.0/16 via 192.168.13.1')

    # rclinic → hospital subnets via both WAN paths (ECMP)
    rclinic.cmd('ip route add 10.10.0.0/16 via 192.168.4.1')
    rclinic.cmd('ip route add 10.10.0.0/16 via 192.168.14.1')

    info('*** Post-configure complete\n')
    
    CLI(net)


if __name__ == '__main__':
    setLogLevel('info')
    myNetwork()
