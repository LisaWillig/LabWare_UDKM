#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SimpleDAQSignal.py

Author: Lisa Willig
Last Edited: 30.11.2018

Python Version: 3.6.5
PyQt Version: 5.9.2
Pyqtgraph Version: 0.10.1

Application to show the analog Input Signals of the DAQ Cards. Physically that
means look at the Boxcar Outputs without further calculations.
Additionally the magnetic field can be set and the shutter can be closed.

Structure of this module:
1) Imports
3) Global Variables
4) Main Class (would benefit from refactor: clear data from GUI Operations)
5) main system call

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# General Imports
import nidaqmx
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5 import uic
import PyQt5
import sys

# Imports of own modules
from modules.NI_CardCommunication_V2 import NI_CardCommunication
from modules.MERedLab_Communication import MECard

# Global variables necessary for suvmodul NI_CardCommunication
LoopParams = {'MeasurementPoints': 1}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Main Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


class MyWindow(PyQt5.QtWidgets.QMainWindow):
    """
    Main GUI, Logic and Data Handeling class
    Needs to be disentangled

    Structure of class:
    a) init (GUI loading & initialization, Instance variable initialization)
    b) events
    c) NI DAQ Channel Setup
    d) Hardware Method
    e) Plotting
    f) Main and Update
    g) UI method
    """

    MeasurementCard = None
    Shutter = None
    MeasureTask = None
    WritingTask = None
    dataLine = None
    timer = None
    ptr = None
    data = []

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ a) Init ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        # load GUI from .ui file (created in QtDesigner)
        self.ui = uic.loadUi('GUI/BalancedDiode.ui', self)
        pg.setConfigOptions(antialias=True)

        # Connect Buttons with Function calls
        self.RestartButton.clicked.connect(self.Main)
        self.StopButton.clicked.connect(self.close)
        self.BoxDeviceChoice.currentIndexChanged.connect(self.changeChannel)
        self.ButtonVoltageSet.clicked.connect(self.setVoltageForMagnet)
        self.EditVoltageValue.returnPressed.connect(self.setVoltageForMagnet)
        self.ButtonShutter.toggled.connect(self.moveShutter)

        self.setupChannels()
        self.initializeChannels()

        # Start Main and show GUI
        self.Main()
        self.show()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ b) events ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def closeEvent(self, event):
        """
        Methods called when application is closed.
        Write Zero as last field, so that magnetic field is not present.
        Close all connection to Hardware, stop the timer.
        :param event:
        """

        self.timer.stop()
        self.MeasurementCard.WriteValues(self.WritingTask, 0)
        self.MeasurementCard.CloseTask(self.MeasureTask)
        self.MeasurementCard.CloseTask(self.WritingTask)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ c) NI DAQ Channel Setup ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def initializeChannels(self):
        """
        intialize DAQ Devices and chose the standard task (to start with) for
        reading (Balanced Photodiode Input) and writing Task for magnetic field.
        """

        self.MeasurementCard = NI_CardCommunication()
        self.MeasurementCard.reset_device("Dev2")
        self.MeasurementCard.reset_device("Dev1")
        self.MeasureTask = \
            self.MeasurementCard.create_Task_ai("Dev2/ai0", bTrig=False)
        self.ui.BoxDeviceChoice.setCurrentIndex(8)
        self.WritingTask = \
            self.MeasurementCard.create_Task_ao0("Dev1/ao0", bTrig=False)

    def setupChannels(self):
        """
        Read the Analog Input Channels from all connected NI DAQ Devices.
        :return: List of channels and devices in GUI
        """

        DevList = nidaqmx.system._collections.\
            device_collection.DeviceCollection().device_names
        ChanList = []
        for entry in DevList:
            ChanList.append(self.channelList(entry))
        ChanList = [item for sublist in ChanList for item in
                    sublist]  # flatten nested Channellist
        for channel in ChanList:
            self.ui.BoxDeviceChoice.addItem(channel)

    @staticmethod
    def channelList(Device):
        """
        Ask the NI DAQ Device for a list of names of all his Analog Input
        Physical Channels.

        :param Device:
        :return: Channellist
        """

        return nidaqmx.system._collections.physical_channel_collection.\
            AIPhysicalChannelCollection(Device).channel_names

    def changeChannel(self):
        try:
            self.MeasurementCard.CloseTask(self.MeasureTask)
            self.MeasureTask = self.MeasurementCard.create_Task_ai(
                self.ui.BoxDeviceChoice.currentText(), bTrig=False)
            self.statusReport("Changed Channel")
        except AttributeError:
            pass

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ d) Hardware Methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def moveShutter(self):
        """
        Check the GUI for Shutter Button Status.
        Move Shutter and change Text on Button accordingly.
        """

        if self.ui.ButtonShutter.isChecked():
            self.ui.ButtonShutter.setText("Shutter closed")
            self.closeShutter(True)
        else:
            self.ui.ButtonShutter.setText("Shutter opend")
            self.closeShutter(False)

    def closeShutter(self, value):
        """
        Initialize shutter if it has not been called before. The initilization
        time for the ME Card is quite long. So it is better to not call it if
        it is not used.
        :param value: Value set for Shutter circuit.
        """

        if self.Shutter is None:
            self.statusReport("Shutter initialization - takes a while")
            self.Shutter = MECard()
        ans = self.Shutter.setDigValue(value)
        self.statusReport("Shutter moved")
        if ans:
            self.statusReport("Problem with shutter!")
            self.timer.stop()

    def setVoltageForMagnet(self):
        """
        Write Voltage value for Magnet. The limits are checked (hardcoded: need
        to be changed for different magnet manually) and the value is not
        written if it is above the given level.
        """

        value = float(self.EditVoltageValue.text())
        if -5.5 < value < 5.5:
            self.MeasurementCard.WriteValues(self.WritingTask, value)
        else:
            self.statusReport("Value is not in a valid range!")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ e) Plotting ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def Plot_Diode(self):
        """
        Set Plot variables and parameters. Besides the written data in the list
        "data" a line at y = 0 is added for visual clarity.
        """

        self.dataLine = \
            self.BalancedDiodePlot.getPlotItem().plot(pen=(215, 128, 26))
        self.BalancedDiodePlot.getPlotItem().\
            addLine(y=0, pen=(215, 128, 26, 125))

    def update_Plot(self):
        """
        Read data and plot the relevant part.
        The ptr parameter determines the scrolling behaviour.
        """

        dat = self.MeasurementCard.ReadValues_ai(self.MeasureTask, LoopParams)
        data1 = dat[0]
        self.data.append(data1)
        self.data[:-1] = self.data[1:]
        self.ptr += 1
        self.dataLine.setData(self.data)
        self.dataLine.setPos(self.ptr, 0)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ f) Main and update ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def Main(self):
        """
        Prepare Plot (Clear it, set the parameters)
        Start the main Update Loop with the QtTimer updating each 10ms.
        """

        self.BalancedDiodePlot.clear()
        self.Plot_Diode()
        self.data = []
        self.ptr = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20)

    def update(self):
        """
        Update Plot and check for Button Activity
        """

        self.update_Plot()
        QtGui.QApplication.processEvents()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ g) UI method ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def statusReport(self, status):
        """
        write Status in Status Bar as well as console
        :param status:
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
