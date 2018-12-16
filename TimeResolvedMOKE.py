#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TRMOKE_V20.py

Author: Lisa Willig
Last Edited: 30.11.2018

Python Version: 3.6.5
PyQt Version: 5.9.2
Pyqtgraph Version: 0.10.1

Application to measure Time Resolved MOKE Signals and Static &
Time Resolved Hysteresis.

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
import os
import sys
import PyQt5
from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import QApplication, QMessageBox
import pyqtgraph as pg
import pyqtgraph.exporters as exporters
from pyqtgraph.Qt import QtCore
import time as t
from datetime import datetime
import pandas as pd
import numpy as np

# Imports of own modules
from calculateFluence import Fluence
import utilities

# Debug Settings
# if variable is True: Hardware is not needed for testing functions
bDebug = False

# import of Hardware modules
if not bDebug:
    from StageCommunication_V2 import StageCommunication
    from NI_CardCommunication_V2 import NI_CardCommunication
    from MERedLab_Communication import MECard
else:
    from StageCommunication_V2 import StageCommunication_Debug
    StageCommunication = StageCommunication_Debug
    from NI_CardCommunication_V2 import NI_CardCommunication_Debug
    NI_CardCommunication = NI_CardCommunication_Debug
    from MERedLab_Communication import MECard_Debug
    MECard = MECard_Debug


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Global Variables and Dictionaries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


MeasParams = {'sampleName': 'XXX', 'angle': -1., 'Fluence': -1.,
              'timeZero': -1., 'timeoverlapp': 5.}
LoopParams = {'Loops': 1, 'MeasurementPoints': 200}
Parameters = {'Voltage': 2.}
HysteresisParameters = {'Amplitude': 5., 'Stepwidth': 0.05, 'Delay': 0.,
                        'Loops': 5}
Stage_SpeedParams = {'Velocity': 20, 'Acceleration': 20}
StageParams_ps = {'StartPoint': 0., 'EndPoint': 10., 'StepWidth': 5.}
StageParams_mm = {}
Offset_mm = 75

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Main Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


