#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowermeterCommunication.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
Powermeter 1919-R Newport

Class to handle communication with Newport Powermeter with interface
OphirLMMeasurement Interface provided by Newport.

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import pywintypes
#import pythoncom # Uncomment this if some other DLL load will fail
import win32com.client
import time as t

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Powermeter Communication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Powermeter():
    """
    Class Handeling the communication with Powermeter
    """
    
    def __init__(self):
        """
        create an interface client.
        Stop all current active Streams.
        """

        self.OphirCOM = \
            win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
        self.OphirCOM.StopAllStreams() 
        self.OphirCOM.CloseAll()
        
    def scanForDevices(self):
        """
        returns a list of connected USB Devices communicating over OphirCOM
        interface.
        :return: DeviceList
        """

        DeviceList = self.OphirCOM.ScanUSB()
        if len(DeviceList) == 0:
            print('No Device connected')
        return DeviceList
        
    def openCommunication(self):
        """
        Open Communication with first Device in Devicelist (for this setup and
        in the general case I expect only one Device to be connected at the
        same time)
        :return: active DeviceHandle
        """

        devices = self.scanForDevices()
        self.DeviceHandle = self.OphirCOM.OpenUSBDevice(devices[0])
        exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
        if not exists:
            print('Powermeter 1919-R: Device Not Found')

    def stStream(self):
        """
        Start stream of data and set the power range of the measurement.
        0 : Autorange.
        """

        autoRange = 0
        self.OphirCOM.SetRange(self.DeviceHandle, 0, autoRange)
        self.OphirCOM.StartStream(self.DeviceHandle, 0)
        
    def readData(self):
        """
        Read the data from the incoming stream with a waiting time of
        0.3 seconds.
        """

        t.sleep(.3)
        return self.OphirCOM.GetData(self.DeviceHandle, 0)

    def closeCommunication(self):
        """
        Close communication and measurement streams of all the devices.
        Release Interface Object
        """

        self.OphirCOM.StopAllStreams()
        self.OphirCOM.CloseAll()
        self.OphirCOM = None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the Powermeterclass.
    """

    test = Powermeter()
    test.openCommunication()
    for i in range(10):
        data = test.readData()[0]
        print(data[0])
    test.closeCommunication()

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()