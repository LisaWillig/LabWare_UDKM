#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OceanOpticsUI.py

Author: Felix Stete, Lisa Willig
Last Edited: 16.12.2018

Python Version: 3.6.5
pyqtgraph Version: 0.10.0
OceanOptics Spectrometer

Simple UI to display a spectrum from a OceanOptics 
Spectrometer.

"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import sys
from PyQt5 import uic
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import pyqtgraph as pg
import numpy as np

from mosules.OceanOpticsCommunication_V1 import OOSpectrometer as Spectrometer

        
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Class Spectrometer UI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MyWindow(QMainWindow):
        
    def __init__(self, parent=None):  
        """
        Initialize Spectrometer and load GUI
        """

        super(MyWindow, self).__init__(parent)
        self.ui=uic.loadUi('GUI\\OceanOpticsGUI.ui', self)
        
        # initialize Spectrometer
        self.Spectro = Spectrometer()
        self.Spectro.connectSpectrometer()
        
        # connect Buttons to action
        self.btnClose.clicked.connect(self.close)
        self.btnEvent.clicked.connect(self.Event)
        
        # set default Int time
        self.lineIntTime.setText('10000')
        self.lineIntTime.returnPressed.connect(self.setIntTime)

        self.Main()
        self.show()
        
    def Event(self):
        """
        Function for collectiong Spectrum when Button is pressed
        """
        
        self.z=self.Spectro.getSpectrum()
        self.curve.setData(self.Spectro.getWave(),self.z)

    def closeEvent(self, event):
        """
        Defines the exiting procedure: saving started measurements and
        closing open hardware connections

        :param event: close ("X" of Window or Stop Button)
        :return: Messagebox "Do you want to quit?"
        """       

        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:                        
                        self.Spectro.closeSpectrometer()
                        print('closing')                        
                        event.accept()
        else:
            event.ignore()

    def Main(self):
        """
        Main Entry Point of measurement procedure.
        preparing GUI plots (clear them and apply settings)
        Start main Update Loop for application
        """

        self.graphicsView.clear()
        self.curve = self.graphicsView.getPlotItem().plot(pen='r')
        
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        
    def setIntTime(self):
        """
        Set the Integration time from UI entry when enter is pressed
        """

        IntTime = self.lineIntTime.text()
        self.Spectro.spec.integration_time_micros(int(IntTime))

            
    def update(self):
        """
        Update Loop for application.
        Get Spectrometer Spectrum
        """
        
        self.z=self.Spectro.getSpectrum()
        self.curve.setData(self.Spectro.getWave(),self.z)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #        
def main():
    app = QApplication(sys.argv)
    window=MyWindow()
    sys.exit(app.exec_())
    
"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()