class MyWindow(PyQt5.QtWidgets.QMainWindow):
    """
    Main GUI, Logic and Data Handeling class
    Needs to be disentangled

    Structure of class:
    a) init (GUI loading & initialization, Instance variable initialization)
    b) Button Control (disable UI elements depending on choices)
    c) events
    d) read Parameters from GUI
    e) prepare GUI, clear and setup plots
    f) initialize and close Hardware
    g) Hardware orders
    h) calculate Measurement Parameters
    i) update loops & Main
    j) measurement order
    k) Data Analysis
    l) Settings and Update of Plots
    m) Save Operations
    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ a) Init ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        # load GUI from .ui file (created in QtDesigner)
        self.ui = uic.loadUi('GUI/Hysteresis_PumpProbe_MOKE_V6.ui', self)
        pg.setConfigOptions(antialias=True)
        # make Debug Mode clearly visible
        if bDebug:
            self.ui.debug_Label.setText("DEBUG")
            self.ui.debug_Label.setStyleSheet('color: yellow')

        # read last timeZeroValue from Measurementlist
        self.timeZeroLine.setText(str(utilities.readLastTimeZero()))

        # Variables used for Tracking Initialization Status and GUI Choices
        self.Pos_ps = 0
        self.stageIni = 0
        self.waveIni = 0
        self.cardIni = 0
        self.StartMeasurement = False
        self.Initialize = False
        self.Stage_ReadFromFile = False
        self.Voltage_ReadFromFile = False
        self.Fluence_ReadFromFile = False
        self.HystDelay_ReadFromFile = False
        self.bFolderCreated = False
        self.timerJustage = None
        
        # Connect Buttons with Function calls
        self.RestartButton.clicked.connect(self.restart)
        self.StopButton.clicked.connect(self.close)
        self.StartButton.clicked.connect(self.Main)
        self.Stage_GUIButton.toggled.connect(self.toggleControl_StageGUI)
        self.Stage_FileButton.toggled.connect(self.toggleControl_StageFile)
        self.AO_FileButton.toggled.connect(self.toggleControl_AOFile)
        self.AO_GUIButton.toggled.connect(self.toggleControl_AOGUI)
        self.Fluence_FileButton.toggled.connect(self.toggleControl_FFile)
        self.Fluence_GUIButton.toggled.connect(self.toggleControl_FGUI)
        self.HystDelay_FileButton.toggled.connect(self.toggleControl_delayFile)
        self.HystDelay_GUIButton.toggled.connect(self.toggleControl_delayGUI)

        # show GUI
        self.show()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ b) Button Disable Control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def toggleControl_StageGUI(self):
        """
        if the Read From GUI - Version for the Stage values is chosen,
        enable the GUI elements for stage control
        """
              
        self.Stage_ReadFromFile = False
        self.Stage_Start.setDisabled(False)
        self.Stage_Stop.setDisabled(False)
        self.Stage_Stepwidth.setDisabled(False)
        self.Stage_Velocity.setDisabled(False)
        self.Stage_Acceleration.setDisabled(False)
        
    def toggleControl_StageFile(self):
        """
        if the Read From File - Version for the Stage values is chosen,
        disable the GUI elements for stage control
        """

        self.Stage_ReadFromFile = True
        self.Stage_Start.setDisabled(True)
        self.Stage_Stop.setDisabled(True)
        self.Stage_Stepwidth.setDisabled(True)
        self.Stage_Velocity.setDisabled(True)
        self.Stage_Acceleration.setDisabled(True)
        
    def toggleControl_AOFile(self):
        """
        if the Read From File - Version for the Voltage values is chosen,
        disable the GUI elements for Set Voltage
        """

        self.Voltage_ReadFromFile = True
        self.Voltage_Input.setDisabled(True)

    def toggleControl_AOGUI(self):
        """
        if the Read From GUI - Version for the Voltage values is chosen,
        enable the GUI elements for Set Voltage
        """
            
        self.Voltage_ReadFromFile = False
        self.Voltage_Input.setDisabled(False)
                   
    def toggleControl_FGUI(self):
        """
        if the Read From GUI - Version for the Fluence values is chosen,
        enable the GUI elements for Set Fluence
        """

        self.Fluence_ReadFromFile = False
        self.fluenceLine.setDisabled(False)
    
    def toggleControl_FFile(self):
        """
        if the Read From File - Version for the Fluence values is chosen,
        disable the GUI elements for Set Fluence
        """

        self.Fluence_ReadFromFile = True
        self.fluenceLine.setDisabled(True)
        
    def toggleControl_delayGUI(self):
        """
        if the Read From GUI - Version for the Hysteresis Delay Values is
        chosen, enable the GUI elements for Hysteresis Delay
        """

        self.HystDelay_ReadFromFile = False
        self.delay_HysteresisLine.setDisabled(False)
    
    def toggleControl_delayFile(self):
        """
        if the Read From File - Version for the Hysteresis Delay Values is
        chosen, disable the GUI elements for Hysteresis Delay
        """

        self.HystDelay_ReadFromFile = True
        self.delay_HysteresisLine.setDisabled(True)

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
            "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:

            # if measurement already started: save the collected data and
            # stop the main update loop
            if self.StartMeasurement:
                self.saveData()
                self.timer.stop()

            # if hardware is initialized, close connection before exit the
            # application
            if self.Initialize:
                self.closeNICard()
                self.closeStage()
            event.accept()
        else:
            event.ignore()

    def restart(self):
        """
        Save Data that is already measured,
        close Tasks and start Main File again
        """

        if self.SaveButton.isChecked():
            self.saveData()
        self.MeasurementCard.CloseTask(self.MeasurementTask)
        self.MeasurementCard.CloseTask(self.WritingTask)
        self.timer.stop()
        self.closeStage()

        self.Main()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ d) Read Parameters from GUI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def readParameters(self):
        """
        reads the values from the GUI Interface and saves them in
        global dictionaries
        """

        Parameters['Voltage'] = float(self.Voltage_Input.toPlainText())
        StageParams_ps['StartPoint'] = float(self.Stage_Start.toPlainText())
        StageParams_ps['EndPoint'] = float(self.Stage_Stop.toPlainText())
        StageParams_ps['StepWidth'] = float(self.Stage_Stepwidth.toPlainText())
        Stage_SpeedParams['Velocity'] = (self.Stage_Velocity.toPlainText())
        Stage_SpeedParams['Acceleration'] = \
            (self.Stage_Acceleration.toPlainText())
        LoopParams['Loops'] = int(self.Loops.toPlainText())
        LoopParams['MeasurementPoints'] = int(self.Repeats.toPlainText())
        LoopParams['MeasurementPoints'] = LoopParams['MeasurementPoints']*2
        MeasParams['sampleName'] = \
            str(self.sampleNameLine.toPlainText())
        MeasParams['angle'] = float(self.angleLine.toPlainText())
        MeasParams['Fluence'] = float(self.fluenceLine.toPlainText())
        MeasParams['timeZero'] = \
            float(self.timeZeroLine.toPlainText())
        MeasParams['timeoverlapp'] = \
            float(self.adjustementline.toPlainText())
        HysteresisParameters['Stepwidth'] = \
            float(self.stepwidth_Hysteresis.toPlainText())
        HysteresisParameters['Loops'] = \
            float(self.loops_Hysteresis.toPlainText())

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ e) Prepare GUI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def prepareGUI(self):
        """
        clear Plots (if other measurement started before)
        and call settings for plots
        """

        self.statusReport('Prepare GUI')
        self.PP_Signal1_PlotAverage.clear()
        self.PP_Signal1_PlotAll.clear()
        self.PP_Signal2_PlotAll.clear()
        self.PP_Signal2_PlotAverage.clear()
        self.MOKE_Average_Plot.clear()
        self.HysteresisPlot.clear()
        self.IntensityPlot.clear()
        self.PumpOnly_Plot.clear()
        self.ProbeOnly_Plot.clear()

        self.plotProbeOnly()
        self.plotPumpOnly()
        self.plotPP1()
        self.plotPP2()
        self.plotMOKE()
        self.plotHysteresis()
        self.plotIntensity()

        self.calculateNumberOfMeasurements()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ f) Initialize and Close Hardware ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def initializeAllHardware(self):
        """
        Start communication with hardware
        Set value for initialization to true
        """

        self.Initialize = True
        self.readParameters()
        self.initializeNICard()
        self.initializeStage()
        self.initializeShutterCard()

    def initializeNICard(self):
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

        if self.cardIni == 1:
            return
        self.cardIni = 1

        self.statusReport('Initialize Measurement Card')
        self.MeasurementCard = NI_CardCommunication()
        self.MeasurementCard.reset_device("Dev1")
        self.MeasurementCard.reset_device("Dev2")
        self.MeasurementTask = self.MeasurementCard.create_Task_ai("Dev2/ai0:5")
        self.WritingTask = self.MeasurementCard.create_Task_ao0("Dev1/ao0")

    def initializeShutterCard(self):
        """
        Initializes communication with MELab Card.
        Communication is very slow, should be avoided if not needed
        Only used for shutter of pump laser
        """

        self.statusReport('Initialize Shutter Card')
        self.Shutter = MECard()

    def closeNICard(self):
        """
        Closes the communication for NI DAQ Card
        """
        if self.cardIni == 0:
            return
        self.cardIni = 0
        self.MeasurementCard.CloseTask(self.WritingTask)
        self.MeasurementCard.CloseTask(self.MeasurementTask)

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
        self.stage.setStageParams(Stage_SpeedParams)
        self.stage.getCurrPos()

    def closeStage(self):
        """
        Close Stage Communication
        """

        self.stage.closeStage()
        self.stageIni = 0

    def initializeWaveplate(self):
        """
        Initialize Waveplate - rotational motor communication
        with XPS Newport Controller
        Strings of Stage Name ('GROUP3', 'POSITIONER') are set in the
        Web Interface of the XPS Controller

        self.waveIni : Boolean to make sure it is initialized only once at
        the time

        IMPORTANT: if waveplate is initialized, it will serach for its
        home position, it is not possible to influence serach direction.
        So the sample (or anything else) needs to be protected with shutter
        (or similar) from the possible high power.

        :return: Waveplate object
        """

        self.statusReport('Initialize Waveplate')
        if self.waveIni == 1:
            return
        self.waveIni = 1
        self.Waveplate = StageCommunication('GROUP3', 'POSITIONER')
        self.Waveplate.connectStage()
        self.Waveplate.searchForHome()
        self.Waveplate.getCurrPos()

    def closeWaveplate(self):
        """
        Close Waveplate Communication
        """

        self.waveIni = 0
        self.Waveplate.closeStage()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ g) Hardware orders ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

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

        self.Waveplate.moveStage_absolute(angle)
        currRef = self.measureReference()

        if abs(currRef) < abs(ref):
            direction = - 1
        else:
            direction = 1

        count = 0
        while ((currRef * 0.025) + currRef) > ref or (
                currRef - (currRef * 0.025)) < ref:

            currRef = self.measureReference()
            self.Waveplate.moveStage(float(self.Waveplate.getCurrPos()) +
                                     (direction * 0.025))
            count += 1
            if count == 150:
                self.Waveplate.moveStage_absolute(angle)
                direction = direction * -1
            QtGui.QApplication.processEvents()

            print(count)
            self.statusReport('Current referenceDiode: '+str(currRef) +
                              ', Goal referenceDiode: '+str(ref))
            self.statusReport('Current Waveplate Angle: ' +
                              str(self.Waveplate.getCurrPos()) +
                              ', Original Goal Angle: '+str(angle))

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

    def checkIfLaserOff(self, reference):
        """
        control if laser seems to be off: check reference diode value

        if value is 0: do something,
        f.e. write Email with notification

        :param reference:  current measurement from voltage diode
        """
        if round(np.mean(reference), 4) == 0:
            print("Laser is off!?")
            utilities.sendEmail(
                "Laser is not in expected range for reference value!")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ h) Calculate Measurement Parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def calculateMeasurementParams(self):
        """
        create save parameters and calculate values from GUI values
        """

        self.createTimeStamp()
        self.createVectors()
        self.createSaveFrame()

    def createVectors(self):
        """
        Create the measurement vectors for the different variables depending
        on if they are read from GUI or from file

        :return:

        self.stageVector_ps : Stage Delays for TR MOKE in Pikoseconds (ps)
        self.stageVector_mm : Stage Delays for TR MOKE in Millimetres (mm)
        self.saveVector : Stage Delays for TR MOKE in Pikoseconds (ps)
        to be saved to file

        self.hystDelayVector_ps : Stage Delay in ps for TR Hysteresis
        self.hystDelayVector_mm : Stage Delay in mm for TR Hysteresis

        self.voltageVector : Voltage Values in Volt (V) - magnetic field

        self.fluenceVector : Fluence Values in mJ/cm^2 to be set
        """

        if not self.Stage_ReadFromFile:
            self.stageVector_ps = utilities.readStageFromGui(StageParams_ps)
            self.stageVector_mm = \
                self.stage.calculateStagemmFromps(self.stageVector_ps)
        else:
            self.stageVector_ps, self.saveVector = utilities.readStageFromFile()
            self.stageVector_mm = \
                self.stage.calculateStagemmFromps(self.stageVector_ps)

        if self.Voltage_ReadFromFile:
            self.voltageVector = utilities.readVoltageFromFile()
        else:
            self.voltageVector = [Parameters['Voltage']]

        if self.Fluence_ReadFromFile:
            self.fluenceVector = utilities.readFluenceFromFile()
        else:
            self.fluenceVector = [MeasParams['Fluence']]

        if self.HystDelay_ReadFromFile:
            self.hystDelayVector_ps = \
                utilities.readHysteresisDelayfromFile(
                    MeasParams['timeZero'])
            self.hystDelayVector_mm = \
                self.stage.calculateStagemmFromps(self.hystDelayVector_ps)
        else:
            delay = str(self.delay_HysteresisLine.toPlainText())
            self.hystDelayVector_ps = utilities.readHysteresisDelayfromGUI(
                delay, MeasParams['timeZero'])
            self.hystDelayVector_mm = self.stage.calculateStagemmFromps(
                self.hystDelayVector_ps)

    def setFluence(self, fluence):
        """
        Set Fluence Value.

        If GUI entry is "-1", nothing will be done.

        Else the calculation of the fluence will be called.
        From the given values the power to set is calculated and the waveplate
        is moved until the reference value in the diode is in range
        of the calibration value.

        close shutter during move of waveplate, to not "barbeque" the sample.

        IMPORTANT: referenceDiode Photodiode must be positioned in front of the
        shutter (so it is not influenced by closing or opening the shutter)

        :param fluence: float, goal value
        """

        if fluence != -1:
            MeasParams['Fluence'] = fluence
            self.currentFluence.setText(str(MeasParams['Fluence']))
            self.statusReport('Close Shutter...')
            self.moveShutter(True)
            self.statusReport('Set Fluence: ' + str(fluence))
            self.initializeWaveplate()
            flu = Fluence()
            power = flu.calculateFluence(fluence)
            angle, reference = flu.calculateWaveplateAngle(power)
            self.moveToReference(reference, angle)
            self.closeWaveplate()
            self.statusReport('Open Shutter...')
            self.moveShutter(False)

    def initializeHysteresisArray(self):
        """
        create the Voltage values for Hysteresis measurement:
        start at zero and stop at zero, but loop from minus to plus value

        check if the value used for Voltage limit is too high.
        Limit is hardcoded (should be changed with caution and thought!)

        :return: Array
        """

        step = float(HysteresisParameters['Amplitude']) / 100
        amplitude = float(HysteresisParameters['Amplitude'])
        loopField = int(HysteresisParameters['Loops'])

        if amplitude > 5.5:
            self.statusReport("Voltage to high! LImit is at 5.5 Volt")
            return

        if (amplitude + step) > 5.2:
            startArray = np.arange(0, amplitude, step)
            loopArray1 = np.arange(amplitude, -1*(amplitude), -1*step)
            loopArray2 = np.arange(-1*amplitude, amplitude, step)
            loopArray = np.concatenate([loopArray1, loopArray2])
            endArray = np.arange(amplitude, 0-step, -step)
        else:
            startArray = np.arange(0, amplitude+step, step)
            loopArray1 = np.arange(amplitude+step, -1*(amplitude+step), -1*step)
            loopArray2 = np.arange(-1*(amplitude+step), amplitude+step, step)
            loopArray = np.concatenate([loopArray1, loopArray2])
            endArray = np.arange((amplitude+step), 0-step, -step)

        Array = startArray
        for i in range(loopField):
            Array = np.concatenate([Array, loopArray])
        Array = np.concatenate([Array, endArray])

        resultlist = np.zeros(shape = (len(Array), 9))
        resultlist[:, 0] = Array
        return resultlist

    def createSaveFrame(self):
        """
        Create the Dataframe used for save "AllData_Reduced.txt"
        :return: self.AllData_Reduced
        """

        Length_for_array = LoopParams['Loops']*(len(self.stageVector_mm))*2*2
        zero_data = np.zeros(shape=(int(Length_for_array), 1))
        self.AllData_Reduced = pd.DataFrame(zero_data, columns=['Diodesignal'])

    def initializeTransientArrays(self):
        """
        Initialize all Lists, Arrays and Parameters used during measurement
        """

        # Lists for the averaged repeated values for each Diode, Chopped and
        # Unchopeed following each other. These Lists are saved in
        # "AllData_Reduced"
        self.DiffDiodeSignal = []
        self.MinusDiodeSignal = []
        self.PlusDiodeSignal = []
        self.RefDiodeSignal = []
        self.chopper = []
        self.StagePosition = []
        self.Looplist = []
        self.MagnetField = []

        # the Pump Probe Signal for each magnetic field direction
        self.PP_Plus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.PP_Minus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.MinusDiode_PP_Plus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.MinusDiode_PP_Minus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.PlusDiode_PP_Plus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.PlusDiode_PP_Minus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.RefDiode_PP_Plus = np.zeros(((int(len(self.stageVector_mm))), 2))
        self.RefDiode_PP_Minus = np.zeros(((int(len(self.stageVector_mm))), 2))

        # All Loops without averaging for easy access to loop changes visible 
        # during measurement
        self.diffDiode_PP_Plus_AllLoops = \
            np.zeros(((int(len(self.stageVector_mm))*LoopParams['Loops']+1), 2))
        self.diffDiode_PP_Minus_AllLoops = \
            np.zeros(((int(len(self.stageVector_mm))*LoopParams['Loops']+1), 2))

        # All Chopped and Unchopped values in arrays for each diode and
        # each magnetic field direction
        self.diffDiodeChopMinus = [0]*int(len(self.stageVector_mm))
        self.diffDiodeUnChopMinus = [0]*int(len(self.stageVector_mm))
        self.diffDiodeChopPlus = [0]*int(len(self.stageVector_mm))
        self.diffDiodeUnChopPlus = [0]*int(len(self.stageVector_mm))
        self.MinusDiodeChop_minus = [0]*int(len(self.stageVector_mm))
        self.MinusDiodeChop_plus = [0] * int(len(self.stageVector_mm))
        self.MinusDiodeUnChop_minus = [0] * int(len(self.stageVector_mm))
        self.MinusDiodeUnChop_plus = [0] * int(len(self.stageVector_mm))
        self.PlusDiodeChop_minus = [0] * int(len(self.stageVector_mm))
        self.PlusDiodeChop_plus = [0] * int(len(self.stageVector_mm))
        self.PlusDiodeUnChop_minus = [0] * int(len(self.stageVector_mm))
        self.PlusDiodeUnChop_plus = [0] * int(len(self.stageVector_mm))
        self.RefDiodeChop_minus = [0] * int(len(self.stageVector_mm))
        self.RefDiodeChop_plus = [0] * int(len(self.stageVector_mm))
        self.RefDiodeUnChop_minus = [0] * int(len(self.stageVector_mm))
        self.RefDiodeUnChop_plus = [0] * int(len(self.stageVector_mm))

        # Averaged Arrays for MOKE and PumpProbe for Diodes
        self.MOKE_Average = np.zeros((int(len(self.stageVector_mm)), 2))
        self.MinusDiode_Average = np.zeros((int(len(self.stageVector_mm)), 2))
        self.PlusDiode_Average = np.zeros((int(len(self.stageVector_mm)), 2))

    def createTimeStamp(self):
        """
        Main folder for data saving is named after Timestamp to ensure
        unique name tha tcannot be overriden accidently
        :return: self.timeStamp
        """

        self.timeStamp = str(datetime.now().strftime("%Y%m%d_%H%M%S"))

    def createFolder(self):
        """
        create Folder with timeStamp as name at given directory.
        Check if folder already exists

        :return: new folder created
        """

        self.statusReport('Create Folder')
        self.timeStampShow.setText(str(self.timeStamp))
        if not os.path.exists("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp):
            os.makedirs("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp)
            os.chdir("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ i) update loops & Main ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def Main(self):
        """
        Main Entry Point of measurement procedure.

        Hardware Initialization,
        preparing GUI plots (clear them and apply settings)
        calculate Measurement Parameters from User values

        Start main Update Loop for application
        """

        self.initializeAllHardware()
        self.calculateMeasurementParams()
        self.prepareGUI()

        # condition for creating folder only once and only when needed
        if self.SaveButton.isChecked() and not self.bFolderCreated:
            self.createFolder()
            self.bFolderCreated = True

        # loop for adjustement of overlapp:
        # MO Signal is measured at constant stage position behind t0
        if self.btn_Justage.isChecked():
            self.timerJustage = QtCore.QTimer()
            self.timerJustage.timeout.connect(self.updateAdjustement)
            self.timerJustage.start(20)
        else:
            # main update for time resolved measurements
            if self.timerJustage:
                self.timerJustage.stop()
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.update)
            self.timer.start(20)

    def updateAdjustement(self):
        """
        Update Loop for application if Button "Justage" is checked.

        Show MO contrast in plot as function of time, but not of stage position
        Stage is set to a position shortly after the timezero (GUI value)
        """

        self.initializeStage()
        position = self.stage.calcStageWay(MeasParams['timeZero'] +
                                           MeasParams['timeoverlapp'])
        self.stage.moveStage(position)
        self.measureMOContrast()

    def update(self):
        """
        Update Loop for application for Measurement of TR MOKE and TR Hysteresis
        """
        self.TotalProgresscount = 0
        self.CurrentNumber = 1
        self.initializeTransientArrays()

        for fluence in self.fluenceVector:
            # Card is initialized and closed frequently to prevent
            # Buffer overflow of Analog Output Card
            # (writing Voltage for amgetnic field)
            self.initializeNICard()
            self.setFluence(fluence)
            self.initializeStage()

            ### Hysteresis Measurements ###
            if self.Hysteresis_Check.isChecked():
                self.measureStaticHysteresis()
                for position in self.hystDelayVector_mm:
                    self.initializeNICard()
                    self.stage.moveStage(position)
                    self.measureHysteresis(position)
                    self.closeNICard()

            self.closeStage()
            self.closeNICard()

            ### MOKE Measurements ###
            if self.TimeResolved_Check.isChecked():
                for entry in self.voltageVector:
                    self.initializeNICard()
                    self.initializeStage()
                    self.measureTransient(entry)
                    self.closeStage()
                    self.closeNICard()
                    self.CurrentNumber += 1
                    self.calculateProgress(0)

        self.closeNICard()
        self.closeStage()
        self.timer.stop()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ j) measurement order ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def measureStaticHysteresis(self):
        """
        Measure Hysteresis without Pump Laser blocked by shutter
        """

        self.moveShutter(True)
        self.measureHysteresis('Static')

        # no useful information contained in the pumped value
        # - columns are deleted
        np.delete(self.resultList, 2, 1)
        if self.SaveButton.isChecked():
            self.saveOnlyHysteresis()
        self.closeStage()
        self.moveShutter(False)

    def measureHysteresis(self, position):
        """
        Measure a Hysteresis at a certain delay points.

        resultList
        :param position: Stage delay for naming the save file
        :return: self.resultList
        """

        self.statusReport('Measuring Hysteresis at ' + str(position))
        # set autofocus to Hysteresis Plot in GUI
        self.tabWidget_3.setCurrentIndex(2)
        self.Progresscount = 0

        try:
            self.resultList = self.initializeHysteresisArray()
        except TypeError:
            return
    
        for i in range(np.size(self.resultList[:, 0])):
            self.MeasurementCard.WriteValues(self.WritingTask,
                                             self.resultList[i, 0])
            attempt = 1

            # attempt used to repeat measurements that have an unequal amount of
            # chopped and unchopped values
            while attempt == 1:

                data = self.MeasurementCard.ReadValues_ai(self.MeasurementTask,
                                                          LoopParams)

                chopper = data[3]
                balancedDiode = data[0]
                plusDiode = data[1]
                minusDiode = data[4]
                referenceDiode = data[5]

                DiffDiodeChop, DiffDiodeUnChop, attempt = \
                    utilities.sortAfterChopperSanityCheck(balancedDiode, chopper)

                refchop, refunchop = \
                        utilities.sortAfterChopper(referenceDiode, chopper)

                DPlusChop, DPlusUnchop = \
                    utilities.sortAfterChopper(plusDiode, chopper)

                DMinusChop, DMinusUnchop = \
                    utilities.sortAfterChopper(minusDiode, chopper)

                #if not bDebug:
                #    self.checkIfLaserOff(refchop)

                QtGui.QApplication.processEvents()
                self.updateGUI()
                self.calculateProgress(1)
                self.TotalProgresscount += 1
                self.Progresscount += 1


            self.resultList[i, 1] = DiffDiodeChop
            self.resultList[i, 2] = DiffDiodeUnChop
            self.resultList[i, 3] = refchop
            self.resultList[i, 4] = refunchop
            self.resultList[i, 5] = DPlusChop
            self.resultList[i, 6] = DPlusUnchop
            self.resultList[i, 7] = DMinusChop
            self.resultList[i, 8] = DMinusUnchop

            self.updateHysteresis()

            # when value of position is not string (as it would be for static)
            # use the delay value in ps to name saving file
            # else use the original name ('static') for saving
            if isinstance(position, int) or isinstance(position, float):
                self.saveHysteresis(self.stage.calcLightWay(position))
            else:
                self.saveHysteresis(position)

        self.CurrentNumber += 1

    def measureMOContrast(self):
        """
        measure only MO contrast: stage is stationary at one position.
        It displays the MO contrast for the entered magnetic field in an
        infinity loop (if end if axid is reached it starts again).
        """

        self.tabWidget_3.setCurrentIndex(0)
        vector = np.arange(0, 501)
        self.PP_Plus = np.zeros((int(len(vector)), 2))
        self.currentAmplitude.setText(str(Parameters['Voltage']))
        self.MeasurementCard.WriteValues(
            self.WritingTask, Parameters['Voltage'])
        self.Stage_idx = int(vector[0])

        while True:
            repeat = 0

            while repeat < 1:
                data = self.MeasurementCard.ReadValues_ai(self.MeasurementTask,
                                                          LoopParams)
                QtGui.QApplication.processEvents()
                balancedDiode = data[0]
                chopper = data[3]
                # returned attempt shows if the length of the lists are
                # equal or not. if not: repeat the measurement.
                DiffDiodeChop, DiffDiodeUnChop, attempt = \
                        utilities.sortAfterChopperSanityCheck(balancedDiode, chopper)
                if attempt == 1:
                    repeat -= 1
                else:
                    self.updateGUI_Adjustement()
                    self.calculateMO(data, vector)

                repeat += 1
            self.Stage_idx += 1
            if self.Stage_idx == 500:
                self.Stage_idx = 0
        self.MeasurementCard.WriteValues(self.WritingTask, 0)

    def calculateMO(self, data, vector):
        """
        calculate the measured MO signal (Pump Probe for one magnetic field
        direction)

        :param data:
        :param vector:
        :return: self.PP_Plus
        """
        balancedDiode = data[0]
        chopper = data[3]

        DiffDiodeChop, DiffDiodeUnChop = \
            utilities.sortAfterChopper(balancedDiode, chopper)

        self.PP_Plus[self.Stage_idx, 0] = vector[int(self.Stage_idx)]
        self.PP_Plus[self.Stage_idx, 1] = DiffDiodeChop - DiffDiodeUnChop

    def measureTransient(self, entry):
        """
        measure time resolved trace of MOKE for applied voltage (entry)
        :param entry: Voltage for Time Trace
        :return:
        """

        self.tabWidget_3.setCurrentIndex(0)
        self.initializeTransientArrays()
        self.Progresscount = 0
        self.StartMeasurement = True

        Loop = 1
        self.PP_MinusIdx = 0
        self.PP_PlusIdx = 0

        Parameters['Voltage'] = float(entry)
        self.currentAmplitude.setText(str(Parameters['Voltage']))

        if self.SaveButton.isChecked():
            self.saveToMeasurementParameterList()
            
        while Loop < LoopParams['Loops']+1:
            Polarity_Field = 1
            self.MagneticFieldChange = 0
            self.statusReport('Loop: '+str(Loop))

            while self.MagneticFieldChange < 2:
                self.MeasurementCard.WriteValues(
                    self.WritingTask, Polarity_Field * Parameters['Voltage'])

                self.Stage_idx = 0
                self.Stage_idx2 = (len(self.stageVector_mm)-1)
                self.j, self.k = 0, 0
      
                for Stagemove in self.stageVector_mm:
                    self.stage.moveStage(Stagemove)
                    self.Pos_ps = self.stage.calcLightWay(Stagemove)
                    self.statusReport('Measure Transient: '
                                      'Stage Position in ps: '+str(self.Pos_ps))
                    repeat = 0
      
                    while repeat < 1:
                        data = self.MeasurementCard.ReadValues_ai(
                                self.MeasurementTask, LoopParams)
                        QtGui.QApplication.processEvents()

                        balancedDiode = data[0]
                        chopper = data[3]

                        # returned attempt shows if the length of the lists are 
                        # equal or not. if not: repeat the measurement.
                        DiffDiodeChop, DiffDiodeUnChop, attempt = \
                            utilities.sortAfterChopperSanityCheck(
                                balancedDiode, chopper)
                        if attempt == 1:
                            repeat -= 1
                        else:
                            self.updateGUI()
                            self.dataOperations(Loop, Polarity_Field, data)

                            if Loop == 1:
                                self.calculateFirstLoop()
                            else:
                                self.calculateLoopAverage()

                        repeat += 1
                        self.Progresscount += 1
                        self.TotalProgresscount += 1
                        self.calculateProgress(0)

                    self.Stage_idx += 1
                    self.Stage_idx2 -= 1

                self.MagneticFieldChange += 1
                Polarity_Field = Polarity_Field*(-1)

                # to save time: measure on return way of stage
                self.stageVector_mm = self.stageVector_mm[::-1]

            Loop += 1

            if self.SaveButton.isChecked():
                self.saveData()

        self.statusReport('Finished Transient Measurement')

        if self.SaveButton.isChecked():
            self.saveData()
        self.MeasurementCard.WriteValues(self.WritingTask, 0)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ k) Data Analysis ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def calculateLoopAverage(self):
        """
        Calculate Loop Average for
        - MOKE_Average
        - MinusDiode_Average
        - PlisDiode_Average
        """

        self.MOKE_Average[:, 1] = (self.MOKE_Average[:, 1] +
                                   (self.PP_Plus[:, 1] - self.PP_Minus[:, 1]))/2
        self.MinusDiode_Average[:, 1] = (self.MinusDiode_Average[:, 1] +
                                         (self.MinusDiode_PP_Minus[:, 1] +
                                          self.MinusDiode_PP_Plus[:, 1]) / 2)/2
        self.PlusDiode_Average[:, 1] = (self.PlusDiode_Average[:, 1] +
                                        (self.PlusDiode_PP_Minus[:, 1] +
                                         self.PlusDiode_PP_Plus[:, 1]) / 2)/2

    def calculateFirstLoop(self):
        """
        Set first column to Stagevector
        Calculate MOKE and Diodes for first loop
        """

        self.MOKE_Average[:, 0] = self.stageVector_ps
        self.MinusDiode_Average[:, 0] = self.stageVector_ps
        self.PlusDiode_Average[:, 0] = self.stageVector_ps

        self.MOKE_Average[:, 1] = self.PP_Plus[:, 1] - self.PP_Minus[:, 1]
        self.MinusDiode_Average[:, 1] = (self.MinusDiode_PP_Minus[:, 1] +
                                         self.MinusDiode_PP_Plus[:, 1]) / 2
        self.PlusDiode_Average[:, 1] = (self.PlusDiode_PP_Minus[:, 1] +
                                        self.PlusDiode_PP_Plus[:, 1]) / 2

    def dataOperations(self, Loop, Polarity_Field, data):
        """
        sort data according to chopper and Magnetic Field direction

        :param Loop, Polarity_Field, data
        """

        balancedDiode = data[0]
        DiodeMinus = data[1]
        chopper = data[3]
        DiodePlus = data[4]
        referenceDiode = data[5]

        DiffDiodeChop, DiffDiodeUnChop = \
            utilities.sortAfterChopper(balancedDiode, chopper)
        ReferenceChop, ReferenceUnchop = \
            utilities.sortAfterChopper(referenceDiode, chopper)
        MinusDiodeChop, MinusDiodeUnChop = \
            utilities.sortAfterChopper(DiodeMinus, chopper)
        PlusDiodeChop, PlusDiodeUnChop = \
            utilities.sortAfterChopper(DiodePlus, chopper)

        if Polarity_Field < 0:
            self.calculateMinusMagneticField(DiffDiodeChop, DiffDiodeUnChop,
                                             ReferenceChop, ReferenceUnchop,
                                             MinusDiodeChop, MinusDiodeUnChop,
                                             PlusDiodeChop, PlusDiodeUnChop,
                                             Loop, data)
        else:
            self.calculatePlusMagneticField(DiffDiodeChop, DiffDiodeUnChop,
                                             ReferenceChop, ReferenceUnchop,
                                             MinusDiodeChop, MinusDiodeUnChop,
                                             PlusDiodeChop, PlusDiodeUnChop,
                                            Loop, data)
        if Loop == 1:
            self.calculatePPFirstLoop(Polarity_Field)
        else:
            self.calculatePPAverageLoop(Polarity_Field)

    def calculatePPAverageLoop(self, Polarity_Field):
        """
        Calculate Values for Pump-Probe Measurements depending on MagneticField
        Average all Loops
        :param Polarity_Field:
        :return:

        self.PP_Plus
        self.MinusDiode_PP_Plus
        self.PlusDiode_PP_Plus
        self.RefDiode_PP_Plus

        OR

        self.PP_Minus
        self.MinusDiode_PP_Minus
        self.PlusDiode_PP_Minus
        self.RefDiode_PP_Minus
        """

        if Polarity_Field > 0:
            PP_Plus_value = \
                (self.diffDiodeChopPlus[self.Stage_idx] -
                 self.diffDiodeUnChopPlus[self.Stage_idx])
            self.PP_Plus[self.Stage_idx, 1] = \
                (self.PP_Plus[self.Stage_idx, 1] +
                 PP_Plus_value) / 2

            Minus_PP_Plus_value = \
                (self.MinusDiodeChop_plus[self.Stage_idx] -
                 self.MinusDiodeUnChop_plus[self.Stage_idx])
            self.MinusDiode_PP_Plus[self.Stage_idx, 1] = \
                (self.MinusDiode_PP_Plus[self.Stage_idx, 1] +
                 Minus_PP_Plus_value) / 2

            Plus_PP_Plus_value = \
                (self.PlusDiodeChop_plus[self.Stage_idx] -
                 self.PlusDiodeUnChop_plus[self.Stage_idx])
            self.PlusDiode_PP_Plus[self.Stage_idx, 1] = \
                (self.PlusDiode_PP_Plus[self.Stage_idx, 1] +
                 Plus_PP_Plus_value) / 2

            Refvalue = \
                (self.RefDiodeChop_plus[self.Stage_idx] -
                 self.RefDiodeUnChop_plus[self.Stage_idx])
            self.RefDiode_PP_Plus[self.Stage_idx, 1] = \
                (self.RefDiode_PP_Plus[self.Stage_idx, 1] +
                 Refvalue) / 2

        else:
            PP_Minus_value = \
                (self.diffDiodeChopMinus[self.Stage_idx2] -
                 self.diffDiodeUnChopMinus[self.Stage_idx2])
            self.PP_Minus[self.Stage_idx, 1] = \
                (self.PP_Minus[self.Stage_idx, 1] +
                 PP_Minus_value) / 2

            Minus_PP_Minus_value = \
                (self.MinusDiodeChop_minus[self.Stage_idx] -
                 self.MinusDiodeUnChop_minus[self.Stage_idx])
            self.MinusDiode_PP_Minus[self.Stage_idx, 1] = \
                (self.MinusDiode_PP_Minus[self.Stage_idx, 1] +
                 Minus_PP_Minus_value) / 2

            Plus_PP_Minus_value = \
                (self.PlusDiodeChop_minus[self.Stage_idx] -
                 self.PlusDiodeUnChop_minus[self.Stage_idx])
            self.PlusDiode_PP_Minus[self.Stage_idx, 1] = \
                (self.PlusDiode_PP_Minus[self.Stage_idx, 1] +
                 Plus_PP_Minus_value) / 2

            Refvalue = \
                (self.RefDiodeChop_minus[self.Stage_idx] -
                 self.RefDiodeUnChop_minus[self.Stage_idx])
            self.RefDiode_PP_Minus[self.Stage_idx, 1] = \
                (self.RefDiode_PP_Minus[self.Stage_idx, 1] +
                 Refvalue) / 2

    def calculatePPFirstLoop(self, Polarity_Field):
        """
        S Values for Pump-Probe Measurements depending on MagneticField
        for first loop
        :param Polarity_Field:
        :return:

        self.PP_Plus
        self.MinusDiode_PP_Plus
        self.PlusDiode_PP_Plus
        self.RefDiode_PP_Plus

        OR

        self.PP_Minus
        self.MinusDiode_PP_Minus
        self.PlusDiode_PP_Minus
        self.RefDiode_PP_Minus
        """
        if Polarity_Field > 0:
            self.PP_Plus[self.Stage_idx, 0] = self.Pos_ps
            self.PP_Plus[self.Stage_idx, 1] = \
                self.diffDiodeChopPlus[self.Stage_idx] - \
                self.diffDiodeUnChopPlus[self.Stage_idx]

            self.MinusDiode_PP_Plus[self.Stage_idx, 0] = self.Pos_ps
            self.MinusDiode_PP_Plus[self.Stage_idx, 1] = \
                self.MinusDiodeChop_plus[self.Stage_idx] -\
                self.MinusDiodeUnChop_plus[self.Stage_idx]

            self.PlusDiode_PP_Plus[self.Stage_idx, 0] = self.Pos_ps
            self.PlusDiode_PP_Plus[self.Stage_idx, 1] = \
                self.PlusDiodeChop_plus[self.Stage_idx] -\
                self.PlusDiodeUnChop_plus[self.Stage_idx]

            self.RefDiode_PP_Plus[self.Stage_idx, 0] = self.Pos_ps
            self.RefDiode_PP_Plus[self.Stage_idx, 1] = \
                self.RefDiodeChop_plus[self.Stage_idx] -\
                self.RefDiodeUnChop_plus[self.Stage_idx]

        else:
            self.PP_Minus[self.Stage_idx2, 0] = self.Pos_ps
            self.PP_Minus[self.Stage_idx2, 1] = \
                self.diffDiodeChopMinus[self.Stage_idx] - \
                self.diffDiodeUnChopMinus[self.Stage_idx]

            self.MinusDiode_PP_Minus[self.Stage_idx2, 0] = self.Pos_ps
            self.MinusDiode_PP_Minus[self.Stage_idx2, 1] = \
            self.MinusDiodeChop_minus[self.Stage_idx] - \
            self.MinusDiodeUnChop_minus[self.Stage_idx]

            self.PlusDiode_PP_Minus[self.Stage_idx2, 0] = self.Pos_ps
            self.PlusDiode_PP_Minus[self.Stage_idx2, 1] = \
            self.PlusDiodeChop_minus[self.Stage_idx] - \
            self.PlusDiodeUnChop_minus[self.Stage_idx]

            self.RefDiode_PP_Minus[self.Stage_idx2, 0] = self.Pos_ps
            self.RefDiode_PP_Minus[self.Stage_idx2, 1] = \
            self.RefDiodeChop_minus[self.Stage_idx] - \
            self.RefDiodeUnChop_minus[self.Stage_idx]

    def calculatePlusMagneticField(self, DiffDiodeChop, DiffDiodeUnChop,
                                   ReferenceChop, ReferenceUnchop,
                                   MinusDiodeChop, MinusDiodeUnChop,
                                   PlusDiodeChop, PlusDiodeUnChop, Loop, data):
        """
        Sort all values in their list and Position in the general dataframe
        for the positive magnetic field

        :param DiffDiodeChop:
        :param DiffDiodeUnChop:
        :param ReferenceChop:
        :param ReferenceUnchop:
        :param MinusDiodeChop:
        :param MinusDiodeUnChop:
        :param PlusDiodeChop:
        :param PlusDiodeUnChop:
        :param Loop:
        :param data:
        :return:
        """
        self.diffDiodeChopPlus[self.k] = DiffDiodeChop
        self.diffDiodeUnChopPlus[self.k] = DiffDiodeUnChop
        self.MinusDiodeChop_plus[self.k] = MinusDiodeChop
        self.MinusDiodeUnChop_plus[self.k] = MinusDiodeUnChop
        self.PlusDiodeChop_plus[self.k] = PlusDiodeChop
        self.PlusDiodeUnChop_plus[self.k] = PlusDiodeUnChop
        self.RefDiodeChop_plus[self.k] = ReferenceChop
        self.RefDiodeUnChop_plus[self.k] = ReferenceUnchop

        self.DiffDiodeSignal.extend([DiffDiodeChop, DiffDiodeUnChop])
        self.MinusDiodeSignal.extend([MinusDiodeChop, MinusDiodeUnChop])
        self.PlusDiodeSignal.extend([PlusDiodeChop, PlusDiodeUnChop])
        self.RefDiodeSignal.extend([ReferenceChop, ReferenceUnchop])

        self.diffDiode_PP_Plus_AllLoops[self.PP_PlusIdx, 0] = self.Pos_ps
        self.diffDiode_PP_Plus_AllLoops[self.PP_PlusIdx, 1] = DiffDiodeChop - \
                                                         DiffDiodeUnChop

        self.chopper.extend([1, 0])
        self.MagnetField.extend(data[2][0:2])
        self.StagePosition.extend(
            [self.Pos_ps, self.Pos_ps])
        self.Looplist.extend([Loop, Loop])

        self.k += 1
        self.PP_PlusIdx += 1

    def calculateMinusMagneticField(self, DiffDiodeChop, DiffDiodeUnChop,
                                   ReferenceChop, ReferenceUnchop,
                                   MinusDiodeChop, MinusDiodeUnChop,
                                   PlusDiodeChop, PlusDiodeUnChop, Loop, data):
        """
        Sort all values in their list and Position in the general dataframe
        for the negative magnetic field

        :param DiffDiodeChop:
        :param DiffDiodeUnChop:
        :param ReferenceChop:
        :param ReferenceUnchop:
        :param MinusDiodeChop:
        :param MinusDiodeUnChop:
        :param PlusDiodeChop:
        :param PlusDiodeUnChop:
        :param Loop:
        :param data:
        :return:
        """

        self.diffDiodeChopMinus[self.j] = DiffDiodeChop
        self.diffDiodeUnChopMinus[self.j] = DiffDiodeUnChop
        self.MinusDiodeChop_minus[self.j] = MinusDiodeChop
        self.MinusDiodeUnChop_minus[self.j] = MinusDiodeUnChop
        self.PlusDiodeChop_minus[self.j] = PlusDiodeChop
        self.PlusDiodeUnChop_minus[self.j] = PlusDiodeUnChop
        self.RefDiodeChop_minus[self.j] = ReferenceChop
        self.RefDiodeUnChop_minus[self.j] = ReferenceUnchop

        self.DiffDiodeSignal.extend([DiffDiodeChop, DiffDiodeUnChop])
        self.MinusDiodeSignal.extend([MinusDiodeChop, MinusDiodeUnChop])
        self.PlusDiodeSignal.extend([PlusDiodeChop, PlusDiodeUnChop])
        self.RefDiodeSignal.extend([ReferenceChop, ReferenceUnchop])

        self.diffDiode_PP_Minus_AllLoops[self.PP_MinusIdx, 0] = self.Pos_ps
        self.diffDiode_PP_Minus_AllLoops[self.PP_MinusIdx, 1] = DiffDiodeChop - \
                                                           DiffDiodeUnChop

        self.chopper.extend([1, 0])
        self.MagnetField.extend(data[2][0:2])
        self.StagePosition.extend([self.Pos_ps, self.Pos_ps])
        self.Looplist.extend([Loop, Loop])

        self.j += 1
        self.PP_MinusIdx += 1

    def updateGUI(self):
        """
        update the plots
        """

        self.updatePumpOnly()
        self.updateProbeOnly()
        self.updatePP1()
        self.updatePP2()
        self.updateMOKE()
        self.updateIntensity()
        self.ui.currentMeasurement_Label.setText(str(self.CurrentNumber))

    def updateGUI_Adjustement(self):
        """
        update the plot during adjustement
        """

        self.updateMOKE()

    def statusReport(self, status):
        """
        Write status in console and in statusbar of GUI
        :param status: Message for user
        """

        print(status)
        self.statusBar().showMessage(status)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ l) Settings and Update of Plots ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def plotPP1(self):
        """
        Settings for plotting the PumpProbe Signal for
        Magnetic Field direction 1
        Plot_All: all Loops on top ov each other
        Plot_Average: plot the average
        """

        self.curve = \
            self.PP_Signal1_PlotAverage.getPlotItem().plot(pen=(215, 128, 26))
        self.PP_Signal1_PlotAverage.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])
        self.PP_Signal1_PlotAverage.getPlotItem().addLine(
            y=0, pen=(215, 128, 26, 125))

        self.curve_all = \
            self.PP_Signal1_PlotAll.getPlotItem().plot(pen=(215, 128, 26))
        self.PP_Signal1_PlotAll.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])
        self.PP_Signal1_PlotAll.getPlotItem().addLine(
            y=0, pen=(215, 128, 26, 125))

    def updatePP1(self):
        """
        update PumpProbe Signal Plot 1
        """

        self.PP_Signal1_PlotAll.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])
        self.PP_Signal1_PlotAll.getPlotItem().enableAutoRange(
            axis=0, enable=False)
        self.curve.setData(self.PP_Plus)
        self.curve_all.setData(self.diffDiode_PP_Plus_AllLoops)

    def plotPP2(self):
        """
        Settings for plotting the PumpProbe Signal for
        Magnetic Field direction 2
        Plot_All: all Loops on top ov each other
        Plot_Average: plot the average
        """

        self.curve2 = \
            self.PP_Signal2_PlotAverage.getPlotItem().plot(pen=(215, 128, 26))
        self.PP_Signal2_PlotAverage.getPlotItem().addLine(
            y=0, pen=(215, 128, 26, 125))
        self.PP_Signal2_PlotAverage.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])

        self.curve2_all = \
            self.PP_Signal2_PlotAll.getPlotItem().plot(pen=(215, 128, 26))
        self.PP_Signal2_PlotAll.getPlotItem().addLine(
            y=0, pen=(215, 128, 26, 125))
        self.PP_Signal2_PlotAll.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])

    def updatePP2(self):
        """
        update PumpProbe Signal Plot 2
        """

        self.PP_Signal2_PlotAll.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])
        self.PP_Signal2_PlotAll.getPlotItem().enableAutoRange(
            axis=0, enable=False)
        self.curve2.setData(self.PP_Minus)
        self.curve2_all.setData(self.diffDiode_PP_Minus_AllLoops)

    def plotPumpOnly(self):
        """
        Settings for plotting the PumpProbe Signal for
        Magnetic Field direction 2
        Plot_All: all Loops on top ov each other
        Plot_Average: plot the average
        """

        self.curvePumpOnlyPlus = \
            self.PumpOnly_Plot.getPlotItem().plot(pen=(215, 128, 26))
        self.curvePumpOnlyMinus = \
            self.PumpOnly_Plot.getPlotItem().plot(pen=(215, 128, 26))

    def updatePumpOnly(self):
        """
        update PumpProbe Signal Plot 2
        """

        self.curvePumpOnlyPlus.setData(self.diffDiodeChopPlus)
        self.curvePumpOnlyMinus.setData(self.diffDiodeChopMinus)

    def plotProbeOnly(self):
        """
        Settings for plotting the PumpProbe Signal for
        Magnetic Field direction 2
        Plot_All: all Loops on top ov each other
        Plot_Average: plot the average
        """

        self.curveProbeOnlyPlus = \
            self.ProbeOnly_Plot.getPlotItem().plot(pen=(215, 128, 26))
        self.curveProbeOnlyMinus = \
            self.ProbeOnly_Plot.getPlotItem().plot(pen=(215, 128, 26))

    def updateProbeOnly(self):
        """
        update PumpProbe Signal Plot 2
        """

        self.curveProbeOnlyPlus.setData(self.diffDiodeUnChopPlus)
        self.curveProbeOnlyMinus.setData(self.diffDiodeUnChopMinus)


    def plotMOKE(self):
        """
        Settings for plotting the MOKE Signal
        Plot_Average: plot the average
        Add Infinite Line add MO = 0
        Add Infinite Line for tha current stage Position
        """

        self.curve3 =\
            self.MOKE_Average_Plot.getPlotItem().plot(pen=(215, 128, 26))
        self.MOKE_Average_Plot.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])
        self.MOKE_Average_Plot.getPlotItem().addLine(
            y=0, pen=(215, 128, 26, 125))
        self.line2 = self.MOKE_Average_Plot.getPlotItem().addLine(
                x=self.Pos_ps, pen=(38, 126, 229, 125), movable = True)

    def updateMOKE(self):
        """
        Update the main plot in the MOKE Tab. Either with transient MOKE or
        static MO Signal at certain stage delay.
        """
        if self.btn_Justage.isChecked():
            self.MOKE_Average_Plot.getPlotItem().setRange(
                xRange=[0, 500])
            self.curve3.setData(self.PP_Plus)
        else:
            self.curve3.setData(self.MOKE_Average)
            self.line2.setValue(self.Pos_ps)
            
    def plotIntensity(self):
        """
        Settings for Relative Intensity: plot both balanced diodes as well as
        there difference with legend
        """

        self.IntensityPlot.getPlotItem().addLegend()
        self.MinusDiodeCurve = self.IntensityPlot.getPlotItem().plot(
            pen=(38, 126, 229, 125), name="Minus Diode")
        self.PlusDiodeCurve = self.IntensityPlot.getPlotItem().plot(
            pen=(229, 38, 222, 125), name="Plus Diode")
        self.AverageDiodeCurve = self.IntensityPlot.getPlotItem().plot(
            pen=(215, 128, 26), name="Difference Diode")
        self.IntensityPlot.getPlotItem().setRange(
            xRange=[self.stageVector_ps[0], max(self.stageVector_ps)])
        self.IntensityPlot.getPlotItem().addLine(
            y=0, pen=(215, 128, 26, 125))

    def updateIntensity(self):
        """
        update Intensity from balanced Photodiode
        """

        self.MinusDiodeCurve.setData(self.MinusDiode_Average)
        self.PlusDiodeCurve.setData(self.PlusDiode_Average)
        self.AverageDiodeCurve.setData((self.MinusDiode_Average +
                                        self.PlusDiode_Average)/2)

    def plotHysteresis(self):
        """
        Plot Hysteresis,
        blue: unpumped Hysteresis
        orange: punped Hysteresis
        """

        self.curve5 = self.HysteresisPlot.getPlotItem().plot(
            pen=(215, 128, 26))
        self.curve6 = self.HysteresisPlot.getPlotItem().plot(
            pen=(38, 126, 229))
        self.HysteresisPlot.getPlotItem().setRange(
            xRange=(HysteresisParameters['Amplitude'],
                    -HysteresisParameters['Amplitude']))

    def updateHysteresis(self):
        """
        update Hysteresis
        """

        self.curve5.setData(self.resultList[:, 0], self.resultList[:, 1])
        self.curve6.setData(self.resultList[:, 0], self.resultList[:, 2])

    def calculateNumberOfMeasurements(self):
        """
        calculate total number of measurements including every Hysteresis and
        Time Resolved MOKE
        :return: TotalNumber
        """

        if self.Hysteresis_Check.isChecked():
            # timeresolved + static measurement
            hystNumber = len(self.hystDelayVector_mm) + 1
        else:
            hystNumber = 0

        TotalNumber = hystNumber + \
                      len(self.fluenceVector)*len(self.voltageVector)

        self.ui.TotalMeasurement_Label.setText(str(TotalNumber))

    def calculateProgress(self, meas):
        """
        calculate the progress based on total Number for all measuremenss
        (small bar) and the current measurement (large bar)

        :param: meas : describes the measurement "mode", necessary because total
        percentage of single measurement is different for Transient and
        Hysteresis measurements

        :return: Percentage for Progress Bars
        :return: Number of Measurement
        """

        MultiplyMagnetfield = 2
        MultiplyChopper = 2

        if self.Hysteresis_Check.isChecked():
            StepsForHysteresis = np.size(self.resultList[:, 0])
            PHysteresis = (len(self.hystDelayVector_mm) + 1) * StepsForHysteresis
        else:
            PHysteresis = 0

        PTransient = LoopParams['Loops'] * (len(self.stageVector_mm)) *\
            MultiplyMagnetfield * len(self.fluenceVector) * \
                     len(self.voltageVector)

        # Calculation of all Progess
        PTotalOverall = PTransient + PHysteresis
        P_momentTotal = self.TotalProgresscount
        PercentageTotal = int((P_momentTotal * 100) / PTotalOverall)
        self.progressBar2.setValue(PercentageTotal)

        # Calculation of single measurement progress
        # meas = 0: Transient is measured
        if meas == 0:
            PTotal = LoopParams['Loops'] * (len(self.stageVector_mm)) *\
            MultiplyMagnetfield
        # meas = 1: Hysteresis is measured
        if meas == 1:
            PTotal = StepsForHysteresis
        P_moment = self.Progresscount
        Percentage = int((P_moment*100)/PTotal)
        self.progressBar.setValue(Percentage)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ m) Save Data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def saveData(self):
        """

        Save all data (repeats are averaged)
        Choppervalue gets rounded to 0 and 1, measured at the threshold of 2V
        (max: 5V, min: 0V)

        File Structure of Directories is as follows:

        - TimeStamp
            |- Static
                |- Static Hysteresis
            |- Fluence Values
                |- Hysteresis
                    |- TR Hysteresis textfiles: "Fluence"_"Sample"_"Time"ps.txt
                |- Voltage Values
                    |- Hyteresis_Measurement_Parameters.txt
                    |- AllData_Reduced.txt
                    |- MOKE_Average.txt

        """
        self.statusReport('Saving...')

        Chopvalue = list(self.chopper)
        for idx, val in enumerate(self.chopper):
            if val < 2.0:
                Chopvalue[idx] = 0
            else:
                Chopvalue[idx] = 1

        self.AllData_Reduced['Diodesignal'] = \
            utilities.listLength(self.DiffDiodeSignal, self.AllData_Reduced)

        self.AllData_Reduced['MinusDiode'] = \
            utilities.listLength(self.MinusDiodeSignal, self.AllData_Reduced)

        self.AllData_Reduced['PlusDiode'] = \
            utilities.listLength(self.PlusDiodeSignal, self.AllData_Reduced)

        self.AllData_Reduced['ReferenzDiode'] = \
            utilities.listLength(self.RefDiodeSignal, self.AllData_Reduced)

        self.AllData_Reduced['chopper'] = \
            utilities.listLength(self.chopper, self.AllData_Reduced)

        self.AllData_Reduced['StagePosition'] = \
            utilities.listLength(self.StagePosition, self.AllData_Reduced)

        self.AllData_Reduced['Loops'] = \
            utilities.listLength(self.Looplist, self.AllData_Reduced)

        self.AllData_Reduced['MagneticField'] = \
            utilities.listLength(self.MagnetField, self.AllData_Reduced)

        if not os.path.exists("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +
                              "\\Fluence\\" +
                              str(MeasParams['Fluence'])+
                              "\\"+self.currentAmplitude.text()):
            os.makedirs("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +
                        "\\Fluence\\" + str(MeasParams['Fluence']) +
                        "\\"+self.currentAmplitude.text())

        os.chdir("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +
                 "\\Fluence\\" + str(MeasParams['Fluence']) +
                 "\\"+self.currentAmplitude.text())

        self.saveParameters()

        self.AllData_Reduced.to_csv('AllData_Reduced.txt', sep="\t")
        np.savetxt('MOKE_Average.txt', self.MOKE_Average, delimiter='\t')

        self.MOKE_Average_Plot.getPlotItem().enableAutoRange()
        exporter = \
            exporters.ImageExporter(self.MOKE_Average_Plot.plotItem)
        exporter.parameters()['width'] = int(2000)
        exporter.export('MOKE_AveragePlot.png')

        self.PP_Signal1_PlotAverage.getPlotItem().enableAutoRange()
        exporter2 = \
            exporters.ImageExporter(self.PP_Signal1_PlotAverage.plotItem)
        exporter2.parameters()['width'] = 2000
        exporter2.export('PumpProbeSignal_Averaged_1.png')

        self.PP_Signal2_PlotAverage.getPlotItem().enableAutoRange()
        exporter3 = \
            exporters.ImageExporter(self.PP_Signal2_PlotAverage.plotItem)
        exporter3.parameters()['width'] = 2000
        exporter3.export('PumpProbeSignal_Averaged_2.png')

        self.PP_Signal1_PlotAll.getPlotItem().enableAutoRange()
        exporter4 = \
            exporters.ImageExporter(self.PP_Signal1_PlotAll.plotItem)
        exporter4.parameters()['width'] = 2000
        exporter4.export('PumpProbeSignal_All_1.png')

        self.PP_Signal2_PlotAll.getPlotItem().enableAutoRange()
        exporter5 = \
            exporters.ImageExporter(self.PP_Signal2_PlotAll.plotItem)
        exporter5.parameters()['width'] = 2000
        exporter5.export('PumpProbeSignal_All_2.png')

        self.statusReport('Saved!')

    def saveHysteresis(self, position):
        """
        if the directory does not exit already: create it
        save hysteresis
        """

        if not os.path.exists("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +
                              "\\Fluence\\" +
                              str(MeasParams['Fluence'])+
                              "\\Hysteresis"):
            os.makedirs("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +
                        "\\Fluence\\" + str(MeasParams['Fluence']) +
                        "\\Hysteresis")

        os.chdir("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp + "\\Fluence\\" +
                 str(MeasParams['Fluence'])+"\\Hysteresis")

        np.savetxt(str(MeasParams['Fluence']) + 'mJcm2_' +
                   str(MeasParams['sampleName'])+"_" +
                   str(position)+'ps.txt',
                   self.resultList, delimiter='\t',
                   header='#Voltage (V)\t Balanced Pumped\t Balanced Umpumed\t '
                          'referenceDiode closed\t referenceDiode\t '
                          'Diode+ Pumped\t Diode+ Unpumped\t Diode- Pumped\t '
                          'Diode- Unpumped')

    def saveOnlyHysteresis(self):
        """
        if the directory does not exit already: create it
        Save the simple Hysteresis with only two columns (static Hysteresis)
        """

        if not os.path.exists(
                        "D:\\Data\\MOKE_PumpProbe\\" +
                        self.timeStamp +"\Fluence\\" +
                         "\\Static\\"):
            os.makedirs("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +
                        "\Fluence\\" +
                         "\\Static\\")
        os.chdir("D:\\Data\\MOKE_PumpProbe\\" + self.timeStamp +"\Fluence\\" +
                         "\\Static\\")
        np.savetxt(str(MeasParams['sampleName']) + '_NoLaser.txt',
                   self.resultList, delimiter='\t',
                   header='#Voltage (V)\t Value ()')

    def saveParameters(self):
        """
        Save all Parameters set or used in the measurement in the Parameter file
        """

        name = 'Hyteresis_Measurement_Parameters.txt'
        file = open(name, 'w')   # Trying to create a new file or open one
        file.write("Voltage: {} V\n".format(str(Parameters['Voltage'])))
        file.write("Loops: {} \n".format(str(LoopParams['Loops'])))
        file.write("Measurementpoints: {} \n".format(
            str(LoopParams['MeasurementPoints'])))
        file.write("Set Fluenz: {} \n".format(
            str(MeasParams['Fluence'])))
        file.write("TimeZero: {} \n".format(
            str(MeasParams['timeZero'])))
        file.write("Pump-Angle: {} \n".format(
            str(MeasParams['angle'])))
        file.write("Samplename: {} \n".format(
            str(MeasParams['sampleName'])))

        if not self.Stage_ReadFromFile:
            file.write("StartPoint: {} ps\n".format(
                str(StageParams_ps['StartPoint'])))
            file.write("End Point: {} ps\n".format(
                str(StageParams_ps['EndPoint'])))
            file.write("Stepwidth: {} ps\n".format(
                str(StageParams_ps['StepWidth'])))
            file.write("Stage Velocity: {} \n".format(
                str(Stage_SpeedParams['Velocity'])))
            file.write("Stage Acceleration: {} \n".format(
                str(Stage_SpeedParams['Acceleration'])))

        if self.Stage_ReadFromFile:
            file.write("Start \t Stop \t Stepwidth ps\n")
            for idx, val in enumerate(self.saveVector):
                entry = '    '.join(str(e) for e in self.saveVector[idx])
                file.write("{}\n".format(entry))

        if self.Hysteresis_Check.isChecked():
            file.write("StartPoint: {} ps\n".format(
                str(HysteresisParameters['Stepwidth'])))
            file.write("Amplitude: {} ps\n".format(
                str(HysteresisParameters['Amplitude'])))
            file.write("@StageDelay")
            for idx, val in enumerate(self.hystDelayVector_ps):
                entry = '    '.join(str(val))
                file.write("{}\n".format(entry))

        file.close()

    def saveToMeasurementParameterList(self):
        """
        write important parameters in measurement list for easy choise of
        Measurements and Labbookentry creation
        """
        
        date, time = utilities.partTimeStamp(self.timeStamp)
        FWHMx, FWHMy = utilities.readFWHMfromBeamprofile()
        file = utilities.createOrOpenMeasurementParameterList()
        file.write(date+'\t')
        file.write(time+'\t')
        file.write(format(str(Parameters['Voltage']))+'\t')
        file.write(format(str(MeasParams['Fluence']))+'\t')
        file.write('300'+'\t')
        file.write(format(str(MeasParams['timeZero']))+'\t')
        file.write(FWHMx+'\t')
        file.write(FWHMy+'\t')
        file.write(format(str(MeasParams['angle']))+'\t')
        file.write(format(str(MeasParams['sampleName']))+'\t')

        file.write('\n')
        file.close()

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
