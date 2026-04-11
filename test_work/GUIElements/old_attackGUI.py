import sys, os, time, subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QLineEdit,
    QComboBox, QSpinBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal


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
    """Runs the ITGRecv → ITGSend → ITGDec sequence off the main thread.
    All UI updates go through signals so Qt stays happy."""
    log       = pyqtSignal(str)
    finished  = pyqtSignal()

    def __init__(self, runner, src_mn, dst_mn, dst_ip, proto, size, pps, dur_s):
        super().__init__()
        self.runner = runner
        self.src_mn = src_mn
        self.dst_mn = dst_mn
        self.dst_ip = dst_ip
        self.proto  = proto
        self.size   = size
        self.pps    = pps
        self.dur_s  = dur_s

    def run(self):
        dur_ms = self.dur_s * 1000

        recv_cmd = f"{self.dst_mn} ITGRecv -l /tmp/ditg_recv.dat &"
        send_cmd = (f"{self.src_mn} ITGSend -a {self.dst_ip} -T {self.proto}"
                    f" -c {self.size} -C {self.pps} -t {dur_ms}")
        dec_cmd  = f"{self.dst_mn} ITGDec /tmp/ditg_recv.dat"

        self.log.emit(f"[D-ITG] Starting receiver on {self.dst_mn}...")
        self.runner.send(recv_cmd)

        time.sleep(1)

        self.log.emit(f"[D-ITG] Sending {self.src_mn} → {self.dst_mn} ({self.dur_s}s)...")
        self.runner.send(send_cmd)

        time.sleep(self.dur_s + 2)

        self.log.emit("[D-ITG] Stopping receiver and decoding...")
        self.runner.send(f"{self.dst_mn} killall ITGRecv 2>/dev/null")
        time.sleep(1)
        self.runner.send(dec_cmd)

        time.sleep(2)
        self.log.emit("[D-ITG] Done.")
        self.finished.emit()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("D-ITG Tracer")
        self.resize(800, 650)
        self.runner  = None
        self.seq     = None
        self._build_ui()

    def _build_ui(self):
        main = QHBoxLayout()
        self.setLayout(main)

        # ── Left column ───────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)
        main.addLayout(left, 1)

        # Topology group
        topo_box = QGroupBox("Topology")
        topo_layout = QVBoxLayout()
        topo_box.setLayout(topo_layout)

        self.topo_combo = QComboBox()
        for name in TOPOLOGIES:
            self.topo_combo.addItem(name)
        self.topo_combo.currentIndexChanged.connect(self._populate_hosts)
        topo_layout.addWidget(self.topo_combo)

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

        # D-ITG form group
        ditg_box = QGroupBox("D-ITG Test")
        form = QFormLayout()
        ditg_box.setLayout(form)

        self.src_combo = QComboBox()
        self.dst_combo = QComboBox()
        form.addRow("Source:", self.src_combo)
        form.addRow("Destination:", self.dst_combo)

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

        # Command preview
        preview_box = QGroupBox("Command Preview")
        preview_layout = QVBoxLayout()
        preview_box.setLayout(preview_layout)
        self.preview_lbl = QLabel()
        self.preview_lbl.setWordWrap(True)
        self.preview_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #555;")
        preview_layout.addWidget(self.preview_lbl)
        left.addWidget(preview_box)

        for w in [self.src_combo, self.dst_combo, self.proto_combo]:
            w.currentIndexChanged.connect(self._update_preview)
        for w in [self.pkt_size, self.pps, self.duration]:
            w.valueChanged.connect(self._update_preview)

        self.run_btn = QPushButton("Run D-ITG Test")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.run_ditg)
        left.addWidget(self.run_btn)
        left.addStretch()

        # ── Right column ──────────────────────
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
        self.cmd_input.setPlaceholderText("e.g.  rH1 ping -c3 rH2")
        self.cmd_input.returnPressed.connect(self.send_cmd)
        self.cmd_input.setEnabled(False)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_cmd)
        self.send_btn.setEnabled(False)
        cmd_row.addWidget(self.cmd_input)
        cmd_row.addWidget(self.send_btn)
        right.addLayout(cmd_row)

        self._populate_hosts()

    # ── Helpers ───────────────────────────────
    def _current_hosts(self):
        return TOPOLOGIES[self.topo_combo.currentText()]["hosts"]

    def _populate_hosts(self):
        hosts = self._current_hosts()
        self.src_combo.clear()
        self.dst_combo.clear()
        for display in hosts:
            self.src_combo.addItem(display)
            self.dst_combo.addItem(display)
        if self.dst_combo.count() > 1:
            self.dst_combo.setCurrentIndex(1)
        self._update_preview()

    def _get_selected(self):
        hosts = self._current_hosts()
        src_mn, src_ip = hosts[self.src_combo.currentText()]
        dst_mn, dst_ip = hosts[self.dst_combo.currentText()]
        return src_mn, src_ip, dst_mn, dst_ip

    def _update_preview(self):
        try:
            src_mn, _, dst_mn, dst_ip = self._get_selected()
        except Exception:
            return
        proto  = self.proto_combo.currentText()
        size   = self.pkt_size.value()
        pps    = self.pps.value()
        dur_ms = self.duration.value() * 1000
        self.preview_lbl.setText(
            f"{dst_mn} ITGRecv -l /tmp/ditg_recv.dat &\n"
            f"{src_mn} ITGSend -a {dst_ip} -T {proto} -c {size} -C {pps} -t {dur_ms}\n"
            f"{dst_mn} ITGDec /tmp/ditg_recv.dat"
        )

    def log(self, text):
        self.output.append(text)
        self.output.ensureCursorVisible()

    # ── Actions ───────────────────────────────
    def launch(self):
        name   = self.topo_combo.currentText()
        script = TOPOLOGIES[name]["script"]
        base   = os.path.dirname(os.path.abspath(__file__))
        path   = os.path.join(base, script)

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

        src_mn, _, dst_mn, dst_ip = self._get_selected()

        self.seq = DITGSequence(
            runner = self.runner,
            src_mn = src_mn,
            dst_mn = dst_mn,
            dst_ip = dst_ip,
            proto  = self.proto_combo.currentText(),
            size   = self.pkt_size.value(),
            pps    = self.pps.value(),
            dur_s  = self.duration.value(),
        )
        # All signals connected to main thread slots — no direct UI calls from thread
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
