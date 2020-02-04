import pyqtgraph as pg

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget


class FiberEndAnalysisWindow(pg.ImageView):
    def __init__(self, trace_size=80):
        view = pg.PlotItem()
        self.trace_size = trace_size
        pg.ImageView.__init__(self, view=view)
        self.cs_layout = pg.GraphicsLayout()
        self.cs_layout.addItem(view, row=1, col=0)
        self.ui.graphicsView.setCentralItem(self.cs_layout)
        self.cross_section_enabled = False


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    win = FiberEndAnalysisWindow()
    win.show()
    app.exec()
