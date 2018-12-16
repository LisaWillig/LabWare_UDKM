#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
magnetCalibration.py

Author: Alexander von Reppert, Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5

Script to read the magnetic field generated in relation to the voltage applied 
from the DAQ measurement card. Generated Calibration File.

Structure of this module:
1) Imports
2) Global Variables
3) Directory and File System Management
4) Initialize Hardware and Measurement Variables
5) Plot Result
6) Main Function

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1 ) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# General Imports
import os
import shutil
import sys
import time as t
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import serial
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode, Slope, \
    DigitalWidthUnits

# Imports of own modules
from GaussmeterCommunication import Gaussmeter
from NI_CardCommunication_V2 import NI_CardCommunication

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Global Variables ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
Measurementpoints = 10


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Directory and File System Management ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def cleanUp():
    """
    Method for managing the file and directory structure. If an older
    calibration is found in the directory "Calibration", it gets moved to the
    folder of "OldCalibrations" and is saved with the date of the movement.
    This ensures that the newest calibration is always found in the
    "Calibration" Folder.
    """

    # Definition of directory names
    sourceFolder = "Calibration"
    destinationFolder = "OldCalibrations"

    # Creates new directories if they dont exist already
    if not os.path.exists(sourceFolder):
        os.makedirs(sourceFolder)
    if not os.path.exists(destinationFolder):
        os.makedirs(destinationFolder)

    # checks if there is content in the Calibration folder
    # that needs to be moved
    # move content
    if len(os.listdir(sourceFolder)) != 0:
        timeStamp = createTimeStamp()
        if not os.path.exists(destinationFolder + "\\" + timeStamp):
            os.makedirs(destinationFolder + "\\" + timeStamp)
        listOfFiles = os.listdir(sourceFolder)
        for file in listOfFiles:
            shutil.move(sourceFolder + "\\" + file,
                        destinationFolder + "\\" + timeStamp + "\\")

    os.chdir(sourceFolder)


def createTimeStamp():
    """
    create a TimeStamp in format YYYYMMDD_HHMMSS for saving the old Calibration
    Files.
    :return: string timeStamp
    """

    return str(datetime.now().strftime("%Y%m%d_%H%M%S"))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 4) Initialize Hardware and Measurement Variables ~~~~~~~~~~~~~~~~~~~~~~~ #
def initializeWritingTask():
    """
    Initialize NI DAQ Measurement Task
    :return: NIDAQ Card Object, Task
    """

    measurementCard = NI_CardCommunication()
    measurementCard.reset_device("Dev1")
    task = measurementCard.create_Task_ao0("Dev1/ao0")

    return measurementCard, task


def initializeGaussmeter():
    """
    Initialize Communication with Gaussmeter
    :return: Gaussmeter Object
    """

    gauss = Gaussmeter()
    gauss.openCommunication()
    return gauss


def createMeasurementArray():
    """
    create the Array for which the values are measured.
    :return: Array : Measurement Parameters
    :return: resultList: List for entries
    """

    Amplitude = 5.1
    step = 0.05

    startArray = np.arange(0, Amplitude+step, step)
    loopArray1 = np.arange(Amplitude+step, -1*(Amplitude+step), -1*step)
    loopArray2 = np.arange(-1*(Amplitude+step), Amplitude+step, step)
    loopArray = np.concatenate([loopArray1, loopArray2])
    endArray = np.arange((Amplitude+step), 0-step, -step)

    Array = np.concatenate([startArray, loopArray, endArray])

    length = np.size(Array)
    resultList = np.zeros((length, 2))
    resultList[:, 0] = Array

    return resultList


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 5) Plot Result ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def plotHysteresis(resultList):
    """
    plot measured Hysteresis
    :param resultList:
    """

    plt.figure(figsize=(10, 6))
    plt.plot(resultList[:, 0], resultList[:, 1] * 1000, 'ob', lw=2, ms=2)
    plt.xlabel("Current (A)")
    plt.ylabel("B-Field (mT)")
    plt.grid()
    plt.yticks(
        np.arange(min(resultList[:, 1]) * 1000, max(resultList[:, 1]) * 1000,
                  50))
    plt.xticks(
        np.arange(min(resultList[:, 0]) + 0.5, max(resultList[:, 0]) + 0.5, 1))
    plt.savefig('HysteresisMagnet.png', dpi=300)
    np.savetxt('HysteresisMagnet.txt', resultList,
               header='#Current (A)\t B-field (T)')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 6) Main Function ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point.

    Checks for older calibration files, moves them in the date folder
    Starts Hardware Communication.
    Measures data and plot it
    Closes Hardware communication.
    """

    # initialize Hardware and Folder Structure
    cleanUp()
    measurementCard, writingTask = initializeWritingTask()
    resultList = createMeasurementArray()
    gauss = initializeGaussmeter()

    # Measure Data :
    # set voltage value,
    # wait (until magnet reacted),
    # read gaussmeter
    for i in range(np.size(reslutlist[:, 0])):
        measurementCard.WriteValues(writingTask, resultList[i, 0])
        t.sleep(0.5)
        resultList[i, 1] = gauss.readMagneticField()

    # close Hardware Communication
    measurementCard.CloseTask(writingTask)
    gauss.closeGaussmeter()

    plotHysteresis(resultList)

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()
