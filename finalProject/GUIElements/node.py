from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize


class Node(QGraphicsPixmapItem):
    def __init__(self, type: str, node_name: str, image: str, x: int, y: int,
                 properties: dict, image_size: int = 64):
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