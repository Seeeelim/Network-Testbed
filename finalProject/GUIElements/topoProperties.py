from PyQt5.QtWidgets import (
    QGraphicsView, QWidget, QFormLayout, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout, QPushButton
)
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

from GUIElements.node import Node
from GUIElements.link import Link


class TopoWindow(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)

        self.scene = scene

    def add_node(self, node_object):
        self.scene.addItem(node_object)

    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in

        current_scale = self.transform().m11()

        min_scale = 0.65
        max_scale = 5.0

        if event.angleDelta().y() > 0:
            if current_scale < max_scale:
                self.scale(zoom_in, zoom_in)
        else:
            if current_scale > min_scale:
                self.scale(zoom_out, zoom_out)


class Properties(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)

        root = QVBoxLayout(self)
        header = QHBoxLayout()

        self.title = QLabel("Properties")
        self.title.setStyleSheet("font-weight: bold;")

        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(30, 30)

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.close_btn)

        self.form = QFormLayout()
        root.addLayout(header)
        root.addLayout(self.form)
        root.addStretch()

        self.traffic_btn = QPushButton("Open Traffic GUI")
        self.traffic_btn.setEnabled(False)
        self.traffic_btn.setFixedHeight(40)
        self.traffic_btn.setStyleSheet("font-weight: bold; font-size: 16px;")

        self.run_btn = QPushButton("Open Attack GUI")
        self.run_btn.setEnabled(False)
        self.run_btn.setFixedHeight(40)
        self.run_btn.setStyleSheet("font-weight: bold; font-size: 16px;")

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setEnabled(False)
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.setStyleSheet("font-weight: bold; font-size: 16px;")

        self.load_topo_button = QPushButton("Load Topology")
        self.load_topo_button.setFixedHeight(40)
        self.load_topo_button.setStyleSheet("font-weight: bold; font-size: 16px;")

        root.addWidget(self.traffic_btn)
        root.addWidget(self.run_btn)
        root.addWidget(self.apply_btn)
        root.addWidget(self.load_topo_button)

        self.show_empty()

    def on_field_changed(self):
        for field, line_edit in self.modifiable_fields.items():
            original = str(self.item.properties.get(field, ""))
            if line_edit.text() != original:
                self.apply_btn.setEnabled(True)
                return
        self.apply_btn.setEnabled(False)

    def clear_form(self):
        while self.form.count():
            item = self.form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def show_empty(self):
        self.clear_form()

    def show_for_item(self, item):
        self.clear_form()

        self.item = item
        self.modifiable_fields = {}

        if isinstance(item, Node):
            if item.type == "host":
                self.title.setText("Host Properties")
                self.form.addRow("Name:", QLabel(item.node_name))
                self.form.addRow("IP:", QLabel(item.properties.get("IP", "N/A")))
                self.form.addRow("Default Gateway:", QLabel(item.properties.get("DefaultRoute", "N/A")))

            elif item.type == "switch":
                self.title.setText("Switch Properties")
                self.form.addRow("Description:", QLabel(item.properties.get("Description", "N/A")))

            elif item.type == "router":
                self.title.setText("Router Properties")
                self.form.addRow("IP:", QLabel(item.properties.get("IP", "N/A")))
                for interface, ip in item.properties.get("Interfaces", {}).items():
                    self.form.addRow(f"Interface {interface}:", QLabel(ip))

        elif isinstance(item, Link):
            self.title.setText("Link Properties")

            self.form.addRow("Endpoint A:", QLabel(item.node_1.node_name))
            self.form.addRow("Endpoint B:", QLabel(item.node_2.node_name))
            self.form.addRow("Segment:", QLabel(item.segment))

            for field in ["Bandwidth", "Delay", "Jitter", "Loss"]:
                line_edit = QLineEdit(str(item.properties.get(field, "N/A")))
                line_edit.textChanged.connect(self.on_field_changed)
                self.modifiable_fields[field] = line_edit
                label = f"{field} (Mbps):" if field == "Bandwidth" else f"{field}:"
                self.form.addRow(label, line_edit)

        else:
            self.show_empty()