#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SimpleSetFluenz.py

Author: Lisa Willig
Last Edited: 30.11.2018

Python Version: 3.6.5
PyQt Version: 5.9.2

Programm to control the motorized lamda - half waveplate to adjust the fluence
by turning the polarization of the pump beam
"""

# General Imports
import sys
import time as t
import PyQt5
from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import QApplication, QMessageBox
from pyqtgraph.Qt import QtCore
import numpy as np

# Imports of own modules
from calculateFluence import Fluence
from MERedLab_Communication import MECard
from NI_CardCommunication_V2 import NI_CardCommunication
from StageCommunication_V2 import StageCommunication
import utilities

LoopParams = {'Loops': 1, 'MeasurementPoints': 200}


class MyWindow(PyQt5.QtWidgets.QMainWindow):
    """
    Main class handeling GUI, Hardware and Data Interface.
    Initialize class variables.
    """

    Waveplate = None
    timer = None
    MeasurementCard = None
    MeasurementTask = None

    def __init__(self, parent=None):
        
        super(MyWindow, self).__init__(parent)

        self.ui = uic.loadUi('GUI/SetFluenzSimple.ui', self)
        self.Shutter = MECard()
        self.initializeCard()

        self.btn_close.clicked.connect(self.close)
        self.btn_power.clicked.connect(self.setPower)
        self.btn_fluenz.clicked.connect(self.setFluenz)
        
        self.Main()
        self.show()

    def setPower(self):
        """
        Set Power directly.
        Shutter is closed during movement. The power from the GUI line is 
        searched in the calibration file and the angle is set.
        The chosen angle is not optimized, the first value found in the search 
        is set 
        """
        
        self.moveShutter(True)
        fluence = Fluence()
        angle, reference = fluence.calculateWaveplateAngle(
            float(self.txt_power.toPlainText()))
        self.Waveplate.moveStage_absolute([angle])
        self.moveShutter(False)

    def initializeCard(self):
        """
        MeasurementCard is needed to measure the reference value in the
        photodiode.
        :return: self.MeasurementTask
        """
        self.MeasurementCard = NI_CardCommunication()
        self.MeasurementCard.reset_device("Dev2")
        self.MeasurementTask = self.MeasurementCard.create_Task_ai("Dev2/ai0:5")

    def moveToReference(self, ref, angle):
        """
        Move Waveplate to angle written in the calibration file.
        The reference value from the calibration file is compared to the
        now measured reference value. If the difference is larger than 1%,
        the angle is corrected. The waveplate is moved
        until value is in the 1% range.

        The measured value is the Power in mW measured in the
        Calibration file.

        :param ref: float reference from pump diode in calibration file
        :param angle: float angle recorded in calibration file
        """

        # TODO: change direction of correction if it proves to be wrong
        # TODO: make stepsize relative to how far it is from the goal reference
        self.Waveplate.moveStage_absolute(angle)
        currRef = self.measureReference()

        if abs(currRef) < abs(ref):
            direction = - 1
        else:
            direction = 1

        while ((currRef * 0.01) + currRef) > ref or (
                currRef - (currRef * 0.01)) < ref:
            currRef = self.measureReference()

            self.Waveplate.moveStage(float(self.Waveplate.getCurrPos()) +
                                     (direction * 0.025))
            self.statusReport('Current referenceDiode: '+str(currRef) +
                              ', Goal referenceDiode: '+str(ref))
            self.statusReport('Current Waveplate Angle: ' +
                              str(self.Waveplate.getCurrPos()) +
                              ', Original Goal Angle: '+str(angle))
            QtGui.QApplication.processEvents()
        self.statusReport('Setting Fluence finished!')

    def measureReference(self):
        """
        MEasure the reference value for diode and sort it for unchoped value.
        :return: ReferenceAverage value
        """

        data = self.MeasurementCard.ReadValues_ai(
            self.MeasurementTask, LoopParams)
        chopper = data[3]
        referenceDiode = data[5]
        refchop, refunchop = \
            utilities.sortAfterChopper(referenceDiode, chopper)
        currRef = np.mean(refunchop)
        return currRef

    def setFluenz(self):
        """
        close Shutter
        calculate Fluence by calling the Fluence script. The goal Fluence is
        read from GUI. The power corresponding to that fluence is calculated
        and the angle to reach that power is looked up in th♣e calibration file.

        Shutter is opend again when reference value is reached.
        """

        self.moveShutter(True)
        fluence = Fluence()
        power = fluence.calculateFluence(float(self.txt_fluenz.toPlainText()))
        angle, reference = fluence.calculateWaveplateAngle(power)
        self.moveToReference(reference, angle)
        self.moveShutter(False)

    def moveShutter(self, value):
        """
        Move Shutter.
        Waiting time necessary, because the motor used at the moment can have
        an intertia, if activated after a longer waiting time
        (not deterministic).

        :param value: True: Shutter closed (Transistor cylce open)
                      False: Shutter open (Transistor cycle close)
        :return: if ans is not zero, an error occured
        """
        ans = self.Shutter.setDigValue(value)
        if ans:
            self.statusReport("Problem with shutter!")
            self.timer.stop()
        t.sleep(0.5)

    def closeEvent(self, event):
        """
        Defines the exiting procedure: saving started measurements and
        closing open hardware connections

        :param event: close ("X" of Window or Stop Button)
        :return: Messagebox "Do you want to quit?"
        """

        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.Waveplate.closeStage()
            event.accept()
        else:
            event.ignore()

    def initializeWaveplate(self):
        """
        Initialize Waveplate - rotational motor communication
        with XPS Newport Controller
        Strings of Stage Name ('GROUP3', 'POSITIONER') are set in the
        Web Interface of the XPS Controller

        IMPORTANT: if waveplate is initialized, it will serach for its
        home position, it is not possible to influence serach direction.
        So the sample (or anything else) needs to be protected with shutter
        (or similar) from the possible high power.

        :return: Waveplate object
        """

        self.Waveplate = StageCommunication('GROUP3', 'POSITIONER')
        self.moveShutter(True)
        self.Waveplate.connectStage()
        self.Waveplate.searchForHome()
        self.Waveplate.getCurrPos()

    def Main(self):
        """
        initialize Waceplate and
        Start the QtTimer with update time of 10ms.
        """

        self.initializeWaveplate()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)

    def update(self):
        """
        Update: Check for User Input
        """

        QtGui.QApplication.processEvents()

    def statusReport(self, status):
        """
        Write status in console and in statusbar of application
        :param status: Message for user
        """

        print(status)
        self.statusBar().showMessage(status)


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
