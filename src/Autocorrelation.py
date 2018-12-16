#!/usr/bin/env python
# -*- coding: cp1252 -*-

"""
Autocorrelation.py

Author: Gino
Last Edited: 16.12.2018

Python Version: 3.6.5

Measure the Autocorrelation with an Interferrometer

!!!CAUTION!!! The unit calculations do not seem to be correct!!!!
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

import sys
#from PyQt5 import uic
import numpy as np
import pandas as pd
import nidaqmx
import os
import time  # to use sleep function
from scipy.interpolate import UnivariateSpline
#import Methods
import datetime
import pyqtgraph.exporters as exporters
import serial
from nidaqmx.constants import AcquisitionType, TaskMode, Slope,DigitalWidthUnits
#import pprint
#from pickle import dumps
from weakref import WeakKeyDictionary
from XPS_ import XPS
import cProfile
import scipy.signal as scisig # to return idxs of relative extrema
# # # # # # import methods for GUI implementation # # # # # # # #
from PyQt5.QtWidgets import  QApplication, QInputDialog, QComboBox, QGridLayout, QWidget, QLabel, QMessageBox, QToolTip, QPushButton, QLineEdit # open a window and use fundamental widgets
from PyQt5.QtGui import QIcon, QFont # inclusion of an icon
from PyQt5.QtCore import QCoreApplication, Qt, QObject, pyqtSignal, pyqtSlot, QThread # core functionality will be used to create a quit button
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# # # # # import methods for dynamic plot # # # # # # # # # # # #
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from nidaqmx.constants import AcquisitionType
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


# conversion factors
mm_to_ps_lw = 2. / 1000 / 299792548 * 10 ** (13)# lw = light way
ps_to_mm_lw = 1. / mm_to_ps_lw
mm_to_ps = 1. / 1000 / 299792548 * 10 ** (13)   
ps_to_mm = 1. / mm_to_ps


StageParams_mm      = {'Offset': -0.0 , 'StartPoint': 0.0,'EndPoint': 4.0, 'StepWidth': 1.0, 'Range': 2.}
MeasureParams       = {'Averages': 1, 'samples_per_channel': 2}
StageParams_ps      = {'Offset': -5.20765*mm_to_ps, 'Range': 0.05, 'StepWidth': 0.0001} # offset was determined by SINGLECHANNEL in LabView which already considered the lightway ( faktor 2 )
Stage_SpeedParams   = {'Velocity': 100. , 'Acceleration': 0}
assumed_pulse_shape = 'gauss' # initially 'gauss' will be assumed

class StageCommunication():


    def connectStage(self):

        self.myxps = XPS()
        self.socketId = self.myxps.TCP_ConnectToServer(b'10.10.1.2', 5001, 20)  # Connect to the XPS
        XPS.TCP_ConnectToServer #TCP_ConnectToServer(self, IP, port, timeOut)
        if (self.socketId == -1):  # Check connection passed
            print('Connection to XPS failed, check IP & Port')
            sys.exit()
        self.groupname = 'Group3'
        self.positionername = '.Pos'
        self.group = self.groupname.encode(encoding='utf-8')
        self.positioner = self.group + self.positionername.encode()
        self.myxps.GroupKill(self.socketId, self.group)  # Kill the group
        self.myxps.GroupInitialize(self.socketId, self.group)  # Initialize the group ♫
        [errorCode, returnString] = self.myxps.GroupHomeSearch(self.socketId, self.group)

    def setStageParams(self):
        # read Parameters from GUI or from File
        self.myxps.GroupJogModeEnable
        self.myxps.GroupJogParametersSet(self.socketId, self.group,Stage_SpeedParams['Velocity'] , Stage_SpeedParams['Acceleration'])

    def getCurrPos(self):
        [errorCode, self.currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)

    def moveStage(self, RelativeMoveX):
        [errorCode_CurrPos, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        [errorCode_relMove, self.relMoveString] = self.myxps.GroupMoveRelative(self.socketId, self.positioner, [(float(RelativeMoveX)-float(currentPosition))])
   
    def closeStage(self):
        self.myxps.TCP_CloseSocket(self.socketId)


class AC_Measure_thread(QObject):
     finished = pyqtSignal()
     position = pyqtSignal(list, list)
     curPosSignal = pyqtSignal(float)

     def alive_m(self, alive=True):
         self.alive = alive
     
     def __init__(self, alive_signal, averages, stage, Channelname):
        QThread.__init__(self)
        self.Stage = stage
        self.dat = []
        self.posi = []
        self.channel = Channelname
        alive_signal.connect(self.alive_m)
        self.counter_bound = averages 
        
     @pyqtSlot()
     def procedure(self):
         endpos      = float(StageParams_mm['EndPoint'])
         startpos    = float(StageParams_mm['StartPoint'])
         increment_2 = float(StageParams_mm['StepWidth'])
         iterations  =  int( (endpos - startpos) / increment_2)
         print("Stage will be moved between {0} mm and {1} mm with an increment of {2} mm (iterations: {3})".format(StageParams_mm['StartPoint'], StageParams_mm['EndPoint'], StageParams_mm['StepWidth'], iterations))  
         self.Stage.moveStage(startpos) # start from left bound of stage movement range
         incr = +1 * increment_2        # start with movement to the right
         moveRight = True
         counter = 1   # count the number of movements from one bound to the other
         step = 0
         
         while counter <= self.counter_bound and self.alive:
            step += 1    
            print("Measurement iteration {0}, Step {1} of {2}".format(counter,step, iterations))
            # if in terminal STEP is greater than ITERATIONS it is probably a matter of inconvenient rounding
            # move stage and display new position
            signal = np.mean(self.ReadValues())                  # use average() to return the mean of the return value of ReadValues()           
            self.Stage.getCurrPos()
            curPos = float(self.Stage.currentPosition) 
            self.curPosSignal.emit(curPos)                       # for absolute position display ( without offset) of window
            self.posi.append(curPos - StageParams_mm['Offset'])
            self.dat.append(float(signal))
            self.Stage.moveStage(curPos + incr)                  # move stage
            
            if moveRight and curPos > endpos:                    # out of right bound
                print("right bound reached...")
                incr = -1 * increment_2                           
                self.position.emit(self.dat, self.posi)
                self.dat = []
                self.posi = []
                self.Stage.moveStage(endpos)  # stage has been moved out of right bound, so move back to bound
                counter += 1
                step = 0
                moveRight = False
                
            if not moveRight and curPos < startpos:              # out of left bound
                print("left bound reached...")
                incr = +1 * increment_2
                self.position.emit(self.dat, self.posi)
                self.dat = []
                self.posi = []
                self.Stage.moveStage(startpos)                   # stage has been moved out of left bound, so move back to bound
                counter += 1
                step = 0
                moveRight = True
                      
         self.finished.emit()
         print("Measurethread has been finished...")
     
        
     def ReadValues(self) :
         # actual samples
         smplsperchan = MeasureParams['samples_per_channel'] #int(str(self.SplPerChanEdit.text()))
        
         with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.channel)
            ###internal clock mode with no trigger
            task.timing.cfg_samp_clk_timing(1000,sample_mode=AcquisitionType.FINITE, samps_per_chan = smplsperchan) # when AcquisitionTzpe.finite: samps_per_chan gives the number of collected sampels per channel 
            data = task.read()
         return data
     
        
class myWindow(QWidget):
    
    alive_signal = pyqtSignal(bool) # true  ->  measurement stopped
    
    def __init__(self):
        super().__init__()
        
        self.shape_dict = {'gauss': 2*np.sqrt(2*np.log(2)) , 'sech': 1.5427}
        self.FWHM = 0.0
        self.pulse_duration = 0.0

        Channel = 'ai5' # adjus to NI MAX conventions
    
        self.Stage = StageCommunication()
        self.Stage.connectStage()
        #self.Stage.setStageParams()      # to set stage speed
        self.NICard = NI_CardCommunication()

        self.input_task = self.NICard.create_Task_ai(Channel)
        self.Stage.getCurrPos() 
      
        self.socketID = self.Stage.socketId
        self.Channelname = self.NICard.Channelname
        self.positioner = self.Stage.positioner
        self.currentPosition = str(float(self.Stage.currentPosition))
        self.obj = AC_Measure_thread(self.alive_signal, MeasureParams['Averages'], self.Stage, self.Channelname) # create object of ACMeasurement
        self.thread = QThread()            # create a thread
        self.obj.moveToThread(self.thread) # move obj to thread
        self.obj.finished.connect(self.thread.quit) # Connect Worker Signals to the Thread slots
        self.obj.position.connect(self.update)
        self.obj.curPosSignal.connect(self.getCurPos)
        self.thread.started.connect(self.obj.procedure) # Connect Thread started signal to Worker operational slot method
        
        self.initUI()       
     
        
    
    # close events
    # # 'X' clicked
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
        "Are you sure to quit?", QMessageBox.Yes | 
        QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.Stage.moveStage(0.0)
            self.Stage.closeStage()
            self.NICard.CloseTask(self.input_task)
            event.accept()
            #self.close()
        else:
            event.ignore() 
            #pass
       
        
    # # quit button has ben clicked
    def exit_clicked(self): # still YES needs to be clicked twice for some reason
        exit_reply = QMessageBox.question(self, 'Message',
        "Are you sure to quit?", QMessageBox.Yes | 
        QMessageBox.No, QMessageBox.Yes)
        if exit_reply == QMessageBox.Yes:
            self.Stage.moveStage(0.0)
            self.Stage.closeStage()
            self.NICard.CloseTask(self.input_task)           
            self.close()
        else:
           pass 

    
    def initUI(self):
        # set variables to initialize 
        self.locWinX = 300
        self.locWinY = 300
        self.WinWidth  = 900
        self.WinHeight = 500
        # data tuple for Autocorr plot
        self.data = []   # measured signal
        self.pos = []    # pos of stage in mm
        # Start implementing the visuals
        grid = QGridLayout()
        grid.setSpacing(10)
        QToolTip.setFont(QFont('SansSerif', 10)) # 10 is in px
        # Initialize Editor Lines # # # # # # # # # # # # # # # # #
        # # NICard
        NICardLabel = QLabel('<b>NICard:</b>', self)
        grid.addWidget(NICardLabel,0,0,Qt.AlignLeft)
        # # Channelname
        ChannelLabel = QLabel('Channelname: ', self)
        ChannelEdit = QLineEdit()
        ChannelEdit.setText(str(self.Channelname))
        ChannelEdit.setAlignment(Qt.AlignRight)
        ChannelEdit.setReadOnly(True)
        grid.addWidget(ChannelLabel,1,0,Qt.AlignLeft)
        grid.addWidget(ChannelEdit,1,1,1,2,Qt.AlignRight)
        # Stage
        StageLabelX = 0
        StageLabelY = 2
        StageLabel = QLabel('<b>Stage:</b>', self)
        grid.addWidget(StageLabel,StageLabelY,StageLabelX)        
        # # SocketID
        SocketLabel = QLabel('SocketID: ', self)
        SocketEdit = QLineEdit()
        SocketLabel.setToolTip('0-99 = Socket identifier (successfull connection) \n -1   = failure during connection')
        SocketEdit.setText(str(self.socketID))
        SocketEdit.setReadOnly(True)
        SocketEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(SocketLabel,StageLabelY+1,StageLabelX,Qt.AlignLeft)
        grid.addWidget(SocketEdit,StageLabelY+1,StageLabelX+1,1,2,Qt.AlignRight)
        # # Positionername  
        PositionerLabel = QLabel('Positionername: ', self)
        PositionerLabel.setToolTip('label of the positioner: ´name of motion group´.´name of positioner´ ')
        PositionerEdit = QLineEdit(str(self.positioner)[1:].strip("'"))
        #PositionerEdit.setText(str(self.positioner))
        PositionerEdit.setReadOnly(True)
        PositionerEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(PositionerLabel,StageLabelY+2,StageLabelX,Qt.AlignLeft)
        grid.addWidget(PositionerEdit,StageLabelY+2,StageLabelX+1,1,2,Qt.AlignRight)
        # # CurrPos        
        CurrPosLabel = QLabel('Curr. Pos. [mm]: ', self)
        CurrPosLabel.setToolTip('Actual position of the stage in mm without offset substracted.')
        self.CurrPosEdit = QLineEdit()
        self.CurrPosEdit.setText(str(self.currentPosition))
        self.CurrPosEdit.setReadOnly(True)
        self.CurrPosEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(CurrPosLabel,StageLabelY+3,StageLabelX,Qt.AlignLeft)
        grid.addWidget(self.CurrPosEdit,StageLabelY+3,StageLabelX+1,1,2,Qt.AlignRight)

        # localize plot of AC # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        PosXOfAutocorr=6
        PosYOfAutocorr=0        
        AveragingLabel = QLabel('<b>Averaging:<\b>', self)
        grid.addWidget(AveragingLabel,PosYOfAutocorr+14,PosXOfAutocorr+2,Qt.AlignLeft)

        # # Integration time 
        SplPerChanLabel = QLabel('samples per channel: ', self)
        self.SplPerChanEdit = QLineEdit(str(MeasureParams['samples_per_channel']))
        self.SplPerChanEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(SplPerChanLabel,PosYOfAutocorr+15,PosXOfAutocorr+2,Qt.AlignLeft)
        grid.addWidget(self.SplPerChanEdit,PosYOfAutocorr+15,PosXOfAutocorr+3,Qt.AlignRight)

        # # Averages 
        AvgLabel = QLabel('Loops: ', self)
        AvgLabel.setToolTip('Number of full Autorcorrelations over which is averaged.  \n "Range" covers one loop.')
        self.AvgEdit = QLineEdit(str(MeasureParams['Averages']))
        self.AvgEdit.setAlignment(Qt.AlignRight)
        self.AvgEdit.setToolTip('Number of full Autorcorrelations over which is averaged')
        grid.addWidget(AvgLabel,PosYOfAutocorr+16,PosXOfAutocorr+2,Qt.AlignLeft)
        grid.addWidget(self.AvgEdit,PosYOfAutocorr+16,PosXOfAutocorr+3,Qt.AlignRight)

        # # Start Pos in mm 
        LightwayLabel = QLabel('<b>Light path:<\b>', self)
        LightwayLabel.setToolTip('Set the delays between the two pulses (factor 2).')
        grid.addWidget(LightwayLabel,PosYOfAutocorr+14,PosXOfAutocorr,Qt.AlignLeft) 
        OffsetLabel = QLabel('Offset [ps]: ', self)
        OffsetLabel.setToolTip('Set the new absolute zero position.')
        self.OffsetEdit = QLineEdit(str(StageParams_ps['Offset'])[:12])
        self.OffsetEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(OffsetLabel,PosYOfAutocorr+15,PosXOfAutocorr,Qt.AlignLeft)
        grid.addWidget(self.OffsetEdit,PosYOfAutocorr+15,PosXOfAutocorr+1,Qt.AlignRight)

        # # End Pos in mm 
        RangeLabel = QLabel('Range [ps]: ', self)
        RangeLabel.setToolTip('Set the extend of the movement towards each side of the offset.')
        self.RangeEdit = QLineEdit(str(StageParams_ps['Range']))
        self.RangeEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(RangeLabel,PosYOfAutocorr+16,PosXOfAutocorr,Qt.AlignLeft)
        grid.addWidget(self.RangeEdit,PosYOfAutocorr+16,PosXOfAutocorr+1,Qt.AlignRight)

        # # Stage increment in mm
        InkrLabel = QLabel('Stepwidth [ps]: ', self)
        self.InkrEdit = QLineEdit(str(StageParams_ps['StepWidth']))
        self.InkrEdit.setAlignment(Qt.AlignRight)
        InkrLabel.setToolTip('The displacement of the stage after each measurement')
        grid.addWidget(InkrLabel,PosYOfAutocorr+17,PosXOfAutocorr,Qt.AlignLeft)
        grid.addWidget(self.InkrEdit,PosYOfAutocorr+17,PosXOfAutocorr+1,Qt.AlignRight)


        # results of AC # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # pulse shape
        AssumedPulseShapeLabel = QLabel('assumed pulse shape: ', self) # include dictionary of pulseshapes that is linked to konversion factors from FWHM to pulse duration
        AssumedPulseShapeLabel.setToolTip('Choose a pulse shape from the list to set the associated conversion factor from FWHM to pulse duration.')
        grid.addWidget(AssumedPulseShapeLabel,PosYOfAutocorr+1,PosXOfAutocorr+6,Qt.AlignLeft)
        self.combo = QComboBox(self)
        self.combo.setStyleSheet('QCombobox {background color: red}')
        self.combo.addItem("gauss")
        self.combo.addItem("sech")
        grid.addWidget(self.combo, PosYOfAutocorr+1,PosXOfAutocorr+7)
        self.combo.currentIndexChanged.connect(self.FWHM_to_duration)

        # # FWHM
        FWHMLabel = QLabel('FWHM [ps]: ', self) # include dictionary of pulseshapes that is linked to konversion factors from FWHM to pulse duration
        self.FWHMEdit = QLineEdit(str(self.FWHM))
        self.FWHMEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(FWHMLabel,PosYOfAutocorr+2,PosXOfAutocorr+6,Qt.AlignLeft)
        grid.addWidget(self.FWHMEdit,PosYOfAutocorr+2,PosXOfAutocorr+7,Qt.AlignRight)

        # # pulse duration 
        PulseDurLabel = QLabel('pulse duration [ps]: ', self) # include dictionary of pulseshapes that is linked to konversion factors from FWHM to pulse duration
        self.PulseDurEdit = QLineEdit(str(self.pulse_duration))
        self.PulseDurEdit.setAlignment(Qt.AlignRight)
        grid.addWidget(PulseDurLabel,PosYOfAutocorr+3,PosXOfAutocorr+6,Qt.AlignLeft)
        grid.addWidget(self.PulseDurEdit,PosYOfAutocorr+3,PosXOfAutocorr+7,Qt.AlignRight)

        # # implementation of AC plot
        AC_PlotLabel = QLabel('<b>Autocorrelation:</b>')
        grid.addWidget(AC_PlotLabel,PosYOfAutocorr,PosXOfAutocorr)


        # initialize buttons # # # # # # # # # # # # # # # # # # #
        # # exit button 
        quit_btn = QPushButton(self)
        quit_btn.setStyleSheet('QPushButton {color: red}')
        quit_btn.setText('Exit')
        quit_btn.setFlat(True)
        quit_btn.clicked.connect(self.exit_clicked)
        quit_btn.resize(quit_btn.sizeHint())
        grid.addWidget(quit_btn,23,PosXOfAutocorr+7)

        # # AC_Measurement button
        StartAC_btn = QPushButton("Measure AC",self)
        grid.addWidget(StartAC_btn,PosYOfAutocorr+11,PosXOfAutocorr)
        StartAC_btn.clicked.connect(self.StartAC)

        # # clear Autocorr Plot
        self.ClearAutocorr_btn = QPushButton("Clear AC", self)
        self.ClearAutocorr_btn.setEnabled(False)
        grid.addWidget(self.ClearAutocorr_btn,PosYOfAutocorr+11,PosXOfAutocorr+1)
        self.ClearAutocorr_btn.clicked.connect(self.Clear_Autocorr_Plot)

        # # Stop Autocorr measurement
        self.StopAutocorr_btn = QPushButton("Stop AC", self)
        self.StopAutocorr_btn.setEnabled(False)
        grid.addWidget(self.StopAutocorr_btn,PosYOfAutocorr+11,PosXOfAutocorr+2)
        self.StopAutocorr_btn.clicked.connect(self.StopAC)

        # # Save Autocorr plot
        self.SaveAC_btn = QPushButton("Save AC data", self)
        grid.addWidget(self.SaveAC_btn,PosYOfAutocorr,PosXOfAutocorr+1)
        self.SaveAC_btn.setEnabled(False)
        self.SaveAC_btn.clicked.connect(self.saveAC)


        # set layout of window # # # # # # # # # # #
        self.setLayout(grid)
        self.setGeometry(self.locWinX, self.locWinY, self.WinWidth, self.WinHeight)
        self.setWindowTitle('Autocorrelation measurement')
        self.setWindowIcon(QIcon('unilogo.png'))
        pg.setConfigOption('background', 'w') # set white background for plot
        self.win = pg.GraphicsWindow(title="AC(t)")
        self.win.resize(50,50)
        pg.setConfigOptions(antialias=True)
        self.p6 = self.win.addPlot(title="", y=self.data, x=self.pos)
        grid.addWidget(self.win, PosYOfAutocorr+1, PosXOfAutocorr, 10, 5)
        self.curve = self.p6.plot(pen='b')
        self.p6.addLine(y=0, pen='k')
        
        self.show()

    
    # # # different methods # # # # # # # # # # # # # # # # # # #

        
    def saveAC(self):
        datetime_  = datetime.datetime.now()
        time_stamp = str(datetime_)
        time_stamp = time_stamp.replace(" ","_").replace(":","_")

        StageParams_ps['Offset'] = StageParams_mm['Offset'] * mm_to_ps_lw
        StageParams_ps['Range'] = StageParams_mm['Range'] * mm_to_ps_lw
        StageParams_ps['StepWidth'] = StageParams_mm['StepWidth'] * mm_to_ps_lw
        
        filename = "./Messdaten/AC_data_"+time_stamp+".txt"
        with open(filename, "w") as file:

            # values of StageParams_mm will be used as ACSave is only enabled after AC measurement and in AC measurement the preset entries of the QTextEdits are written in StageParams_mm
            file.write('parameters:\n\n')
            file.write('samples_per_position:\t'+str(MeasureParams['samples_per_channel']))
            file.write('\naverages:\t\t'+str(MeasureParams['Averages']))
            file.write('\noffset[ps]:\t\t'+str(StageParams_ps['Offset']))            
            file.write('\nrange[ps]:\t\t'+str(StageParams_ps['Range']))            
            file.write('\nstep width[ps]:\t\t'+str(StageParams_ps['StepWidth']))

            # pulse characteristics calculated from AC signal
            file.write('\n\n pulse_characteristics:\n\n')
            file.write('assumed_pulse_shape:\t'+str(self.assumed_pulse_shape))
            file.write('\nFWHM[ps]:\t\t'+str(self.FWHM))
            file.write('\npulse_duration[ps]:\t'+str(self.pulse_duration))

            # AC signal
            for idx in range(len(self.data)+1):
                if idx == 0: file.write('\n\n'+str(time_stamp)+"\n\nDelay [ps]\tIntensity [arb. u.]\n")
                else:
                    input_str = str(self.pos[idx-1]) + "\t" + str(self.data[idx-1]) + "\n"
                    file.write(input_str)
        print("Aquired data has been saved to '{0}'...".format(filename))

        
    def StartAC(self):

        # read the QEdits for parameters
        StageParams_mm['Offset']              = float(self.OffsetEdit.text()) * ps_to_mm_lw
        StageParams_mm['StartPoint']          = (float(self.OffsetEdit.text()) - float(self.RangeEdit.text())) * ps_to_mm_lw
        StageParams_mm['EndPoint']            = (float(self.OffsetEdit.text()) + float(self.RangeEdit.text())) * ps_to_mm_lw
        StageParams_mm['StepWidth']           = float(self.InkrEdit.text()) * ps_to_mm_lw
        StageParams_mm['Range']               = float(self.RangeEdit.text()) * ps_to_mm_lw # for SAVE_AC
        MeasureParams['Averages']             = int(self.AvgEdit.text())
        MeasureParams['samples_per_channel']  = int(self.SplPerChanEdit.text())
       
        self.StopAutocorr_btn.setEnabled(True)
        self.ClearAutocorr_btn.setEnabled(True)

        # connect to AC_measurement thread and initialize variables
        self.obj.counter_bound = MeasureParams['Averages'] # remove this parameter from MEASURETHREAD.init
        self.obj.alive = True
        self.thread.start() # start measurement in additional thread to enable simultaneous refreshing of GUI

        # if last measurement and averaging is done, enable save button
        self.SaveAC_btn.setEnabled(True) # enable after full thread so samples are actually available

   
    def StopAC(self):
        print("StopAC() has been called...")
        self.alive_signal.emit(False) # should work more immediate than the above line
        self.StopAutocorr_btn.setEnabled(False)
    
    def getCurPos(self, pos):
        self.CurrPosEdit.setText(str(pos)[:8])
        self.currentPosition = pos     # remove this line if problems arise

    def update(self, plot_y, plot_x):

        # refresh the whole plot and calculate pulse characteristics (FWHM, duration)
        self.data = []
        self.pos = []
        
        for k in range(len(plot_y)):
           self.data.append(plot_y[k])               # update data
           self.pos.append(plot_x[k] * mm_to_ps_lw)  # update positions and convert stage path to light path
        
        
        self.curve.clear()
        self.curve.setData(self.pos, self.data)
        
        self.FWHM = 42
        self.FWHMEdit.setText(str(self.FWHM)[0:6]) # [0:6] to display only 6 digits
        
        self.FWHM_to_duration()
        
    def FWHM_to_duration(self):
        self.assumed_pulse_shape = str(self.combo.currentText()) # leave out braces if code doesnt run
        self.pulse_duration = self.FWHM / self.shape_dict[str(self.combo.currentText())]
        self.PulseDurEdit.setText(str(self.pulse_duration)[:6])      
        print("Combobox index changed and/or update for pulse shape has been called...")
        
    def Clear_Autocorr_Plot(self):
        self.data = []
        self.pos = []
        self.FWHM = 0.
        self.pulse_duration = 0.
        self.curve.setData(self.data[:-1], self.pos[:-1])
        self.FWHMEdit.setText(str(self.FWHM)[0:6]) # [0:6] to display only first 4 decimal places
        self.PulseDurEdit.setText(str(self.pulse_duration)[:6])      


if __name__ == '__main__':

    app3 = QApplication(sys.argv)
    window = myWindow()
    sys.exit(app3.exec_())
          
