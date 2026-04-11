from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QComboBox
)

import json

from pathlib import Path


class AttackDialog(QDialog):
    def __init__(self, nodes, ditg_server, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attack Config")
        self.setModal(True)
        self.setFixedWidth(420)

        self.attack_script = None
        self.ditg_server = ditg_server
        self.defaults = self.load_defaults()

        host_names = []
        for name, node in nodes.items():
            if node.type == "host":
                host_names.append(name)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        attack_script_row = QHBoxLayout()
        self.attack_script_label = QLabel("No script selected")
        self.attack_script_label.setWordWrap(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.pick_script)
        attack_script_row.addWidget(self.attack_script_label, stretch=1)
        attack_script_row.addWidget(browse_btn)

        self.attacker_combo = QComboBox()
        self.attacker_combo.addItems(host_names)

        self.target_combo = QComboBox()
        self.target_combo.addItem("")
        self.target_combo.addItems(host_names)

        self.protocol_edit = QLineEdit(str(self.defaults.get("protocol", "TCP")))

        self.packet_size_edit = QLineEdit(str(self.defaults.get("packet_size", 512)))

        self.rate_edit = QLineEdit(str(self.defaults.get("rate", 1000)))

        self.baseline_edit = QLineEdit(str(self.defaults.get("baseline_seconds", 10)))

        self.duration_edit = QLineEdit(str(self.defaults.get("duration", 30)))

        self.runs_edit = QLineEdit(str(self.defaults.get("runs", 1)))

        form.addRow("Attack Script:", attack_script_row)
        form.addRow("Attacker:", self.attacker_combo)
        form.addRow("Target:", self.target_combo)
        form.addRow("Protocol:", self.protocol_edit)
        form.addRow("Packet Size (bytes):", self.packet_size_edit)
        form.addRow("Rate (pps):", self.rate_edit)
        form.addRow("Baseline (sec):", self.baseline_edit)
        form.addRow("Attack Duration (sec):", self.duration_edit)
        form.addRow("Runs:", self.runs_edit)

        layout.addLayout(form)


        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.launch_btn = QPushButton("Launch Simulation")

        self.launch_btn.setDefault(True)
        self.launch_btn.setEnabled(False)

        self.cancel_btn.clicked.connect(self.reject)
        self.launch_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.launch_btn)

        layout.addLayout(btn_row)

        self.target_combo.currentIndexChanged.connect(self.validate)

    def load_defaults(self):
        with open("./attackGUIConfigs.json", "r") as f:
            return json.load(f)

    def pick_script(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Attack Script", "./attacks/", "Python Files (*.py)"
        )
        if path:
            self.attack_script = path
            self.attack_script_label.setText(Path(path).name)
            self.attack_script_label.setStyleSheet("")
            self.validate()

    def validate(self):
        if self.attack_script is None:
            self.launch_btn.setEnabled(False)
            return
        if self.target_combo.currentText() == "":
            self.launch_btn.setEnabled(False)
            return
        self.launch_btn.setEnabled(True)

    def get_config(self):
        return {
            "attack_script": self.attack_script,
            "attacker": self.attacker_combo.currentText(),
            "target": self.target_combo.currentText(),
            "receiver": self.ditg_server,
            "protocol": self.protocol_edit.text(),
            "packet_size": int(self.packet_size_edit.text()),
            "rate": int(self.rate_edit.text()),
            "baseline_seconds": int(self.baseline_edit.text()),
            "duration": int(self.duration_edit.text()),
            "runs": int(self.runs_edit.text())
        }