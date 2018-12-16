#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
waveplatePowerCalibration.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5

Script to measure the Calibration file for the rotating waveplate. It measures
the total power as well as the reference value from the Reference Photodiode in
dependence of the waveplate angle. The resulting curve is saved interpolated.
As with the Magnet Hysteresis the old Calibration File found in the
"Calibration" Folder is moved to the "OldCalibrations" Folder and saved with
the date of movement.

Structure of this module:
1) Imports
2) Global Variables and Dictionaries
3) Directory and File System Management
4) Initialize Hardware and Measurement Variables
5) Measurement
6) Plot Results
7) Interpolate Results
8) Main Function

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# General Imports
import math
import os
import sys
import time as t
from datetime import datetime
import shutil

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

# Imports of own modules
from NI_CardCommunication_V2 import NI_CardCommunication
from PowermeterCommunication import Powermeter
from StageCommunication_V2 import StageCommunication
import utilities


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Global Variables and Dictionaries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
Stage_SpeedParams = {'Velocity': '4', 'Acceleration': '1'}
LoopParams = {'Loops': 1, 'MeasurementPoints': 500}


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
        if not os.path.exists(destinationFolder+"\\"+timeStamp):
            os.makedirs(destinationFolder+"\\"+timeStamp)
        listOfFiles = os.listdir(sourceFolder)
        for file in listOfFiles:
            shutil.move(sourceFolder+"\\"+file, destinationFolder+"\\" +
                        timeStamp+"\\")

    os.chdir(sourceFolder)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 4) Initialize Hardware and Measurement Variables ~~~~~~~~~~~~~~~~~~~~~~~ #
def createTimeStamp():
    """
    create a TimeStamp in format YYYYMMDD_HHMMSS for saving the old Calibration
    Files.
    :return: string timeStamp
    """
    return str(datetime.now().strftime("%Y%m%d_%H%M%S"))


def initializeMeasurementCard():
    """
    Communication for DAQ Measurement Cards from National Instruments

    :return: Measurement Card Object, Measurement Task
    """

    print('Initialize Card')
    MeasurementCard = NI_CardCommunication()
    MeasurementCard.reset_device("Dev2")
    MeasurementTask = MeasurementCard.create_Task_ai("Dev2/ai0:5")
    return MeasurementCard, MeasurementTask


def initializeWaveplate():
    """
    Initialize Waveplate - rotational motor communication
    with XPS Newport Controller
    Strings of Stage Name ('GROUP3', 'POSITIONER') are set in the
    Web Interface of the XPS Controller

    IMPORTANT: if waveplate is initialized, it will serach for its
    home position, it is not possible to influence serach direction.
    So the sample (or anything else) needs to be protected with shutter
    (or similar) from the possible high power.

    :return: Waveplate object
    """
    print('Initialize Waveplate')
    Waveplate = StageCommunication('GROUP3', 'POSITIONER')
    Waveplate.connectStage()
    Waveplate.setStageParams(Stage_SpeedParams)
    Waveplate.searchForHome()
    Waveplate.getCurrPos()
    return Waveplate


