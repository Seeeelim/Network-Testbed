from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QLineF


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