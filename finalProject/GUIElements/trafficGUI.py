#!/usr/bin/env python3
"""
D-ITG Tracer — Mininet CLI wrapper with D-ITG form
Run with: sudo python3 ditg_tracer.py
"""

import sys
import os
import time
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QLineEdit,
    QComboBox, QSpinBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal


# currently, hardcoded for the two demo topologies, but could be extended to read from a config file or directory
TOPOLOGIES = {
    "Rural to Hospital": {
        "script": "rural_urban.py",
        "hosts": {
            "rH1 (10.10.10.2)": ("rH1", "10.10.10.2"),
            "rH2 (10.10.10.3)": ("rH2", "10.10.10.3"),
            "rH3 (10.10.10.4)": ("rH3", "10.10.10.4"),
            "rH4 (10.10.10.5)": ("rH4", "10.10.10.5"),
            "aH1 (10.20.10.2)": ("aH1", "10.20.10.2"),
            "aH2 (10.20.10.3)": ("aH2", "10.20.10.3"),
            "aH3 (10.20.10.4)": ("aH3", "10.20.10.4"),
            "cH1 (10.20.20.2)": ("cH1", "10.20.20.2"),
            "cH2 (10.20.20.3)": ("cH2", "10.20.20.3"),
            "cH3 (10.20.20.4)": ("cH3", "10.20.20.4"),
            "iH1 (10.20.30.2)": ("iH1", "10.20.30.2"),
            "iH2 (10.20.30.3)": ("iH2", "10.20.30.3"),
            "iH3 (10.20.30.4)": ("iH3", "10.20.30.4"),
        },
    },
    "Urban Hospital": {
        "script": "urban_urban.py",
        "hosts": {
            "admin1 (10.10.10.11)": ("admin1", "10.10.10.11"),
            "admin2 (10.10.10.12)": ("admin2", "10.10.10.12"),
            "client1 (10.10.20.21)": ("client1", "10.10.20.21"),
            "client2 (10.10.20.22)": ("client2", "10.10.20.22"),
            "client3 (10.10.20.23)": ("client3", "10.10.20.23"),
            "iot1 (10.10.30.31)": ("iot1", "10.10.30.31"),
            "voice1 (10.10.40.41)": ("voice1", "10.10.40.41"),
            "guest1 (10.10.50.51)": ("guest1", "10.10.50.51"),
            "server1 (10.10.60.61)": ("server1", "10.10.60.61"),
            "clinic1 (10.20.10.10)": ("clinic1", "10.20.10.10"),
            "clinic2 (10.20.10.11)": ("clinic2", "10.20.10.11"),
        },
    },
}

PROTOCOLS = ["UDP", "TCP", "ICMP"]
LOG_DIR = "./trafficGenerator/trafficLogs"