def initializeMeasurementArray():
    """
    Initialize Measurement Array based on the steps for the angles to move to
    :return: measurementArray, stageAngle
    """

    numberOfSteps = 100 / 0.5
    stageAngle = np.linspace(0, 100, int(numberOfSteps))
    measurementArray = np.zeros(shape=(len(stageAngle), 4))
    measurementArray[:, 0] = stageAngle
    return measurementArray, stageAngle


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 5) Measurement ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def measurement():
    """
    Set up Communication with Hardware
    Create Measurement Array and steps

    Measure: set angle for waveplate, measure power and reference
    Save the result with interpolation
    """

    Waveplate = initializeWaveplate()
    MeasurementCard, MeasurementTask = initializeMeasurementCard()
    measurementArray, stageAngle = initializeMeasurementArray()
        
    for idx, val in enumerate(stageAngle):

        # start communication with Powermeter.
        # It works more stbale if it is initiliazed every measurement.
        power = Powermeter()
        power.openCommunication()
        power.stStream()

        # Move Waveplate to angle
        print('Move to Angle: ', val)
        Waveplate.moveStage(val)
        stage = Waveplate.getCurrPos()

        # readData
        data = MeasurementCard.ReadValues_ai(MeasurementTask, LoopParams)
        measurementArray[idx, 1] = stage

        # Wait for some time unitil waveplate is moved
        t.sleep(1)

        # sometimes the powermeter returns nothing, so the array is empty and
        # it throughs an IndexError Excpetion. This appears to be less often if
        # it is initialized regularly.
        try:
            measurementArray[idx, 2] = power.readData()[0][0]
        except IndexError:
            measurementArray[idx, 2] = np.inf

        chopper = data[3]
        referenceDiode = data[5]
        refchop, refunchop = \
            utilities.sortAfterChopper(referenceDiode, chopper)

        measurementArray[idx, 3] = np.mean(refunchop)

        print('RefValue: ', np.mean(refunchop), 'Power: ',
              measurementArray[idx, 2], 'Angle: ', val)

        # save results
        np.savetxt('Calibration_PowervsWaveplateAngle_raw.txt',
                   measurementArray,
                   header='#angle Set (Degree)\t Angle measured (Degree)\t '
                          'Power (W)\t Reference Diode (V) ',
                   delimiter='\t')

        power.closeCommunication()

        # plot results during measurement
        plotResults(measurementArray)

    # close all Hardware Communication
    Waveplate.closeStage()
    MeasurementCard.CloseTask(MeasurementTask)
    return measurementArray


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 6) Plot Results ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def plotResults(measurementArray):
    """
    Plot the Results related to each other
    - Angle vs Power
    - Power vs Reference
    -> Angle vs Reference

    :param measurementArray:
    """

    plt.figure()
    plt.plot(measurementArray[:, 1], measurementArray[:, 2])
    plt.savefig('AngleVspower.png', dpi=300, transparent=False)
    plt.close()
    plt.figure()
    plt.plot(measurementArray[:, 2], measurementArray[:, 3])
    plt.savefig('PowerVsReference.png', dpi=300, transparent=False)
    plt.close()
    plt.figure()
    plt.plot(measurementArray[:, 1], measurementArray[:, 3])
    plt.savefig('AngleVsReference.png', dpi=300, transparent=False)
    plt.close()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 7) Interpolate Results ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def interpolation(data):
    """
    Interpolate the measured data. A measurement takes a long time for a lot of
    steps. The information gain compared to interpolation is not justifiyng the
    time spend. Most problematic are very low powers close to a zer reference
    value and very high powers in the flat part of the sine. The errors seem to
    be equally large: reference value jumps a lot if it is measured.

    :param data:
    """

    xnew = np.linspace(data[0, 0], data[len(data) - 1, 0], 10000)
    f = interp1d(data[:, 0], data[:, 2])
    dataRefSmooth = savgol_filter(data[:, 3], 51, 3)
    f_ref = interp1d(data[:, 0], dataRefSmooth, kind='cubic')

    plt.plot(xnew, f(xnew), 'ro', markersize=0.1, label="new interpolated")
    plt.plot(data[:, 0], data[:, 2], 'bo', markersize=0.5, label="raw data")
    plt.legend()
    plt.xlabel('Angle in Degree')
    plt.ylabel('Power in W with Chopper')
    plt.savefig('Interpolated_PowerCalibration.png', dpi=300)
    plt.show()

    plt.plot(xnew, f_ref(xnew), 'ro', markersize=0.1, label="new interpolated")
    plt.plot(data[:, 0], data[:, 3], 'bo', markersize=0.5, label="raw data")
    plt.legend()
    plt.xlabel('Ref in Volt')
    plt.ylabel('Power in W with Chopper')
    plt.savefig('Interpolated_RefCalibration.png', dpi=300)
    plt.show()

    newSet = np.vstack((xnew, f(xnew), f_ref(xnew)))
    np.savetxt("Calibration_PowervsWaveplateAngle.txt", newSet.T,
               header="Angle in Degree\t Power in W\t Ref in V")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 8) Main Function ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point.
    - Change the directory structure and file positions
    - do the measurement
    - interpolate the data
    - save
    """

    cleanUp()
    data = measurement()
    interpolation(data)

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()
