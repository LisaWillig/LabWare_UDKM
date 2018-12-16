# -*- coding: utf-8 -*-
"""
Created on Thu Mar  8 16:38:38 2018

@author: Mikroskop
"""

import sys
from PyQt5 import QtGui, uic
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox

#import pyqtgraph as pg
import numpy as np
#from pyqtgraph.Qt import QtGui, QtCore
#import pandas as pd
#import os
#import Methods
#from datetime import datetime
#import pyqtgraph.exporters as exporters
#import serial
#from nidaqmx.constants import AcquisitionType, TaskMode, Slope,DigitalWidthUnits
#import pprint
#from pickle import dumps
#from weakref import WeakKeyDictionary
from XPS_ import XPS
#import math 

class StageCommunication():
    
    
    def __init__(self):

          # Instantiate the class
        
        test=2

    def connectStage(self):
        
        self.myxps = XPS()
        self.socketId = self.myxps.TCP_ConnectToServer(b'192.168.255.252', 5001, 20)  # Connect to the XPS
        XPS.TCP_ConnectToServer
        if (self.socketId == -1):  # Check connection passed
            print('Connection to XPS failed, check IP & Port')
            sys.exit()
        self.groupname = 'GROUP3'
        self.positionername = '.POSITIONER'
        self.group = self.groupname.encode(encoding='utf-8')
        self.positioner = self.group + self.positionername.encode()
        self.myxps.GroupKill(self.socketId, self.group)  # Kill the group
        self.myxps.GroupInitialize(self.socketId, self.group)  # Initialize the group 
        self.myxps.GroupJogParametersSet(self.socketId, self.group, '20', '20')
        [errorCode, returnString] = self.myxps.GroupHomeSearch(self.socketId, self.group)
        
    
        # self.myxps.GroupKill(self.socketId, self.group) # Kill the group
        # self.myxps.GroupInitialize(self.socketId,self.group) # Initialize the group 

    def setStageParams(self):

        # read Parameters from GUI or from File
        self.myxps.GroupJogParametersSet(self.socketId, self.group, '20', '20')

    def getCurrPos(self):
        [errorCode, self.currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        #Position=self.currentPosition
        #print('Positioner ' + self.positioner.decode() + ' is in mm position ' + str(self.currentPosition))
        
        #self.CalculateParameters_LightWay(Position)
        #print('Positioner ' + self.positioner.decode() + ' is in ps position ' + str(Pos_ps))

    def moveStageRel(self, RelativeMoveX):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        print('Current Pos: ',currentPosition)
        print('Relative move mm: ', RelativeMoveX)
        self.myxps.GroupMoveRelative(self.socketId, self.positioner, [(float(RelativeMoveX))])
    
        # print ('Positioner ' + positioner.decode() + ' is in position ' +str(currentPosition))
        
    def moveStageAbs(self, AbsoluteMoveX):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        print('Current Pos: ',currentPosition)
        print('Relative move mm: ', AbsoluteMoveX)
        self.myxps.GroupMoveAbsolute(self.socketId, self.positioner, [(float(AbsoluteMoveX))])
    
        # print ('Positioner ' + positioner.decode() + ' is in position ' +str(currentPosition))


    def closeStage(self):

        self.myxps.TCP_CloseSocket(self.socketId)
        # Close connection
    
'''    
    def CalculateParameters_StageMove(self):
        
        for key, value in StageParams_ps.items():
            mm_value=(value*3/10)/2
            StageParams_mm[key]=mm_value
            
        self.Num=(StageParams_ps['EndPoint']-StageParams_ps['StartPoint'])/StageParams_ps['StepWidth']    

        StageParams_mm['StartPoint']=StageParams_mm['StartPoint']-Offset_mm
        StageParams_mm['EndPoint']=StageParams_mm['EndPoint']-Offset_mm
 
        
        print('Number of Steps: ', self.Num)
       
    def CalculateParameters_LightWay(self, Position):
        Offset_ps=(Offset_mm*10/3)*2
        Position_ps=(Position*10/3)*2+Offset_ps
        
        
        return Position_ps
'''        

class MyWindow(QMainWindow):
        
    def __init__(self, parent=None):      
        super(MyWindow, self).__init__(parent)
   
        self.ui=uic.loadUi('MovingStage.ui', self)
        self.show()
       
        self.Button_GoX_abs.clicked.connect(self.MoveStageAbs)
        self.Button_GoX_rel.clicked.connect(self.MoveStageRel)
        self.input_SetRelPositionX.returnPressed.connect(self.MoveStageRel)
        self.input_SetAbsPositionX.returnPressed.connect(self.MoveStageAbs)
        self.Button_Close.clicked.connect(self.close)
        self.Stage=StageCommunication()
        self.Stage.connectStage()
        self.Stage.setStageParams()
        #self.Stage.CalculateParameters_StageMove()
        #self.Stage.getCurrPos()
        
        self.Main()
        
    def closeEvent(self, event):
         reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)
         if reply == QMessageBox.Yes:
                                self.Stage.closeStage()
                                event.accept()
         else:
            event.ignore()
            
        
        
    def Main(self):
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50) 
        self.Stage=StageCommunication()
        self.Stage.connectStage()
        self.Stage.setStageParams()
        #self.Stage.CalculateParameters_StageMove()
        #self.Stage.getCurrPos()
       
    def update(self):  
        self.getCurrentPosition_X()
        
        
        
    def getCurrentPosition_X(self):
        res2=self.Stage.getCurrPos()
        #print(res2)
        res = self.Stage.currentPosition
        #res = self.XPS().GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        res = float(res)
        PosX = round(res,4)
        if PosX == -0.0:
            PosX = 0.0
        else:
            PosX = PosX
        #print(PosX)
        self.Read_CurrentPostionX.setText(str(PosX))
        
    def MoveStageRel(self):
        move = self.input_SetRelPositionX.text()
        self.Stage.moveStageRel(move)
        
    def MoveStageAbs(self):
        move = self.input_SetAbsPositionX.text()
        self.Stage.moveStageAbs(move)
        
        
 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window=MyWindow()
    sys.exit(app.exec_())