class MininetRunner(QThread):
    output_line = pyqtSignal(str)

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
        self.process = None

    def run(self):
        self.process = subprocess.Popen(
            ["sudo", "python3", "-u", self.script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in self.process.stdout:
            self.output_line.emit(line.rstrip())
        self.process.wait()

    def send(self, cmd):
        if self.process and self.process.poll() is None:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()

    def stop(self):
        self.send("exit")


class DITGSequence(QThread):
    """Runs the ITGRecv → ITGSend (all senders) → ITGDec sequence off the main thread.
    All UI updates go through signals so Qt stays happy."""
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, runner, senders, dst_mn, dst_ip, proto, size, pps, dur_s, log_dir):
        super().__init__()
        self.runner = runner
        self.senders = senders # list of mn host names, excluding dst
        self.dst_mn = dst_mn
        self.dst_ip = dst_ip
        self.proto = proto
        self.size = size
        self.pps = pps
        self.dur_s = dur_s
        self.log_dir = log_dir

    def run(self):
        dur_ms = self.dur_s * 1000
        recv_log = f"{self.log_dir}/recv_{self.dst_mn}.log"

        os.makedirs(self.log_dir, exist_ok=True)

        self.log.emit(f"[D-ITG] Starting receiver on {self.dst_mn}...")
        self.runner.send(f"{self.dst_mn} ITGRecv -l {recv_log} &")

        time.sleep(1)

        self.log.emit(f"[D-ITG] Starting {len(self.senders)} senders → {self.dst_mn} ({self.dur_s}s)...")
        for src_mn in self.senders:
            send_log = f"{self.log_dir}/send_{src_mn}.log"
            send_cmd = (
                f"{src_mn} ITGSend -a {self.dst_ip} -T {self.proto}"
                f" -c {self.size} -C {self.pps} -t {dur_ms} -l {send_log} &"
            )
            self.runner.send(send_cmd)

        time.sleep(self.dur_s + 2)

        self.log.emit("[D-ITG] Stopping receiver...")
        self.runner.send(f"{self.dst_mn} killall ITGRecv 2>/dev/null")
        time.sleep(1)

        self._decode_logs()
        self.finished.emit()

    def _decode_logs(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = os.path.join(self.log_dir, timestamp)
        os.makedirs(output_dir, exist_ok=True)

        self.log.emit("[D-ITG] Decoding logs...")

        recv_log = f"{self.log_dir}/recv_{self.dst_mn}.log"
        with open(os.path.join(output_dir, f"recv_{self.dst_mn}.txt"), "w") as f:
            subprocess.run(["ITGDec", recv_log], stdout=f)

        for src_mn in self.senders:
            send_log = f"{self.log_dir}/send_{src_mn}.log"
            with open(os.path.join(output_dir, f"send_{src_mn}.txt"), "w") as f:
                subprocess.run(["ITGDec", send_log], stdout=f)

        for fname in os.listdir(self.log_dir):
            if fname.endswith(".log"):
                os.remove(os.path.join(self.log_dir, fname))

        self.log.emit(f"[D-ITG] Results saved to {output_dir}")


class App(QWidget):
    def __init__(self, selected_topology=None):
        super().__init__()
        self.setWindowTitle("D-ITG Tracer")
        self.resize(800, 650)
        self.runner = None
        self.seq = None
        self.selected_topology = selected_topology
        self._build_ui()

    def _build_ui(self):
        main = QHBoxLayout()
        self.setLayout(main)

        left = QVBoxLayout()
        left.setSpacing(8)
        main.addLayout(left, 1)

        topo_box = QGroupBox("Topology")
        topo_layout = QVBoxLayout()
        topo_box.setLayout(topo_layout)

        self.topo_combo = QComboBox()
        for name in TOPOLOGIES:
            self.topo_combo.addItem(name)
        self.topo_combo.currentIndexChanged.connect(self._populate_hosts)

        if self.selected_topology:
            if self.selected_topology in TOPOLOGIES:
                self.topo_combo.setCurrentText(self.selected_topology)
            else:
                script_to_find = f"{self.selected_topology}.py"
                for topo_name, topo_data in TOPOLOGIES.items():
                    if topo_data.get("script") == script_to_find:
                        self.topo_combo.setCurrentText(topo_name)
                        break

        btn_row = QHBoxLayout()
        self.launch_btn = QPushButton("Launch")
        self.launch_btn.clicked.connect(self.launch)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.launch_btn)
        btn_row.addWidget(self.stop_btn)
        topo_layout.addLayout(btn_row)
        left.addWidget(topo_box)

        ditg_box = QGroupBox("D-ITG Test")
        form = QFormLayout()
        ditg_box.setLayout(form)

        self.dst_combo = QComboBox()
        form.addRow("Destination (receiver):", self.dst_combo)

        self.proto_combo = QComboBox()
        for p in PROTOCOLS:
            self.proto_combo.addItem(p)
        form.addRow("Protocol:", self.proto_combo)

        self.pkt_size = QSpinBox()
        self.pkt_size.setRange(64, 65535)
        self.pkt_size.setValue(512)
        form.addRow("Packet size (bytes):", self.pkt_size)

        self.pps = QSpinBox()
        self.pps.setRange(1, 100000)
        self.pps.setValue(1000)
        form.addRow("Packets/sec:", self.pps)

        self.duration = QSpinBox()
        self.duration.setRange(1, 3600)
        self.duration.setValue(10)
        form.addRow("Duration (sec):", self.duration)

        left.addWidget(ditg_box)

        preview_box = QGroupBox("Command Preview")
        preview_layout = QVBoxLayout()
        preview_box.setLayout(preview_layout)
        self.preview_lbl = QLabel()
        self.preview_lbl.setWordWrap(True)
        self.preview_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #555;")
        preview_layout.addWidget(self.preview_lbl)
        left.addWidget(preview_box)

        for w in [self.dst_combo, self.proto_combo]:
            w.currentIndexChanged.connect(self._update_preview)
        for w in [self.pkt_size, self.pps, self.duration]:
            w.valueChanged.connect(self._update_preview)

        self.run_btn = QPushButton("Run D-ITG Test")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.run_ditg)
        left.addWidget(self.run_btn)
        left.addStretch()

        right = QVBoxLayout()
        main.addLayout(right, 2)

        right.addWidget(QLabel("Output:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(
            "background: #1e1e1e; color: #d4d4d4;"
            "font-family: monospace; font-size: 12px;"
        )
        right.addWidget(self.output)

        right.addWidget(QLabel("Manual command:"))
        cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("e.g. rH1 ping -c3 rH2")
        self.cmd_input.returnPressed.connect(self.send_cmd)
        self.cmd_input.setEnabled(False)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_cmd)
        self.send_btn.setEnabled(False)
        cmd_row.addWidget(self.cmd_input)
        cmd_row.addWidget(self.send_btn)
        right.addLayout(cmd_row)

        self._populate_hosts()

    def _current_hosts(self):
        return TOPOLOGIES[self.topo_combo.currentText()]["hosts"]

    def _populate_hosts(self):
        hosts = self._current_hosts()
        self.dst_combo.clear()
        for display in hosts:
            self.dst_combo.addItem(display)
        self._update_preview()

    def _get_selected(self):
        hosts = self._current_hosts()
        dst_display = self.dst_combo.currentText()
        dst_mn, dst_ip = hosts[dst_display]
        senders = [mn for display, (mn, _) in hosts.items() if display != dst_display]
        return senders, dst_mn, dst_ip

    def _update_preview(self):
        try:
            senders, dst_mn, dst_ip = self._get_selected()
        except Exception:
            return
        proto = self.proto_combo.currentText()
        size = self.pkt_size.value()
        pps = self.pps.value()
        dur_ms = self.duration.value() * 1000
        recv_log = f"{LOG_DIR}/recv_{dst_mn}.log"
        sender_list = ", ".join(senders)
        self.preview_lbl.setText(
            f"{dst_mn} ITGRecv -l {recv_log} &\n"
            f"[{sender_list}] ITGSend -a {dst_ip} -T {proto} -c {size} -C {pps} -t {dur_ms} -l send_<host>.log &\n"
            f"→ decoded to {LOG_DIR}/<timestamp>/"
        )

    def log(self, text):
        self.output.append(text)
        self.output.ensureCursorVisible()

    def launch(self):
        name = self.topo_combo.currentText()
        script = TOPOLOGIES[name]["script"]
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "ditg_topos", script)

        self.output.clear()
        self.log(f"Launching {name}...\n")

        self.runner = MininetRunner(path)
        self.runner.output_line.connect(self.log)
        self.runner.start()

        self.launch_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.cmd_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.run_btn.setEnabled(True)

    def stop(self):
        if self.runner:
            self.runner.stop()
        self.launch_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.cmd_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.run_btn.setEnabled(False)
        self.log("\n[Stopped]")

    def send_cmd(self):
        cmd = self.cmd_input.text().strip()
        if not cmd or not self.runner:
            return
        self.log(f"\n> {cmd}")
        self.runner.send(cmd)
        self.cmd_input.clear()

    def run_ditg(self):
        if not self.runner:
            return

        senders, dst_mn, dst_ip = self._get_selected()

        self.seq = DITGSequence(
            runner = self.runner,
            senders = senders,
            dst_mn = dst_mn,
            dst_ip = dst_ip,
            proto = self.proto_combo.currentText(),
            size = self.pkt_size.value(),
            pps = self.pps.value(),
            dur_s = self.duration.value(),
            log_dir = LOG_DIR,
        )
        self.seq.log.connect(self.log)
        self.seq.finished.connect(self._on_ditg_finished)
        self.seq.start()

        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")

    def _on_ditg_finished(self):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run D-ITG Test")

    def closeEvent(self, event):
        if self.runner:
            self.runner.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
