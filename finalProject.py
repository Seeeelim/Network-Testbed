from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem, QGraphicsPixmapItem,QWidget,
    QFormLayout, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout,
    QPushButton
)
from PyQt5.QtGui import (
    QPainter, QPen, QPixmap, QIcon, QBrush, QPainterPath,
    QPainterPathStroker
)
from PyQt5.QtCore import QRectF, Qt, QSize, pyqtSignal, QLineF

import sys


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
    def __init__(self, node_name: str, image: str, x: int, y: int, 
                 properties: dict, image_size: int=64):
        try:
            node_picture = QPixmap(f"./assets/{image}.png")
            if node_picture.isNull():
                raise FileNotFoundError(f"./assets/{image}.png not found or invalid image")
            node_picture = node_picture.scaled(
                QSize(image_size, image_size),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        except Exception as e:
            print(f"Error loading image for node '{node_name}': {e}")
            QApplication.instance().quit()
            sys.exit(1)

        super().__init__(node_picture)
        
        self.node_name = node_name
        
        self.setPos(x, y)
        
        self.properties = properties
        
        self.setFlag(self.ItemIsSelectable, True)
        
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)

        self._edges = []

    def add_edge(self, edge):
        self._edges.append(edge)
        

class Links(QGraphicsLineItem):
    def __init__(self, node_1, node_2):
        super().__init__()
        self.node_1 = node_1
        self.node_2 = node_2

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

        self.show_empty()

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

        if isinstance(item, Node):
            self.title.setText("Node Properties")

            name = QLabel(item.node_name)
            
            ip = QLineEdit(item.properties.get("IP", "N/A"))
            mac = QLineEdit(item.properties.get("MAC", "N/A"))
            status = QLineEdit(item.properties.get("Status", "N/A"))

            self.form.addRow("Name:", name)
            self.form.addRow("IP:", ip)
            self.form.addRow("MAC Address:", mac)
            self.form.addRow("Status:", status)

        elif isinstance(item, Links):
            self.title.setText("Link Properties")

            a = QLabel(item.node_1.node_name)
            b = QLabel(item.node_2.node_name)
            
            self.form.addRow("Endpoint A:", a)
            self.form.addRow("Endpoint B:", b)

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
        
        self.setCentralWidget(container)

        self.scene.setSceneRect(QRectF(-400, -300, 1200, 800))
        
        # figure a way to load this from a file or something
        test_properties = {"IP": "192.168.2.2", "MAC": "00:1A:2B:3C:4D:5E", "Status": "Active"}
        
        n1 = Node("s1", "switch", 100, 100, test_properties)
        n2 = Node("h1", "host", 300, 100, test_properties)
        n3 = Node("r1", "router", 200, 300, test_properties)

        self.view.add_node(n1)
        self.view.add_node(n2)
        self.view.add_node(n3)

        self.scene.addItem(Links(n1, n2))
        self.scene.addItem(Links(n2, n3))
        
    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            self.props.show_empty()
            return
        self.props.show_for_item(items[-1])

    def clear_properties(self):
        self.scene.clearSelection()
        self.props.show_empty()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()

    window = MainWindow()
    window.resize(int(size.width() * 0.75), int(size.height() * 0.75))
    window.show()

    # Here goes code for CLI connection
    
    sys.exit(app.exec_())