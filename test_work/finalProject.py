from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem, QGraphicsPixmapItem,QWidget,
    QFormLayout, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout,
    QPushButton, QFileDialog, QGraphicsTextItem
)
from PyQt5.QtGui import (
    QPainter, QPen, QPixmap, QIcon
)
from PyQt5.QtCore import Qt, QSize, QLineF

import sys, json, subprocess

from pathlib import Path

from GUIElements import attackGUI


TOPO_JSONS_DIR = "./topo_jsons/"


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


class Node(QGraphicsPixmapItem):
    def __init__(self, type: str, node_name: str, image: str, x: int, y: int, 
                 properties: dict, image_size: int=64):
        # create exception
        node_picture = QPixmap(f"./assets/{image}.png")
        node_picture = node_picture.scaled(
            QSize(image_size, image_size),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        super().__init__(node_picture)

        self.type = type
        
        self.node_name = node_name
        
        self.setPos(x, y)
        
        self.properties = properties
        
        self.setFlag(self.ItemIsSelectable, True)
        
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)

        self._edges = []

        self.label = QGraphicsTextItem(node_name, self)
        label_x = (image_size - self.label.boundingRect().width()) / 2
        self.label.setPos(label_x, image_size + 2)

    def add_edge(self, edge):
        self._edges.append(edge)
        

