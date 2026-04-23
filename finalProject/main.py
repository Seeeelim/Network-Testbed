#!/usr/bin/env python3

import sys
from GUIElements.mainWindow import MainWindow
from PyQt5.QtWidgets import QApplication


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()

    window = MainWindow()
    window.resize(int(size.width() * 0.75), int(size.height() * 0.75))
    window.show()

    sys.exit(app.exec_())