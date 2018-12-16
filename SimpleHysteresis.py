#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TRMOKE_V20.py

Author: Alexander von Reppert, Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
PyQt Version: 5.9.2
Pyqtgraph Version: 0.10.1

Application to measure Time Resolved and Static Hysteresis.

Structure of this module:
1) Imports
2) Debug Settings
3) Global Variables
4) Main Class (would benefit from refactor: clear data from GUI Operations)
5) main system call

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# General Imports
import sys
from PyQt5 import uic, QtGui
import PyQt5
from PyQt5.QtWidgets import QApplication, QMessageBox, QErrorMessage
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import os
import matplotlib.pyplot as plt

# Imports of own modules
from StageCommunication_V2 import StageCommunication
from NI_CardCommunication_V2 import NI_CardCommunication
from MERedLab_Communication import MECard
from calculateFluence import Fluence
import utilities

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Global Variables and Dictionaries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

Parameters = {'MeasurementPoints': 22,
              'loopfield': 2.,
              'Amplitude': 2.,
              'timeZero': -1,
              'Power': -1}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Main Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MyWindow(PyQt5.QtWidgets.QMainWindow):
    """
    main class
    handles the GUI communication and Data aquisition.

    TODO: Decouple Data and GUI operations

    Structure:
    a) Init class variables and GUI
    b) Button Disable Control
    c) Events
    d) Read Parameters from GUI
    e) Initialize and Close Hardware
    f) Hardware orders
    g) Calculate Measurement Parameters
    h) update loops & Main
    i) Save Data
    j) Data Analysis
    k) Settings and Update of Plots


    """

    stage = None
    shutter = None
    timer = None
    measurementCard = None
    writingTask = None
    readingTask = None
    sampleName = None
    folderName = None
    HystDelay_ReadFromFile = False
    delays = None
    resultList = None

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ a) Init ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        # load GUI from .ui file (created in QtDesigner)
        self.ui = uic.loadUi('GUI/SimpleHysteresis.ui', self)
        pg.setConfigOptions(antialias=True)

        # booleans that ensure communication to devices is only started once
        self.shut = 0
        self.card_ini = 0
        self.stageIni = 0

        # read last timeZeroValue from Measurementlist
        self.line_timeZero.setText(str(utilities.readLastTimeZero()))

        # Button connections
        self.btn_close.clicked.connect(self.close)
        self.btn_start.clicked.connect(self.Main)
        self.btn_shutter.toggled.connect(self.shutterState)
        self.btn_delayFile.toggled.connect(self.toggleControl_delayFile)
        self.btn_delayGUI.toggled.connect(self.toggleControl_delayGUI)

        # show GUI
        self.show()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ b) Button Disable Control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def toggleControl_delayGUI(self):
        """
        if the Read From GUI - Version for the Hysteresis Delay Values is
        chosen, enable the GUI elements for Hysteresis Delay
        """

        self.HystDelay_ReadFromFile = False
        self.line_delays.setDisabled(False)

    def toggleControl_delayFile(self):
        """
        if the Read From File - Version for the Hysteresis Delay Values is
        chosen, disable the GUI elements for Hysteresis Delay
        """

        self.HystDelay_ReadFromFile = True
        self.line_delays.setDisabled(True)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ c) Events ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
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
            self.closeAllHardware()
            event.accept()
        else:
            event.ignore()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ d) Read Parameters from GUI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def readParameters(self):
        """
        reads Parameters from the UI in the global
        Measurement Parameter dictionary
        """

        Parameters['MeasurementPoints'] = \
            int(self.line_measPoints.toPlainText())
        Parameters['loopfield'] = float(self.line_loopField.toPlainText())
        Parameters['Amplitude'] = float(self.line_amplitude.toPlainText())
        Parameters['Power'] = float(self.line_power.toPlainText())
        Parameters['timeZero'] = float(self.line_timeZero.toPlainText())
        self.sampleName = str(self.line_sampleName.toPlainText())
        self.createDelayVector()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ e) Initialize and Close Hardware ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def initializeHardware(self):
        """
        Initialize Herdware: Stage and Measurement Card.
        The shutter Card is only initialized if it is used, because
        communication is quite long.
        """

        self.initializeMeasurementCard()
        self.initializeStage()

    def closeAllHardware(self):
        """
        Close all Hardware Communication.
        """

        self.closeStage()
        self.cardClosing()

    def initializeShutterCard(self):
        """
        Initializes communication with MELab Card.
        Communication is very slow, should be avoided if not needed
        Only used for shutter of pump laser
        """

        print('Initialize Shutter Card')
        if self.shut == 0:
            self.shutter = MECard()
        self.shut = 1

    def initializeStage(self):
        """
        Initialize Stage communication with XPS Newport Controller
        Strings of Stage Name ('GROUP1', 'POSITIONER') are set in the
        Web Interface of the XPS Controller
        Also the Stage offset determined by length of Stage and the number of
        times the light crosses the stage is hardcoded, needs to be changed
        in the code for each setup.

        StageSpeedParams : can be set to 0, than default values will be used

        self.stageIni : Boolean to make sure it is initialized only once at
        the time
        :return: stage object
        """
        self.statusReport('Initialize Stage')
        if self.stageIni == 1:
            return
        self.stageIni = 1
        self.stage = StageCommunication('GROUP1', 'POSITIONER')
        self.stage.connectStage()

    def closeStage(self):
        """
        Close Stage Communication
        """

        if self.stageIni == 0:
            return
        self.stage.closeStage()
        self.stageIni = 0

    def initializeMeasurementCard(self):
        """
        Communication for DAQ Measurement Cards from National Instruments
        Boolean checks zhaz connection is only started once

        Created task for several channels issynchronized,
        so reading the analog input (ai) from channel 0:5 means
        the timing for reading is identical

        Cards cannot read and write at the same time
        (tasks need to be closed before it is possible to switch)
        :return: Measurement Tasks
        """

        if self.card_ini == 1:
            return
        self.measurementCard = NI_CardCommunication()
        self.measurementCard.reset_device("Dev1")
        self.measurementCard.reset_device("Dev2")
        self.writingTask = self.measurementCard.create_Task_ao0("Dev1/ao0")
        self.readingTask = self.measurementCard.create_Task_ai("Dev2/ai0:7")
        self.card_ini = 1

    def cardClosing(self):
        """
        Closes the communication for NI DAQ Card only if it was opend before
        """
        if self.card_ini == 0:
            return
        self.measurementCard.CloseTask(self.writingTask)
        self.measurementCard.CloseTask(self.readingTask)
        self.card_ini = 0

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ f) Hardware orders ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def shutterState(self):
        """
        Handles the shutter State as well as text on the button
        1 : circuit open, shutter closed
        0 : circuit closed, shutter open
        """

        if self.ui.btn_shutter.isChecked():
            if not self.shutter:
                self.initializeShutterCard()
            ans = self.shutter.setDigValue(1)
            self.ui.btn_shutter.setText("shutter Closed")
            self.shut = 1
            self.line_delays.setDisabled(True)
            self.line_power.setDisabled(True)
            self.line_timeZero.setDisabled(True)
            if ans:
                print("Problem with shutter!")
        else:
            ans = self.shutter.setDigValue(0)
            self.ui.btn_shutter.setText("shutter Open")
            self.line_delays.setDisabled(False)
            self.line_power.setDisabled(False)
            self.line_timeZero.setDisabled(False)
            self.shut = 0
            if ans:
                print("Problem with shutter!")

    def moveShutter(self, value):
        """
        move shutter to position 0 (closed) or 1 (open)
        sleeping time is necessary because motor of shutter is sometimes
        unpredictable delayed in reaction after value is set
        :param value:
        """
        ans = self.shutter.setDigValue(value)
        if ans:
            print("Problem with shutter!")
            self.timer.stop()
        t.sleep(0.5)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ g) Calculate Measurement Parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def createMeasurementArray(self):
        """
        create Array with empty columns for measured values and applied voltage
        in first column
        """

        HystArray = self.createHysteresisArray()
        self.resultList = np.zeros((len(HystArray), 5))
        self.resultList[:, 0] = HystArray

    @staticmethod
    def createHysteresisArray():
        """
        creates the array with the voltage values
        :return Array:
        """

        step = float(Parameters['Amplitude'])/100
        Amplitude = float(Parameters['Amplitude'])
        loopField = int(Parameters['loopfield'])

        startArray = np.arange(0, Amplitude + step, step)
        loopArray1 = np.arange(Amplitude + step, -1 * (Amplitude + step),
                               -1 * step)
        loopArray2 = np.arange(-1 * (Amplitude + step), Amplitude + step, step)
        loopArray = np.concatenate([loopArray1, loopArray2])
        endArray = np.arange((Amplitude + step), 0 - step, -step)

        Array = startArray
        for i in range(loopField):
            Array = np.concatenate([Array, loopArray])
        Array = np.concatenate([Array, endArray])

        return Array

    def createDelayVector(self):
        """
        create the delay vector by reading it from file or from GUI
        :return: self.delays
        """

        if self.HystDelay_ReadFromFile:
            self.delays = \
                utilities.readHysteresisDelayfromFile(
                    Parameters['timeZero'])
        else:
            delay = str(self.line_delays.toPlainText())
            self.delays = utilities.readHysteresisDelayfromGUI(
                delay, Parameters['timeZero'])

    def createfolderName(self):
        """
        create a Folder Name depending on the GUI entries and measurement mode
        """

        if self.shut:
            self.folderName = str(self.sampleName)+"_" + \
                        str(Parameters['Amplitude']) + "V_static"
        else:
            self.folderName = str(self.sampleName)+"_" + \
                        str(Parameters['Amplitude']) + "V"

    def checkFolderNaming(self):
        """
        create Folder, check if the names are valid
        :return:
        """

        self.createfolderName()
        try:
            self.makeFolder(str(self.folderName))
        except OSError:
            error_dialog = QErrorMessage()
            error_dialog.showMessage('The entered File Name is not valid')
            self.timer.stop()

    def createResultFolder(self):
        """
        calculate the fluence from the given Power and save the data under the
        correct folder.
        """

        if Parameters['Power'] == -1:
                self.makeFolder(str(self.folderName) + "/-1")
                SaveDataFile = str(self.folderName) + "/-1/"
        else:
            flu = Fluence()
            fluence = flu.calculateFluenceFromPower(Parameters['Power'])
            self.makeFolder(
                str(self.folderName) + "/" + str(fluence) + "mJcm")
            SaveDataFile = str(self.folderName) + "/" + + str(
                fluence) + "mJcm/"

        return SaveDataFile

    def makeFolder(self, PathToFolder):
        """
        check if the Folder already exists. If not, create it. If it does, show
        a message and ask if folder should be overwritten.
        If not: restart is necessary. If yes, folder is used.
        :param PathToFolder:
        """

        if not os.path.exists(PathToFolder):
            os.makedirs(PathToFolder)
        if os.path.exists(PathToFolder):
            ans = QtGui.QMessageBox.question(self, '',
                                             "This folder already exitst. "
                                             "Are you sure you want to "
                                             "overwrite it?",
                                             QtGui.QMessageBox.No |
                                             QtGui.QMessageBox.Yes)
            if ans == QtGui.QMessageBox.Yes:
                os.chdir('D:\\Data\\HysteresisPumpProbe')
                return
            else:
                self.statusReport("Idle")
                self.closeAllHardware()
                sys.exit(1)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ h) update loops & Main ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def Main(self):
        """
        Initialize Hardware.
        Prepare GUI.
        Change Working Directory.
        Start the main Update Loop with the QtTimer updating each 10ms.
        """

        self.initializeHardware()

        self.readParameters()
        self.checkFolderNaming()
        self.HysteresisPlot.clear()
        self.HysteresePlot()

        # starts the main Update Loop of Qt
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)

    def update(self):
        """
        Update Loop for application for Measurement of Hysteresis
        """

        for delay in self.delays:

            # measurement card has to be reset each measurement, otherwise
            # buffer might overflow with too many values written
            self.initializeMeasurementCard()

            # set position of stage
            try:
                stageDelay = self.stage.calcStageWay(delay)
                lightDelay = self.stage.calcLightWay(stageDelay)
            except ValueError:
                # catch the possibility that an empty string is given after
                # end of program
                break

            self.stage.moveStage(stageDelay)
            self.statusReport("stage: " + str(lightDelay))
            self.createMeasurementArray()

            for i in range(len(self.resultList[:, 0])):
                try:
                    self.measurementCard.WriteValues(self.writingTask,
                                                     self.resultList[i, 0])
                except DaqError:
                    self.timer.stop()
                    break

                attempt = 1

                while attempt:
                    # this while loop catches a hickup in the laser trigger
                    # causing tho measure an uneven number of choped and
                    # unchoped values

                    # read data
                    data = self.measurementCard.ReadValues_ai(self.readingTask,
                                                              Parameters)
                    Diode = data[0]
                    Chopper = data[3]
                    singleDiodeRef = data[6]

                    choplist, unchoplist = \
                        utilities.sortAfterChopper(Diode, Chopper)
                    refChop, refUnchop = \
                        utilities.sortAfterChopper(singleDiodeRef, Chopper)

                    if np.size(choplist) == np.size(unchoplist):
                        attempt = 0

                self.resultList[i, 1] = np.mean(choplist)
                self.resultList[i, 2] = np.mean(unchoplist)
                self.resultList[i, 3] = np.mean(refChop)
                self.resultList[i, 4] = np.mean(refUnchop)

                self.update_HysteresePlot()
                QtGui.QApplication.processEvents()

            # Analysis
            Amp = self.calculateMOKENormalization()
            SaveDataFile = self.createResultFolder()
            self.savePlotHysteresis(Amp, delay)
            self.saveData(SaveDataFile, delay)

            self.cardClosing()

        self.cardClosing()
        self.stage.closeStage()

    def updateGUI(self):
        """
        updates progress bar and painting of Hysteresis measurement
        """
        self.calculate_Progress()
        self.update_HysteresisPlot()

    def statusReport(self, status):
        """
        Write status in console and in statusbar of GUI
        :param status: message thet gets printed
        """

        print(status)
        self.statusBar().showMessage(status)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ i) Save Data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def saveData(self, SaveDataFile, delay):
        """
        Save Textfile of measurement with
        :param SaveDataFile: 
        :param delay: 
        :return: 
        """
        np.savetxt(
            SaveDataFile + str(self.sampleName)+'_Hysteresis' + str(int(delay))
            + '.dat', self.resultList, header='#Current (A)\t HystPumped_up\t '
                                              'HystPumped_down\t '
                                              'HystUnPumped_up\t'
                                              'HystUnPumed_downp\t',
            delimiter="\t")

    def savePlotHysteresis(self, Amp, delay):
        """
        Plot the measured Hysteresis in mV vs. A. Hysteresis are not averaged.
        :param Amp:
        :param delay:
        """
        plt.figure(figsize=(10, 6))
        plt.suptitle('Normvalue: ' + str(Amp * 1000) + " mV")
        plt.title(str(self.Power) + ' mW ' + str(int(delay)) + " ps")
        plt.plot(self.resultList[:, 0], self.resultList[:, 1] * 1000, 'o-b',
                 lw=2, ms=2,
                 label='Not pumped')
        plt.plot(self.resultList[:, 0], self.resultList[:, 2] * 1000, 's-r',
                 lw=2, ms=2,
                 label='Pumped')
        plt.xlabel("Current (A)")
        plt.ylabel("Balanced Diode Signal (mV)")
        plt.grid()
        plt.legend()
        plt.savefig(
            str(SaveImageFile) + 'SampleHysteresisCurrent' + str(int(delay)) +
            '.png', bbox_inches="tight", dpi=300)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ j) Data Analysis ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def calculateMOKENormalization(self):
        """
        calculate the normalizationValue for the Hysteresis.
        :return: Amp: MOKE Amplitude in mV
        """

        threshold = float(Parameters['Amplitude']) * 4 / 5
        selectMin = self.resultList[:, 0] > threshold
        selectMax = self.resultList[:, 0] < -1 * threshold
        minAmplitude = np.mean(self.resultList[selectMin, 1])
        maxAmplitude = np.mean(self.resultList[selectMax, 1])
        Amp = np.abs(minAmplitude - maxAmplitude)
        print("Moke Amplitude: " + str(Amp * 1000) + " mV")
        return Amp

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ k) Settings and Update of Plots ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def HysteresePlot(self):
        """
        Initialize curves for four possible lines: pumped & unpumped balanced
        diode as well as intensity diode
        """

        self.curve5 = self.HysteresisPlot.getPlotItem().plot(
            pen=(38, 126, 229))
        self.curve6 = self.HysteresisPlot.getPlotItem().plot(
            pen=(215, 128, 26))

        self.curve1 = self.HysteresisPlot.getPlotItem().plot(
            pen='y')
        self.curve2 = self.HysteresisPlot.getPlotItem().plot(
            pen='y')

        self.HysteresisPlot.getPlotItem().setRange(
            xRange=(Parameters['Amplitude'],
                    -Parameters['Amplitude']))

    def update_HysteresePlot(self):
        """
        Update Hysteresis Plot. curve 1 and 2 need to be uncommented to show
        intensity change. Normally would mess with autoscale properties of
        hysteresis.
        """

        self.curve5.setData(self.resultList[:, 0], self.resultList[:, 1])
        self.curve6.setData(self.resultList[:, 0], self.resultList[:, 2])
        #self.curve1.setData(self.resultList[:, 0], self.resultList[:, 3])
        #self.curve2.setData(self.resultList[:, 0], self.resultList[:, 4])


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Main System Call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

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
