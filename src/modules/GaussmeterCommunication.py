#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GaussmeterCommunication.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
pyserial Version: 3.4
Gaussmeter

Simple Interface class to handle serial communication with the Gaussmeter.

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import serial

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) COM Communication Gaussmeter ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Gaussmeter:
    """
    Class initializing Serial communication and read value.
    """

    def __init__(self):
        """
        Initialize serial port. Values are hardcoded, port needs to be changed
        for other configurations.
        """

        self.ser = serial.Serial()
        self.ser.port = 'COM5'
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 10

    def openCommunication(self):
        """
        Open serial communication.
        """

        self.ser.open()

    def readMagneticField(self):
        """
        Send the command "MEAS?\r" to the Gaussmeter to retrieve the current
        measured value. Return the answer as float
        :return: value (float)
        """

        befehl = ":MEAS?\r"
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.write(befehl.encode())
        res = (self.ser.readline()).decode()
        return float(res.rstrip('\n'))

    def closeGaussmeter(self):
        """
        Close communication with Gaussmeter/Close COM Port.
        """

        self.ser.close()
