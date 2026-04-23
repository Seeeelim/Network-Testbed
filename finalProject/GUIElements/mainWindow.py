from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QWidget, QHBoxLayout,
    QFileDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import json, subprocess
from pathlib import Path

from GUIElements.node import Node
from GUIElements.link import Link
from GUIElements.topoProperties import TopoWindow, Properties
from GUIElements import attackGUI
from GUIElements import trafficGUI


TOPO_JSONS_DIR = "./topo_jsons/"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Test Bed Application")
        self.setWindowIcon(QIcon("./assets/switch.png"))

        # Main canvas for rendering the topology graph
        self.scene = QGraphicsScene()
        self.view = TopoWindow(self.scene)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view, stretch=4)

        # Side panel for node/link properties and action buttons
        self.props = Properties()
        layout.addWidget(self.props, stretch=1)

        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.props.close_btn.clicked.connect(self.clear_properties)
        self.props.apply_btn.clicked.connect(self.apply_modifications)
        self.props.load_topo_button.clicked.connect(self.open_file_dialog)
        self.props.run_btn.clicked.connect(self.run_topo)
        self.props.traffic_btn.clicked.connect(self.open_traffic_gui)

        self.setCentralWidget(container)

        # Stores all rendered nodes and links keyed by name
        self.nodes: dict[str, Node] = {}
        self.links: dict[str, Link] = {}

        # current_topo holds the loaded JSON in memory (may include user edits)
        # current_runner_topo is the path to the matching Mininet .py script
        self.current_topo = None
        self.current_runner_topo = None

        # ditg_server is read from the topology JSON and passed to AttackDialog
        # to lock the receiver field and exclude it from attacker selection
        self.ditg_server = None
        self.traffic_window = None

    def apply_modifications(self):
        """Apply user edits from the properties panel back to the in-memory topology.
 
        Link property changes are propagated to all links sharing the same segment
        (e.g. editing one rwan link updates all rwan links). The updated topology
        is then written to modified_topology.json for reference.
        """
        item = self.props.item
        for k, v in self.props.modifiable_fields.items():
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
        """Serialize the current in-memory topology (nodes + links) to modified_topology.json.
 
        This file is not used by the simulation directly — it serves as a snapshot
        of any user edits made through the properties panel.
        """
        new_json = {"nodes": [], "links": []}

        for node in self.nodes.values():
            new_json["nodes"].append({
                "id": node.node_name,
                "type": node.type,
                "x": int(node.pos().x()),
                "y": int(node.pos().y()),
                "properties": node.properties
            })

        for link in self.links.values():
            new_json["links"].append({
                "src": link.node_1.node_name,
                "dst": link.node_2.node_name,
                "segment": link.segment,
                "properties": link.properties
            })

        with open("./modified_topology.json", "w") as json_file:
            json.dump(new_json, json_file, indent=4)

        self.current_topo = new_json

    def run_topo(self):
        """Launch the attack simulation.
 
        Flow:
        1. Open AttackDialog to collect simulation parameters
        2. Write the config to /tmp/attack_config.json — the topology script
           reads this file when it starts to configure TrafficGenerator
        3. Build CLI args from the current link properties so the topology
           script uses whatever values are currently set in the GUI
        4. Spawn a gnome-terminal running the topology script as sudo
        """
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

        for segment, properties in segments.items():
            args += [
                f"--{segment}-bw", str(properties["Bandwidth"] / 1000),
                f"--{segment}-delay", properties["Delay"],
                f"--{segment}-jitter", properties["Jitter"],
                f"--{segment}-loss", str(properties["Loss"])
            ]

        subprocess.Popen([
            "gnome-terminal", "--",
            "bash", "-c",
            "sudo python3 " + self.current_runner_topo + " " + " ".join(args) + "; read"
        ])

    def open_traffic_gui(self):
        """Open the standalone D-ITG traffic test window.
 
        Passes the current topology name so the Traffic GUI can pre-select
        the matching topology in its dropdown.
        """
        topology_name = None
        if self.current_runner_topo:
            topology_name = Path(self.current_runner_topo).stem

        self.traffic_window = trafficGUI.App(selected_topology=topology_name)
        self.traffic_window.show()

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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open JSON Topology", TOPO_JSONS_DIR, "JSON Files (*.json)"
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
        """Clear the canvas and render a topology from a JSON object.
 
        Nodes must be created before links since links hold references
        to node objects. ditg_server is read from the JSON root and used
        to configure the AttackDialog when a simulation is launched.
        """
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
        self.props.traffic_btn.setEnabled(True)