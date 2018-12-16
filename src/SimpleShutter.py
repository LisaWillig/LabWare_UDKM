#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SimpleShutter.py

Author: Lisa Willig
Last Edited: 30.11.2018

Python Version: 3.6.5
PyQt Version: 5.9.2

Simple Program to open and close a shutter with the Meilhaus MeasurementCard.
"""

# General Imports
import sys
import PyQt5
from PyQt5 import QtGui, uic
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore

# Imports of own modules
from modules.MERedLab_Communication import MECard


class MyWindow(PyQt5.QtWidgets.QMainWindow):
    """
    GUI class.
    Simple Push Button.
    Label changes when state of Push Button changes.

    A motorized Shutter controlled with Meilhaus MEasureemnt Card opens and
    closes.
    Initialize Class variables.
    """

    Shutter = None
    timer = None

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        self.ui = uic.loadUi('GUI/ShutterSimple.ui', self)

        self.Shutter = MECard()
        self.btn_shutter.toggled.connect(self.shutterState)

        self.Main()
        self.show()

    def shutterState(self):
        """
        Handles the Shutter State as well as text on the button
        1 : circuit open, shutter closed
        0 : circuit closed, shutter open
        """

        if self.ui.btn_shutter.isChecked():
            ans = self.Shutter.setDigValue(1)
            if ans:
                print('Error! Problem with shutter!')
            self.ui.btn_shutter.setText("Closed")

        else:
            ans = self.Shutter.setDigValue(0)
            if ans:
                print('Error! Problem with shutter!')
            self.ui.btn_shutter.setText("Open")

    def Main(self):
        """
        Start the main Update Loop with the QtTimer updating each 10ms.
        """

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)

    def update(self):
        """
        Check for Button Activity
        """

        QtGui.QApplication.processEvents()


def main():
    """
    main entry point. Start and Stopp application and call application.
    """

    app = QApplication(sys.argv)
    MyWindow()
    sys.exit(app.exec_())

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()
