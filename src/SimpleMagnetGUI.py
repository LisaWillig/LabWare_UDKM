import sys
from PyQt5 import QtGui, uic
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np

Parameters = {'Voltage': 0}


class MyWindow(PyQt5.QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        self.ui = uic.loadUi('GUI\\GroßerMagnet_SimpleMeasurement.ui', self)
        self.btn_start.clicked.connect(self.Main)
        self.Main()
        self.show()

    def Main(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def vector(self):
        vec = np.linspace(0, 10, 10)
        return vec

    def update(self):
        vect = self.vector()
        for i in vect:
            print('Hello')
        self.timer.stop()


def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()




