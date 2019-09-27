import os

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

from dispertech.view import VIEW_BASE_DIR


class FocusingWindow(QMainWindow):
    def __init__(self):
        super(FocusingWindow, self).__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Focusing_Window.ui'), self)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    win = FocusingWindow()
    win.show()
    app.exec()