class Link(QGraphicsLineItem):
    def __init__(self, node_1, node_2, segment: str, properties: dict):
        super().__init__()
        self.node_1 = node_1
        self.node_2 = node_2
        self.segment = segment
        self.properties = properties

        self.setPen(QPen(Qt.black, 2))
        self.setZValue(-1)
        
        self.setFlag(self.ItemIsSelectable, True)
        
        self.update_line()

    def update_line(self):
        center_1 = self.node_1.mapToScene(self.node_1.boundingRect().center())
        center_2 = self.node_2.mapToScene(self.node_2.boundingRect().center())

        self.setLine(QLineF(center_1, center_2))


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

        self.run_btn = QPushButton("Run")
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

                name = QLabel(item.node_name)
                ip = QLabel(item.properties.get("IP", "N/A"))
                default_gateway = QLabel(item.properties.get("DefaultRoute", "N/A"))

                self.form.addRow("Name:", name)
                self.form.addRow("IP:", ip)
                self.form.addRow("Default Gateway:", default_gateway)
            elif item.type == "switch":
                self.title.setText("Switch Properties")

                description = QLabel(item.properties.get("Description", "N/A"))

                self.form.addRow("Description:", description)
            elif item.type == "router":
                self.title.setText("Router Properties")

                ip = QLabel(item.properties.get("IP", "N/A"))
                self.form.addRow("IP:", ip)

                interfaces = item.properties.get("Interfaces", [])
                for interface, ip in interfaces.items():
                    self.form.addRow(f"Interface {interface}:", QLabel(ip))

        elif isinstance(item, Link):
            self.title.setText("Link Properties")
            modifiable_fields = ["Bandwidth", "Delay", "Jitter", "Loss"]

            a = QLabel(item.node_1.node_name)
            b = QLabel(item.node_2.node_name)
            segment = QLabel(item.segment)

            self.form.addRow("Endpoint A:", a)
            self.form.addRow("Endpoint B:", b)
            self.form.addRow("Segment:", segment)

            for field in modifiable_fields:
                line_edit = QLineEdit(str(item.properties.get(field, "N/A")))
                line_edit.textChanged.connect(self.on_field_changed)
                self.modifiable_fields[field] = line_edit
                if field == "Bandwidth":
                    self.form.addRow(f"{field} (Mbps):", line_edit)
                else:
                    self.form.addRow(f"{field}:", line_edit)
        else:
            self.show_empty()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Test Bed Application")
        self.setWindowIcon(QIcon("./assets/switch.png"))

        self.scene = QGraphicsScene()
        self.view = TopoWindow(self.scene)
        container = QWidget()
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.view, stretch=4)
        self.props = Properties()
        layout.addWidget(self.props, stretch=1)
        
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.props.close_btn.clicked.connect(self.clear_properties)
        self.props.apply_btn.clicked.connect(self.apply_modifications)
        self.props.load_topo_button.clicked.connect(self.open_file_dialog)
        self.props.run_btn.clicked.connect(self.run_topo)
        
        self.setCentralWidget(container)

        self.nodes: dict[str, Node] = {}
        self.links: dict[str, Link] = {}
        
        self.current_topo = None
        self.current_runner_topo = None

        self.ditg_server = None

    def apply_modifications(self):
        item = self.props.item
        for k, v in self.props.modifiable_fields.items():
            # hardcoded, fix later
            if k == "Loss":
                item.properties[k] = float(v.text())
            elif k == "Bandwidth":
                item.properties[k] = int(v.text())
            else:
                item.properties[k] = v.text()
                
        if isinstance(item, Link):
            for link in self.links.values():
                if link.segment == item.segment:
                    link.properties.update(item.properties)
                
        self.props.apply_btn.setEnabled(False)
        self.modify_json()

    def modify_json(self):
        new_json = {
            "nodes":[],
            "links":[]
        }
        for node in self.nodes.values():
            node_json = {
                "id": node.node_name,
                "type": node.type,
                "x": int(node.pos().x()),
                "y": int(node.pos().y()),
                "properties": node.properties
            }
            new_json["nodes"].append(node_json)
        for link in self.links.values():
            link_json = {
                "src": link.node_1.node_name,
                "dst": link.node_2.node_name,
                "segment": link.segment,"properties": link.properties
            }
            new_json["links"].append(link_json)

        with open("./modified_topology.json", "w") as json_file:
            json.dump(new_json, json_file, indent=4)

        self.current_topo = new_json

    def run_topo(self):
        setup_attack = attackGUI.AttackDialog(self.nodes, self.ditg_server, parent=self)

        if setup_attack.exec_() != attackGUI.QDialog.Accepted:
            return

        attack_config = setup_attack.get_config()

        with open("./attack_config.json", "w") as config_file:
            json.dump(attack_config, config_file, indent=4)

        segments = {}
        args = []

        for link in self.current_topo.get("links", []):
            segment = link.get("segment", "")
            if segment and segment not in segments:
                segments[segment] = []
            if segment:
                segments[segment] = link["properties"]

        for segment, property in segments.items():
            args += [
            f"--{segment}-bw",     str(property["Bandwidth"] / 1000),
            f"--{segment}-delay",  property["Delay"],
            f"--{segment}-jitter", property["Jitter"],
            f"--{segment}-loss",   str(property["Loss"])
        ]
            
        subprocess.Popen([
            "gnome-terminal", "--",
            "bash", "-c",
            "sudo python3 " + self.current_runner_topo + " " + " ".join(args) + "; read"
        ])

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            self.props.show_empty()
            return
        self.props.show_for_item(items[-1])

    def clear_properties(self):
        self.scene.clearSelection()
        self.props.show_empty()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self,
                                                   "Open JSON Topology",
                                                   TOPO_JSONS_DIR,
                                                   "JSON Files (*.json)"
                                                   )
        if not file_path:
            return
        self.file_to_json(file_path)

    def file_to_json(self, file_path):
        with open(file_path, "r") as topo_file:
            topo_json = json.load(topo_file)
        
        self.current_runner_topo = "./topos/" + Path(file_path).stem + ".py"

        self.load_topology(topo_json)
    
    def create_node(self, node_json):
        node = Node(
            type=node_json["type"],
            node_name=node_json["id"],
            image=node_json["type"],
            x=int(node_json["x"]),
            y=int(node_json["y"]),
            properties=node_json.get("properties", {})
        )
        self.nodes[node_json["id"]] = node
        self.view.add_node(node)

    def create_link(self, link_json):
        link = Link(
            node_1=self.nodes.get(link_json["src"]),
            node_2=self.nodes.get(link_json["dst"]),
            segment=link_json.get("segment", ""),
            properties=link_json.get("properties", {})
        )
        self.links[f"{link_json['src']}-{link_json['dst']}"] = link
        self.view.scene.addItem(link)

    def load_topology(self, topo_json):
        # nodes before links (links reference nodes)
        self.scene.clear()

        self.nodes = {}
        self.links = {}
        
        for node_json in topo_json.get("nodes", []):
            self.create_node(node_json)

        for link_json in topo_json.get("links", []):
            self.create_link(link_json)

        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

        self.current_topo = topo_json

        self.ditg_server = topo_json.get("ditg_server")

        self.props.run_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()

    window = MainWindow()
    window.resize(int(size.width() * 0.75), int(size.height() * 0.75))
    window.show()
    
    sys.exit(app.exec_())