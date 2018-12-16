#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SpectroPumpProbe.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
PyQt Version: 5.9.2
Pyqtgraph Version: 0.10.1

Pump Probe Measurement Program with Ocean Optics Spectrometer,
Newport XPS stage.

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
from PyQt5 import QtGui, uic
import PyQt5
from PyQt5.QtWidgets import QApplication, QMessageBox
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtCore
import os
from datetime import datetime
import pyqtgraph.exporters as exporters

# Imports of own modules
from modules.StageCommunication_V2 import StageCommunication
from modules.OceanOpticsCommunication_V1 import OOSpectrometer


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Global Variables and Dictionaries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

MeasureParameters = {'Name': '', 'Loops': 1, 'Average': 30, 'IntTime': 50.0,
                     'Comment': '', 'Fluence': -1, 'Power': -1}
Stage_SpeedParams = {'Velocity': 20, 'Acceleration': 20}
StageParams_ps = {'StartPoint': 0.0, 'EndPoint': 10.0, 'StepWidth': 5.0}
StageParams_mm = {}
Offset_mm = 75
NumberOfPixelsToSkip = 5


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ Main Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MyWindow(PyQt5.QtWidgets.QMainWindow):
    """
    Main Class handeling data, GUI and Hardware Communication

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

    stage = None
    spectro = None
    timer = None
    stageVector_ps = None
    stageVector_mm = None
    allSpectra = None

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        # load GUI from .ui file (created in QtDesigner)
        self.ui = uic.loadUi('UI_Files/SpectroPumpProbe_V2.ui', self)
        pg.setConfigOptions(antialias=True)

        # Variables used for Tracking Initialization Status and GUI Choices
        self.StartMeasurement = False
        self.Initialize = False
        self.StageParams_mm = None
        self.stageIni = 0

        # Connect Buttons with Function calls
        self.StartButton.clicked.connect(self.Main)
        self.StopButton.clicked.connect(self.close)

        # show GUI
        self.show()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # ~~~ b) Events ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:

            if self.StartMeasurement:
                self.SaveData()
                self.timer.stop()

            if self.Initialize:
                self.stage.closeStage()

            event.accept()

        else:
            event.ignore()

    def initializeStage(self):
        """
        Initialize stage communication with XPS Newport Controller
        Strings of stage Name ('GROUP2', 'POSITIONER') are set in the
        Web Interface of the XPS Controller.
        Also the stage offset determined by length of stage and the number of
        times the light crosses the stage is hardcoded, needs to be changed
        in the code for each setup.

        StageSpeedParams : can be set to 0, than default values will be used

        self.stageIni : Boolean to make sure it is initialized only once at
        the time
        :return: stage object
        """

        self.statusReport("Initialize stage")
        if self.stageIni == 1:
            return
        self.stageIni = 1
        self.stage = StageCommunication('GROUP2', 'POSITIONER')
        self.stage.connectStage()
        self.stage.setStageParams(Stage_SpeedParams)
        self.StageParams_mm = \
            self.stage.CalculateParameters_StageMove(StageParams_ps)
        self.stage.getCurrPos()

    def readParameters(self):
        """
        reads the values from the GUI Interface and saves them in
        global dictionaries
        """

        StageParams_ps['StartPoint'] = float(self.Stage_Start.toPlainText())
        StageParams_ps['EndPoint'] = float(self.Stage_Stop.toPlainText())
        StageParams_ps['StepWidth'] = float(self.Stage_Stepwidth.toPlainText())
        Stage_SpeedParams['Velocity'] = (self.Stage_Velocity.toPlainText())
        Stage_SpeedParams['Acceleration'] = \
            (self.Stage_Acceleration.toPlainText())
        MeasureParameters['Loops'] = int(self.Loops.toPlainText())
        MeasureParameters['Average'] = int(self.Repeats.toPlainText())
        MeasureParameters['IntTime'] = int(self.Int_Time.toPlainText())
        MeasureParameters['Name'] = str(self.sampleNameLine.toPlainText())
        MeasureParameters['Comment'] = str(self.commentLine.toPlainText())
        MeasureParameters['Fluence'] = float(self.fluenceLine.toPlainText())
        MeasureParameters['Power'] = float(self.powerLine.toPlainText())

    @staticmethod
    def calculateStageVectorFromGui():
        """
        create the stageVector_ps from UI entries
        :return: stageVector_ps in Oikoseconds
        """
        stepnumber = \
            (float(StageParams_ps['EndPoint'])-StageParams_ps['StartPoint']) / \
            float(StageParams_ps['StepWidth'])

        vec = np.linspace(float(StageParams_ps['StartPoint']),
                          float(StageParams_ps['EndPoint']),
                          int(stepnumber), endpoint=True)
        return vec

    def Main(self):
        """
        Main Entry Point of measurement procedure.

        Hardware Initialization,
        preparing GUI plots (clear them and apply settings)
        calculate Measurement Parameters from User values

        Start main Update Loop for application
        """
        self.readParameters()
        self.initializeAllHardware()
        self.createVectors()
        self.initialize_Arrays()
        self.prepareGUI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def initializeAllHardware(self):
        """
        Start communication with all Hardware. 
        Set boolean for initialization to true.
        """
        
        self.statusReport("Initialize Hardware")
        self.Initialize = True
        self.initializeStage()
        self.initializeSpectrometer()

    def prepareGUI(self):
        """
        Prepare GUI: set Parameters for Plots, create Colormap, clear plot
        """
        
        self.statusReport("Prepare GUI")
        self.liveSpectraPlot.clear()
        self.createColormap()
        self.Plot_liveSpectra()
        self.Plot_spectra2D()

    def createVectors(self):
        """
        create Stage measurements from GUI entries
        :return: stageVector_ps, stageVector_mm
        """

        self.stageVector_ps = self.calculateStageVectorFromGui()
        self.stageVector_mm = \
            self.stage.calculateStagemmFromps(self.stageVector_ps)

    def initializeSpectrometer(self):
        """
        Initialize OceanOptics Spectrometerm, set Integration Time
        :return: Spectrometer Object
        """

        self.statusReport("Initialize Ocean Optics Spectrometer")
        self.spectro = OOSpectrometer()
        self.spectro.connectSpectrometer()
        self.spectro.setIntTime(MeasureParameters['IntTime'])

    def initialize_Arrays(self):
        """
        Initialize Measurement Arrays and Parameters

        numberWavelength : Number of Pixels/Wavelengths, corrected by a skipping
        factor for the lowest Wavelengthpixel, which would always saturate the
        detector and therefore mess with autoscale properties.

        allSpectra : save measurement of all spectra at each position 
        averagedSpectra : average spectra over loops
        currentSpectra : single current measurement for display
        completeSpectra : Spectra including number of skipped pixels
  
        Parameters: loopValue, repeat, progresscount
        """

        numberWavelength = len(self.spectro.getWave())-NumberOfPixelsToSkip
        self.allSpectra = \
            np.zeros(
                ((int(len(self.stageVector_mm) * MeasureParameters['Loops'])),
                 numberWavelength+2))
        self.averagedSpectra = np.zeros(((int(len(self.stageVector_mm))),
                                         numberWavelength+1))
        self.currentSpectra = np.zeros((numberWavelength, 2))
        self.completeSpectra = np.zeros((numberWavelength+NumberOfPixelsToSkip,
                                         2))
        self.completeSpectra[:, 0] = self.spectro.getWave()
        self.currentSpectra[:, 0] = \
            self.completeSpectra[NumberOfPixelsToSkip:, 0]

        self.loopValue = MeasureParameters['Loops']+1
        self.repeat = MeasureParameters['Average']
        self.progresscount = 0

        return numberWavelength

    def update(self):
        """
        Main Measurement call.
        """

        wavenumber = self.initialize_Arrays()
        self.StartMeasurement = True
        self.Loop = 1

        if self.SaveButton.isChecked():
            self.createFolder()
            self.saveToMeasurementParameterList()

        while self.Loop < self.loopValue:
            self.Stage_idx = 0

            for Stagemove in self.stageVector_mm:
                QtGui.QApplication.processEvents()
                self.stage.moveStage(Stagemove)
                self.Pos_ps = self.stage.calcLightWay(Stagemove)
                dataAverageRepeats = np.zeros((1, wavenumber))
                self.statusReport("Loop: " + str(self.Loop) +
                                  " @StagePosition: " + str(self.Pos_ps))

                self.Repeat_Measurements = 0

                while self.Repeat_Measurements < self.repeat:
                    dat = self.spectro.getSpectrum()
                    data = dat[NumberOfPixelsToSkip:]
                    dataAverageRepeats = dataAverageRepeats + data
                    self.currentSpectra[:, 1] = self.currentSpectra[:, 1] + data
                    QtGui.QApplication.processEvents()
                    self.progresscount = self.progresscount+1
                    self.Repeat_Measurements = self.Repeat_Measurements+1

                data = dataAverageRepeats/self.repeat
                self.currentSpectra[:, 1] = data
                self.calculate_Progress()
                self.update_liveSpectra()
                self.update_spectra2D()

                self.allSpectra[self.Stage_idx, 2:] = data
                self.allSpectra[self.Stage_idx, 0] = self.Pos_ps
                self.allSpectra[self.Stage_idx, 1] = self.Loop

                if self.Loop == 1:
                    self.averagedSpectra[self.Stage_idx, 0] = self.Pos_ps
                    self.averagedSpectra[self.Stage_idx, 1:] = data

                else:
                    dataav = (self.averagedSpectra[self.Stage_idx, 1:]+data)/2
                    self.averagedSpectra[self.Stage_idx, 1:] = dataav

                self.Stage_idx = self.Stage_idx+1
                self.progresscount = self.progresscount+1

            self.Loop = self.Loop+1
            self.progresscount = self.progresscount + 1

            if self.SaveButton.isChecked():
                self.SaveData()

        self.statusReport("Finished Measurement")
        self.timer.stop()

        if self.SaveButton.isChecked():
            self.SaveData()

    def createFolder(self):
        """
        create Folder with timeStamp as name at given directory.
        Check if folder already exists.

        Create Folder with timeStamp Name in the Format: YYYYmmdd_hhmmss.

        :return: new folder created, self.timeStamp
        """

        self.statusReport("Create Folder")
        if self.SaveButton.isChecked():
            self.timeStamp = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
            self.timeStampShow.setText(str(self.timeStamp))
            if not os.path.exists("N:\\FROG\FROG_Measurements\\" +
                                  self.timeStamp):
                os.makedirs("N:\\FROG\FROG_Measurements\\" + self.timeStamp)
                os.chdir("N:\\FROG\FROG_Measurements\\" + self.timeStamp)

    def SaveData(self):
        """
        Save Data:
            - make screenshots of plots
            - save all data
            - save averaged data
        """

        self.statusReport("Saving....")

        Wavelengths = self.currentSpectra[:, 0]

        np.savetxt('FROG_AllData.txt', self.allSpectra,
                   header='0Delay\t 1Loop\t Wavelength\n' +
                          '\t'.join(map(str, Wavelengths)), delimiter='\t')

        np.savetxt('FROG_AveragedData.txt', self.averagedSpectra,
                   header='0Delay\t 1Loop\t Wavelength\n' +
                          '\t'.join(map(str, Wavelengths)), delimiter='\t')

        self.SaveParameters()

        self.plt.enableAutoRange()
        exporter4 = exporters.ImageExporter(self.plt)
        exporter4.parameters()['width'] = 2000
        exporter4.export('Spectra2D.png')

        self.liveSpectraPlot.getPlotItem().enableAutoRange()
        exporter5 = exporters.ImageExporter(self.liveSpectraPlot.plotItem)
        exporter5.parameters()['width'] = 2000
        exporter5.export('LastSingleSpectrum.png')

        self.statusReport("Saved.")

    def Plot_liveSpectra(self):
        """
        Line Spectrum of live spectra
        """

        self.curve = self.liveSpectraPlot.getPlotItem().plot(pen=(215, 128, 26))

    def update_liveSpectra(self):
        """
        Update of live spectra: set the current Spectrum as value
        """

        self.curve.setData(self.currentSpectra)

    def createColormap(self):
        """
        Create Colormap
        :return: self.colmap
        """

        colors = [
            (14, 1, 241),
            (147, 0, 107),
            (252, 3, 1),
            (150, 104, 0),
            (17, 239, 1)
        ]
        self.colmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 5), color=colors)

    def Plot_spectra2D(self):
        """
        Plot 2D transient of Spectrum. y-Axis : Wavelength, x-Axis : timeDelay
        """

        self.plt = pg.PlotItem()
        self.img_view = pg.ImageView(view=self.plt)
        self.img_view.setColorMap(self.colmap)
        self.SpectraGridLayout.addWidget(self.img_view, 0, 0)
        self.plt.setRange(xRange=(self.stageVector_ps.min(),
                                  self.stageVector_ps.max()),
                          yRange=(self.currentSpectra[:, 0].min(),
                                  self.currentSpectra[:, 0].max()))

    def update_spectra2D(self):
        """
        Update 2D transient Spectrum.
        """

        waveMax = self.currentSpectra[:, 0].max()
        waveMin = self.currentSpectra[:, 0].min()
        numberPixel = len(self.currentSpectra[:, 0])
        scalingFactorY = (waveMax-waveMin)/numberPixel
        scalingFactorX = (self.stageVector_ps.max() -
                          self.stageVector_ps.min())/len(self.stageVector_ps)

        self.img_view.setImage(self.averagedSpectra, autoLevels=True,
                               autoRange=False,
                               pos=(self.stageVector_ps.min()/scalingFactorX,
                                    self.currentSpectra[:, 0].min()),
                               scale=(scalingFactorX, scalingFactorY))
        self.plt.setAspectLocked(False)

    def calculate_Progress(self):
        """
        Calculate total Number of Measurement and current Progress.
        :return: Percentage for progressbar
        """

        P_total = MeasureParameters['Loops']*(len(self.stageVector_mm)) * \
                  self.repeat*2
        P_moment = self.progresscount
        Percentage = int((P_moment*100)/P_total)
        self.progressBar.setValue(Percentage)

    def statusReport(self, status):
        """
        Write status in console and in statusbar of GUI
        :param status: Message for user
        """

        print(status)
        self.statusBar().showMessage(status)

    @staticmethod
    def SaveParameters():
        """
        Save all Parameters set or used in the measurement in the Parameter file
        """

        name = 'FROG_Measurement_Parameters.txt'
        file = open(name, 'w')   # Trying to create a new file or open one
        file.write("Loops: {} \n".format(str(MeasureParameters['Loops'])))
        file.write("Averages: {} \n".format(str(MeasureParameters['Average'])))
        file.write("Name: {} \n".format(str(MeasureParameters['Name'])))
        file.write("Integration Time: {} \n".format(
            str(MeasureParameters['IntTime'])))

        file.write("StartPoint: {} ps\n".format(
            str(StageParams_ps['StartPoint'])))
        file.write("End Point: {} ps\n".format(
            str(StageParams_ps['EndPoint'])))
        file.write("Stepwidth: {} ps\n".format(
            str(StageParams_ps['StepWidth'])))
        file.write("stage Velocity: {} \n".format(
            str(Stage_SpeedParams['Velocity'])))
        file.write("stage Acceleration: {} \n".format(
            str(Stage_SpeedParams['Acceleration'])))
        file.write("\n")
        file.write("{} ".format(str(MeasureParameters['Comment'])))

        file.close()

    @staticmethod
    def createOrOpenMeasurementParameterList():
        """
        write important parameters in measurement list for easy choise of
        Measurements and Labbookentry creation
        """

        header = False
        fn = "N:\\FROG\\FROG_MeasurementList.dat"
        file = open(fn, 'a+')
        if os.stat(fn).st_size == 0:
            header = True
        if header:
            file.write('#0Date[YYYYMMDD]\t 1Time[HHMMSS]\t 2Fluence[mJ/cm^2]\t '
                       '3Power[mW]\t 4Temperature[Kelvin]\t 5Samplename\t '
                       '6Comment\n')
        return file

    def partTimeStamp(self):
        """
        Split Timestamp for saving in the measurement list:
            date : YYYYmmdd
            time : hhmmss

        :return: date, time
        """

        date = self.timeStamp.split('_')[0]
        time = self.timeStamp.split('_')[1]
        return date, time

    def saveToMeasurementParameterList(self):
        """
        write important parameters in measurement list for easy choise of
        Measurements and Labbookentry creation
        """

        date, time = self.partTimeStamp()
        file = self.createOrOpenMeasurementParameterList()
        file.write(date+'\t')
        file.write(time+'\t')
        file.write(format(str(MeasureParameters['Fluence'])) + '\t')
        file.write(format(str(MeasureParameters['Power'])) + '\t')
        file.write(format(str('300')) + '\t')
        file.write(format(str(MeasureParameters['Name']))+'\t')
        file.write('#'+format(
            str(MeasureParameters['Comment'].replace("\n", " "))) + '\t')
        file.write('\n')
        file.close()


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
