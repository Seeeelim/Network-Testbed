import os, json
import subprocess
from datetime import datetime
import time


class TrafficGenerator:
    def __init__(self, net, topo_json_path):
        self.net = net
        self.topo_json_path = topo_json_path

        self.server_name = None
        self.active_hosts = []

        self.log_directory = "./trafficGenerator/trafficLogs"

    def start(self, attack_config):
        with open(self.topo_json_path, "r") as file:
            json_topo = json.load(file)

        for node in json_topo["nodes"]:
            if node["type"] == "host":
                self.active_hosts.append(node["id"])

        server = self.net.get(self.server_name)
        server_ip = server.IP()

        os.makedirs(self.log_directory, exist_ok=True)

        recv_log = self.log_directory + f"/recv_{self.server_name}.log"
        recv_cmd = f"ITGRecv -l {recv_log} &"

        server.cmd(recv_cmd)

        protocol = attack_config.get("protocol")
        packet_size = attack_config.get("packet_size")
        rate = attack_config.get("rate")
        duration = attack_config.get("duration")
        baseline_seconds = attack_config.get("baseline_seconds")
        attacker = attack_config.get("attacker")

        ditg_duration = (baseline_seconds + duration) * 1000

        senders = []

        for host_name in self.active_hosts:
            if host_name == self.server_name:
                continue
            if host_name == attacker:
                continue

            host = self.net.get(host_name)

            send_log = self.log_directory + f"/send_{host.name}.log"
            send_cmd = (f"ITGSend -a {server_ip} -T {protocol} -c {packet_size} -C {rate} -t {ditg_duration} -l {send_log}")
            
            host.sendCmd(send_cmd)
            senders.append(host)

        return senders

        # print("[DITG] Background traffic running")

    def stop(self):
        print("[DITG] Stopping background traffic...")
        subprocess.run(["sudo", "pkill", "-f", "ITGSend"])
        subprocess.run(["sudo", "pkill", "-f", "ITGRecv"])
        print("[DITG] All D-ITG processes stopped")

    def decode_logs(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = self.log_directory + "/" + timestamp
        os.makedirs(output_dir, exist_ok=True)

        recv_log = self.log_directory + f"/recv_{self.server_name}.log"

        with open(output_dir + f"/recv_{self.server_name}.txt", "w") as file:
            subprocess.run(["ITGDec", recv_log], stdout=file)

        for host_name in self.active_hosts:
            if host_name == self.server_name:
                continue

            host = self.net.get(host_name)
            send_log = self.log_directory + f"/send_{host.name}.log"

            with open(output_dir + f"/send_{host.name}.txt", "w") as file:
                subprocess.run(["ITGDec", send_log], stdout=file)

        for file in os.listdir(self.log_directory):
            if file.endswith(".log"):
                os.remove(os.path.join(self.log_directory, file))

        print("[DITG] Raw Files Decoded")

    def run_attack(self, attack_config):
        attack = attack_config.get("attack_script")

        attacker = self.net.get(attack_config.get("attacker"))
        target = self.net.get(attack_config.get("target"))
        receiver = self.net.get(attack_config.get("receiver"))

        target_ip = target.IP()
        receiver_ip = receiver.IP()
        duration = attack_config.get("duration")

        cmd = (f"python3 {attack} "
               f"--target-ip {target_ip} "
               f"--receiver-ip {receiver_ip} "
               f"--duration {duration}")
        attacker.sendCmd(cmd)

    def stop_attack(self, attack_config):
        attacker = self.net.get(attack_config.get("attacker"))
        attacker.waitOutput()


    def demo(self):
        attack_config = {}
        with open("./attack_config.json", "r") as config_file:
            attack_config = json.load(config_file)

        self.server_name = attack_config.get("receiver")
        baseline_seconds = attack_config.get("baseline_seconds")
        attack_duration = attack_config.get("duration")
        runs = attack_config.get("runs")

        for i in range(runs):
            print(f"\n[DITG] Starting simulation run {i+1}/{runs}...")
            
            self.active_hosts = []

            senders = self.start(attack_config)

            print(f"[DITG] Baseline traffic for {baseline_seconds} seconds...")
            time.sleep(baseline_seconds)

            if attack_config.get("attack_script"):
                self.run_attack(attack_config)
                print(f"[DITG] Attack running for {attack_duration} seconds...")
                time.sleep(attack_duration)
                self.stop_attack(attack_config)

            for sender in senders:
                sender.waitOutput()

            print("[DITG] Ending traffic...")

            self.stop()
            print("[DITG] Traffic generator stoped")

            print("[DITG] Decoding logs...")
            self.decode_logs()
            print("[DITG] Logs decoded and saved")

            if i < runs - 1:
                time.sleep(2)

        print("[DITG] All runs complete. Check logs for details")


def start(net, topo_json_path):
    # make into loop if we want to run demo multiple times without restarting
    tg = TrafficGenerator(net, topo_json_path)
    tg.demo()

