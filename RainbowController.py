#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RainbowController.py

Author: Felix Stete, Lisa Willig
Last Edited: 16.12.2018

Python Version: 3.6.5
Rainbow Laser

Communication with the Rainbow Laser Controller.

"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import sys
import PyQt5 
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import serial

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) GUI Communication Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MyWindow(QMainWindow):
        
    def __init__(self, parent=None):      
        super(MyWindow, self).__init__(parent)
   
        # load UI
        self.ui=uic.loadUi('GUI/mainwindowUbuntu.ui', self)
        
        # connect Buttons to Action
        self.OnButton.clicked.connect(self.on)
        self.OffButton.clicked.connect(self.off)
        self.SetPowerLine.returnPressed.connect(self.setPower)
        self.CloseButton.clicked.connect(self.close)
        self.ReadPowerLCD.setDigitCount(4) 
        #self.TestButton.clicked.connect(self.OPMode)
        self.StandbyButton.clicked.connect(self.Standby)
        #self.WarningText.returnPressed.connect(self.WarnI)
        
        # Show GUI
        self.Main()
        self.show()

    def initializeCommunication(self):
        """
        Open Communication with COM connected Laser Controller.
        Read Power

        :returns: Laser Object
        """

        self.initializeCOM()
        if self.ser.isOpen():
            print("Device is connected")
            self.readSetPower()


    def initializeCOM(self):
        """
        Initialize COM Communication
        """

        self.ser = serial.Serial()
        self.ser.port = 'COM10'
        self.ser.baudrate=19200
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE 
        self.ser.timeout=0.1
        self.ser.close() 
        self.ser.open()


    def closeEvent(self, event):
        """
        Avtions for Closing event when exit or window close button is pressed.
        If the laser is still running, show an error message
        """

        self.readOnOff()
        if self.res=='OPMODE=ON':
        
            reply = QMessageBox.question(self, 'Message',
                                         "Laser is still running. Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
        
    def Main(self):
        """
        Main Entry point for Application. 
        Laser Communication is established, QTimer is started.
        """

        self.initializeCommunication()
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50) 
       
    def update(self):  
        """
        Update Loop for Laser running. 
        Update the GUI displays and check for errors
        """

        self.readPower()
        self.Warn()
        self.interlock()
        self.shutter()
        self.operationHours()
        self.runHours()
        self.OPMode()
        
    def readSetPower(self):
        befehl="POWER SET?\r"
        res=self.sendcommand(befehl)
        #res=res.rstrip("POWER SET=")
        power=res[10:]
        self.SetPowerLine.setText(power)
        
    def readPower(self):
        befehl="POWER?\r"
        res=self.sendcommand(befehl)
        power=res[6:]
        #print(power)
        self.ReadPowerLCD.display(power)
        
    def Warn(self):
        befehl="WARNING?\r"
        res=self.sendcommand(befehl)
        warn=res[8:]
        self.WarningText.setText(warn)
        
    def setPower(self):
        power=self.SetPowerLine.text()
        power=str(power)       
        befehl="POWER SET="+power+"\r"
        self.sendcommand(befehl)
        befehl="POWER SET?\r"
        self.sendcommand(befehl)
        befehl="OPMODE?\r"
        self.sendcommand(befehl)
        
    def on(self):  
       befehl="OPMODE=ON\r"
       self.sendcommand(befehl)
       
    def Standby(self):
        befehl="OPMODE=IDLE\r"
        self.sendcommand(befehl)
       
    def off(self):  
       befehl="OPMODE=OFF\r"
       self.sendcommand(befehl)
       befehl="OPMODE?\r"
       self.sendcommand(befehl)
       
    def readOnOff(self):
       befehl="OPMODE?\r"
       self.sendcommand(befehl)
       
    def WarnI(self):
        befehl="WARNING?\r"
        self.sendcommand(befehl)
        print(self.res)
        
    def interlock(self):
        befehl="INTERLOCK?\r"
        res=self.sendcommand(befehl)
        warn=res[10:]
        #print(res)
        #print(warn)
        self.InterlockText.setText(warn)
        
    def shutter(self):
        befehl="SHUTTER?\r"
        res=self.sendcommand(befehl)
        shut=res[8:]
        self.ShutterText.setText(shut)
        
    def operationHours(self):
        befehl="HOURS?\r"
        res=self.sendcommand(befehl)
        opHour=res[6:]
        #print(res)
        self.OperationHoursText.setText(opHour)
        
    def runHours(self):
        befehl="RUN HOURS?\r"
        res=self.sendcommand(befehl)
        runHour=res[10:]
       # print(res)
        self.RunHoursText.setText(runHour)
        
    def OPMode(self):
        befehl="OPMODE?\r"
        res=self.sendcommand(befehl)
        opMode=res[7:]
        self.OPModeText.setText(opMode)
    

    def sendcommand(self, befehl):    
       """
       Method for sending the COM commands and receiving the answer

       :return: Answer as string
       """

       befehlb= befehl.encode()
       self.ser.flushInput()
       self.ser.flushOutput()
       self.ser.write(befehlb)
       resunicode=self.ser.readline()
       self.res=resunicode.decode()
       self.res=self.res.rstrip('\r')      
       return self.res
 
 
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
