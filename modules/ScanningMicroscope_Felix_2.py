#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  5 14:59:34 2018

@author: felix
"""
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  8 16:38:38 2018

@author: Mikroskop
"""

import sys
from PyQt5 import QtGui, uic
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox

import time  #to get the timeouts
import datetime  #to add timestamp to the filenames

import pyqtgraph as pg
pg.setConfigOption('background', [64,64,64])
pg.setConfigOption('foreground', [238,238,238])

import numpy as np
from matplotlib import pyplot as plt
from XPS_ import XPS
from MEMeasurementCard import MECard
Stage_SpeedParams={'Velocity':'20', 'Acceleration':'20'}
import serial
import os

SavePath = "F:/Users/Mikroskop/Daten/Raman Scanning Microscope/tmpData"


speed = '1'

class StageCommunication_Y():
    
    
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
        self.myxps.GroupJogParametersSet(self.socketId, self.group, speed, speed)
        [errorCode, returnString] = self.myxps.GroupHomeSearch(self.socketId, self.group)
            
    def setStageParams(self):
        # read Parameters from GUI or from File
        self.myxps.GroupJogParametersSet(self.socketId, self.group, speed, speed)

    def getCurrPos(self):
        [errorCode, self.currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        return self.currentPosition

    def moveStageRel(self, RelativeMoveX):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        print('Current Pos: ',currentPosition)
        print('Relative move mm: ', RelativeMoveX)
        self.myxps.GroupMoveRelative(self.socketId, self.positioner, [(float(RelativeMoveX))])
            
    def moveStageAbs(self, AbsoluteMoveX):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        self.myxps.GroupMoveAbsolute(self.socketId, self.positioner, [(float(AbsoluteMoveX))])
    
    def closeStage(self):

        self.myxps.TCP_CloseSocket(self.socketId)   # Close connection
        
    

class StageCommunication_X():
    
    
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
        self.groupname = 'GROUP1'
        self.positionername = '.POSITIONER'
        self.group = self.groupname.encode(encoding='utf-8')
        self.positioner = self.group + self.positionername.encode()
        self.myxps.GroupKill(self.socketId, self.group)  # Kill the group
        self.myxps.GroupInitialize(self.socketId, self.group)  # Initialize the group 
        self.myxps.GroupJogParametersSet(self.socketId, self.group, speed, speed)
        [errorCode, returnString] = self.myxps.GroupHomeSearch(self.socketId, self.group)

    def setStageParams(self):
        # read Parameters from GUI or from File
        self.myxps.GroupJogParametersSet(self.socketId, self.group, speed, speed)

    def getCurrPos(self):
        [errorCode, self.currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        return self.currentPosition

    def moveStageRel(self, RelativeMoveX):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        print('Current Pos: ',currentPosition)
        print('Relative move mm: ', RelativeMoveX)
        self.myxps.GroupMoveRelative(self.socketId, self.positioner, [(float(RelativeMoveX))])
        
    def moveStageAbs(self, AbsoluteMoveX):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        self.myxps.GroupMoveAbsolute(self.socketId, self.positioner, [(float(AbsoluteMoveX))])

    def closeStage(self):

        self.myxps.TCP_CloseSocket(self.socketId)
        # Close connection
        
                
class MonochromatorCommunication():
    
    def __init__(self):
        
        test=2
        
    def MonoCommunication(self,befehl):  
        self.ser = serial.Serial()
        self.ser.port = 'COM2'
        self.ser.baudrate=9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE 
        self.ser.timeout=0.1
        self.ser.close() 
        self.ser.open()
        
        befehlb= befehl.encode()
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.write(befehlb)
        resunicode=self.ser.readline()
        resunicode2=self.ser.readline()
        res=resunicode.decode()
        res2=resunicode2.decode()
        res=res.rstrip('\r\n')
        res2=res2.rstrip('\r\n')
        self.ser.close()
                
        return res2
    
    def closeMonochromator(self):
        self.ser = serial.Serial()
        self.ser.port = 'COM2'
        self.ser.baudrate=9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE 
        self.ser.timeout=0.1
        self.ser.close() 

                              
        
class MyWindow(QMainWindow):
        
    def __init__(self, parent=None):      
        super(MyWindow, self).__init__(parent)   
        self.ui=uic.loadUi('ScanningMicroscope_Felix_4_MainWindow.ui', self)
        self.show()
        
        self.StopScanButton = False
        self.PauseScanButton = False
        self.StopSpectrumButton = False
        self.PauseSpectrumButton = False
        
        
        self.Button_StartScan.clicked.connect(self.Main)
        self.Button_StartSpectrum.clicked.connect(self.Main_Spectrum)
        self.Button_Quit.clicked.connect(self.close)
        self.StageX=StageCommunication_X()
        self.StageX.connectStage()
        self.Mono=MonochromatorCommunication()
        self.AICard=MECard()
        self.StageX.setStageParams()
        self.StageY=StageCommunication_Y()
        self.StageY.connectStage()
        self.StageY.setStageParams()       
        self.Input_SpectrumPositionX.returnPressed.connect(self.MoveStageXAbsExt)
        self.Input_SpectrumPositionY.returnPressed.connect(self.MoveStageYAbsExt)
        self.Button_SaveImage.clicked.connect(self.SaveImage)
        self.Button_StopScan.clicked.connect(self.StopScan)
        self.Button_PauseScan.clicked.connect(self.PauseScan)
        self.Button_StopSpectrum.clicked.connect(self.StopSpectrum)
        self.Button_SaveSpectrum.clicked.connect(self.SaveSpectrum)
        self.Button_PauseSpectrum.clicked.connect(self.GetCurrentWavelength)
        self.ImageDataWidget.clear()
        self.SpectrumDataWidget.clear()
        self.Input_DetectionWavelength.returnPressed.connect(self.GoToWaveExtInput)
        
        self.GetCurrentWavelength()
        self.getCurrentPosition_X()
        self.getCurrentPosition_Y()



    def closeEvent(self, event):
         reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)
         if reply == QMessageBox.Yes:
                                self.StageX.closeStage()
                                self.StageY.closeStage()
                                self.Mono.closeMonochromator()
                                event.accept()
         else:
            event.ignore()
            
        
        
    def Main(self):        
        self.initializeValues_Scan()
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50) 
        
    def Main_Spectrum(self):
        self.initializeValues_Spectrum()
        self.timer_2 = PyQt5.QtCore.QTimer()
        self.timer_2.timeout.connect(self.update_Spectrum)
        self.timer_2.start(50) 
               
    def update(self):  
        self.Scan()
        self.timer.stop()
        
    def update_Spectrum(self):
        self.Spectrum()
        self.timer_2.stop()

    #Get the current X position, and show it in the info box in um    
    def getCurrentPosition_X(self):
        res=self.StageX.getCurrPos()
        res = float(res)
        PosX = round(res,6)
        if PosX == -0.0:
            PosX = 0.0
        else:
            PosX = PosX
        self.Read_CurrentPositionX.setText(str(round(PosX*1000,2)))
        
    #Get the current Y position, and show it in the info box in um    
    def getCurrentPosition_Y(self):
        res=self.StageY.getCurrPos()
        res = float(res)
        PosY= round(res,5)
        if PosY == -0.0:
            PosY = 0.0
        else:
            PosY = PosY
        self.Read_CurrentPositionY.setText(str(round(PosY*1000,2)))
    
    '''    
    #Moving stage Y by value given by input field     
    def MoveStageXRel(self):
        move = self.input_SetRelPositionX.text()
        self.StageX.moveStageRel(move)
        self.getCurrentPosition_X()'''
        
    # Moving Stage X to absolute value given from other function
    def MoveStageXAbsInt(self,goX):
        self.StageX.moveStageAbs(goX)
        self.getCurrentPosition_X()

    # Moving Stage X to absolute value given by spectrum position field
    def MoveStageXAbsExt(self):
        goX = float(self.Input_SpectrumPositionX.text())/1000
        self.StageX.moveStageAbs(str(goX))
        self.getCurrentPosition_X()
        
    '''
    #Moving stage Y by value given by input field   
    def MoveStageYRel(self):
        move = self.input_SetRelPositionY.text()
        self.StageY.moveStageRel(move)'''

        
    # Moving Stage Y to absolute value given from other function
    def MoveStageYAbsInt(self,goY):
        self.StageY.moveStageAbs(goY)
        self.getCurrentPosition_Y()

    # Moving Stage Y to absolute value given by spectrum position field
    def MoveStageYAbsExt(self):
        goY = float(self.Input_SpectrumPositionY.text())/1000
        self.StageY.moveStageAbs(str(goY))
        self.getCurrentPosition_Y()

    # Initialising values for a scan    
    def initializeValues_Scan(self):
        x_start = float(self.Input_CentralPositionX.text()) - 0.5*float(self.Input_ImageArea_X.text())
        x_end = float(self.Input_CentralPositionX.text()) + 0.5*float(self.Input_ImageArea_X.text())        
        self.x_Points = np.linspace(x_start,x_end,int((x_end-x_start)/float(self.Input_StepSize.text()))+1)       

        y_start = float(self.Input_CentralPositionY.text()) - 0.5*float(self.Input_ImageArea_Y.text())
        y_end = float(self.Input_CentralPositionY.text()) + 0.5*float(self.Input_ImageArea_Y.text())        
        self.y_Points = np.linspace(y_start,y_end,int((y_end-y_start)/float(self.Input_StepSize.text()))+1)
        
        self.image_data = np.zeros([len(self.x_Points),len(self.y_Points)])
        self.plotImageView()
 
    # Initialising values for a spectrum       
    def initializeValues_Spectrum(self):
        wave_start = float(self.Input_StartWavelength.text())
        wave_end = float(self.Input_EndWavelength.text())
        self.wave_Points = np.linspace(wave_start,wave_end,int((wave_end-wave_start)/float(self.Input_StepWidth.text()))+1)
        self.SpectrumData = np.zeros(len(self.wave_Points))
 
    # Starting an image scan. The scanning wavelength is read from the input
    # field in the GUI
    def Scan(self):
        self.GoToWaveExtInput()
        self.StopScanButton = False
                
        for j in range(len(self.y_Points)):
            print(' ')
            self.MoveStageYAbsInt(str(round(self.y_Points[j]/1000,4)))
            print('Set Y-position = ' , round(self.y_Points[j],2))
            self.getCurrentPosition_Y()
            print('Real Y-position = ' , float(self.StageY.currentPosition)*1000)
            print(' ')
            
            if self.StopScanButton == True:
                break
            
            for i in range(len(self.x_Points)):
                self.MoveStageXAbsInt(str(round(self.x_Points[i]/1000,4)))
                time.sleep(200/1000)
                QtGui.QApplication.processEvents()
                
                # The card does not have an integration time but only reads the 
                # voltage value at the moment of the question. Thus an average
                # over several values is taken instead of longer integration 
                # times
                int_time = int(self.Input_IntegrationTimeScan.text())
                sig=0
                for k in range(int_time):
                    sig =+  self.AICard.measure()                     
                self.image_data[i,j] = sig/int_time
                print(self.image_data[i,j])
                self.updateImageView()
                self.getCurrentPosition_X()
                                
                print('Set X-position = ' , round(self.x_Points[i],2))
                print('Real X-position = ' , float(self.StageX.currentPosition)*1000)
                print(' ')
                                                    
                if self.StopScanButton == True:
                    break
                
        data = np.column_stack((self.x_Points,self.image_data))
        data = np.column_stack((np.append(0,self.y_Points),data.transpose()))       
        np.savetxt('temp_Scan.csv',data,delimiter=',')
                
    def plotImageView(self):
        self.ImageDataWidget.setImage(self.image_data, autoRange=False,autoLevels=False )
        
    def updateImageView(self):
        self.ImageDataWidget.setImage(self.image_data, xvals=self.x_Points, autoRange=True,autoLevels=True)
        
    #Changing the value for StopScan to interrupt the scan
    def StopScan(self):
        self.StopScanButton = True
 
    #Changing the value for PauseScan to halt the scan       
    def PauseScan(self):
        self.PauseScanButton = not self.PauseScanButton
    
    # Saving an image from a tempfile stored in the program folder. The name
    # can be chosen and a timestamp is added. Files are stored to a tmp folder
    # in the data folder of the microscope pc
    def SaveImage(self):
        data = np.genfromtxt('temp_Scan.csv',delimiter=',')
        print(data)
        Name = self.Input_SaveImageName.text()
        Name = str(Name)
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')     
        time_stamp = time_stamp.replace(" ","_")
        time_stamp = time_stamp.replace(":","_")
        
        FileName = time_stamp + Name + '.csv'

        np.savetxt(os.path.join(SavePath,FileName),data,delimiter=',')
    
    def PlotImage(self):
        data = np.genfromtxt('temp_Scan.csv',delimiter=',')
        plt.figure(1)
        plt.pcolor(data[0,:],data[:,0],data[1:,1:])
        data = data[1:,1:]
        pg.image(data)
     
    # Starting a spetrum. The position is given by the input values
    def Spectrum(self):
        self.MoveStageXAbsExt()
        self.MoveStageYAbsExt()
        self.StopSpectrumButton = 'false'
        print(self.wave_Points)
        self.SpectrumDataWidget.clear()
        
        for i in range(len(self.wave_Points)):
            self.GoToWaveIntInput(str(round(self.wave_Points[i],3)))
            if i==0:
                time.sleep(2)
            else:
                time.sleep(0.5)
             
            QtGui.QApplication.processEvents()
            
            # The card does not have an integration time but only reads the 
            # voltage value at the moment of the question. Thus an average
            # over several values is taken instead of longer integration 
            # times
            int_time = int(self.Input_IntegrationTimeSpectrum.text())
            spec=0
            for j in range(int_time):
                spec =+  self.AICard.measure()  
                               
            self.SpectrumData[i]= spec/int_time
            self.SpectrumDataWidget.clear()
            self.SpectrumDataWidget.plot(self.wave_Points,self.SpectrumData)
            
            if self.StopSpectrumButton == True:
                break
            
        data_Spec = self.SpectrumData
        data_Spec = np.column_stack((self.wave_Points,self.SpectrumData))
        np.savetxt('temp_Spec.csv',data_Spec,delimiter=',')

    #Changing the value for StopScan to interrupt the spectrum
    def StopSpectrum(self):
        self.StopSpectrumButton = True

    # Saving aspectrum from a tempfile stored in the program folder. The name
    # can be chosen and a timestamp is added. Files are stored to a tmp folder
    # in the data folder of the microscope pc    
    def SaveSpectrum(self):
        data = np.genfromtxt('temp_Spec.csv',delimiter=',')
        Name = self.Input_SaveSpectrum.text()
        Name = str(Name)
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')     
        time_stamp = time_stamp.replace(" ","_")
        time_stamp = time_stamp.replace(":","_")
        FileName = time_stamp + Name + '.csv'
        np.savetxt(os.path.join(SavePath,FileName),data,delimiter=',')
          
    # Moving the monochromator to a wavelength given by the detection
    # wavelength field               
    def GoToWaveExtInput(self):
        GoWave = self.Input_DetectionWavelength.text()
        Go = str(GoWave)
        Go ="GOWAVE "+Go+"\r\n"
        self.Mono.MonoCommunication(Go)
        self.GetCurrentWavelength()
        
    # Moving the monochromator to a wavelength given by an internal function
    def GoToWaveIntInput(self,GoWave):
        Go = str(GoWave)
        Go ="GOWAVE "+Go+"\r\n"
        self.Mono.MonoCommunication(Go)
        self.GetCurrentWavelength()
      
    # Reading out current wavelength position and writing it into the control
    # window    
    def GetCurrentWavelength(self):
        befehl = 'WAVE?\r\n'
        x = self.Mono.MonoCommunication(befehl)
        x = float(x)
        x = round(x,1)
        self.Read_CurrentWavelength.setText(str(x))
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window=MyWindow()
    sys.exit(app.exec_())


'''
there is still an unprecision on the stage. It doesn't wait until it has reached it's position
may be add x- and y-axes to the live image plot
may be change waiting time for monochromator to when it's where it's supposed to be
make side bar in scan image smaller
add a pause button
make a proper ducoumentation / add more comments
'''


'''
calc
'''