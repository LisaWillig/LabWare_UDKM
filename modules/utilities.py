#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
utilities.py

Author: Lisa Willig
Last Edited: 30.11.2018

Python Version: 3.6.5

Static methods supproting the TRMOKE_V20 and other applications.

Structure of this module:
1) Imports
2) Static Methods - calculate Vectors from given Inputs
3) Message method
4) Math methods
5) Save Operation methods
"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

import numpy as np
import smtplib
import math
import os

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Vector Calculations ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def readStageFromGui(StageParams_ps):
    """
    From the values Start, Stop and Stepwidth the simple linear Stage Vector
    gets calculated
    :param StageParams_ps:
    :return: stageVector_ps
    """

    Stepnumber = \
        (float(StageParams_ps['EndPoint']) - StageParams_ps['StartPoint']) / \
        float(StageParams_ps['StepWidth'])
    Vec = np.linspace(
        float(StageParams_ps['StartPoint']), float(StageParams_ps['EndPoint']),
        int(Stepnumber), endpoint=True)

    return Vec

def readStageFromFile():
    """
    From the values given in the data file the complete Stage Vector is created.
    Each line in file represents one linear segment of the Stage Delay Vector
    Consisting of Start : Stop : Stepwidth with MatlabSyntax
    (, : delimiter, . : Decimal Point)

    :return: stageVector_ps
    """

    Vector = []
    Vector_total = []
    with open('MeasureParams\\StageParams.txt') as f:
        for line in f:
            Vector.append(line.strip().split(','))
            SaveVector = Vector
        for entry in Vector:
            Stepnumber = (int(entry[1]) - int(entry[0])) / float(entry[2])
            Vector_total.extend(np.linspace(int(entry[0]), int(entry[1]),
                                            int(Stepnumber), endpoint=True))
        Vec = []
    for entry, x in enumerate(Vector_total):
        Vec.append(x)

    return Vec, SaveVector


def readVoltageFromFile():
    """
    Create Voltage Vector by reading entries from file

    :return: voltageVector
    """

    Vector = []
    with open('MeasureParams\\VoltageParams.txt') as f:
        for line in f:
            Vector.append(line.strip().split(','))
    voltageVector = Vector[0]
    return voltageVector


def readFluenceFromFile():
    """
    Create Fluence Vector by reading entries from file

    :return: fluenceVector
    """

    Vector = []
    with open('MeasureParams\\FluenceParams.txt') as f:
        for line in f:
            Vector.append(line.strip().split(','))
    fluenceVector = Vector[0]
    return fluenceVector


def readHysteresisDelayfromFile(timeZero):
    """
    Read and create Hysteresis Delays from File. The values are given relative
    to the timezero (so -20 means 20ps before the set t0).
    The returned value is the absolute ps Delay for the setting of the stage.

    :param timeZero:
    :return: delayVector
    """
    Vector = []
    delayVector = []

    with open('MeasureParams\\HysteresisDelayParams.txt') as f:
        for line in f:
            Vector.append(line.strip().split(','))

    for entry in Vector[0]:
        delayVector.append(timeZero + float(entry))
    return delayVector


def readHysteresisDelayfromGUI(delay, timeZero):
    """
    Read and create Hysteresis Delays from GUI. The values are given relative
    to the timezero (so -20 means 20ps before the set t0).
    The returned value is the absolute ps Delay for the setting of the stage.

    :param delay, timeZero:
    :return: delayVector
    """
    delayVector = [s.strip() for s in str(delay).split(',')]
    for idx, val in enumerate(delayVector):
        delayVector[idx] = timeZero + float(val)

    return delayVector

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Message Method ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def sendEmail(msg):
    """
    Can be used to send an email from the Labemailadress (found in UDKM Wiki)

    :param msg: message to be send
    :return:
    """
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    # Login: emailadress, password
    server.login("...", "...")

    #email send, email receiver, message
    server.sendmail("...", "...", msg)
    server.quit()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 4) Math methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def sortAfterChopperSanityCheck(toSort, chopper):
    """
    Return the averaged value for chopped and unchopped values from the list
    (length of each list determined by repeat number).
    The list of the Chopper Diode (returned from the Thorlabs Chopper Trigger
    Out) is reference value for sorting.

    it also returns a boolean value (0, 1) which describes if the condition is
    fullfilled, that both lists are not empty.

    :param toSort: Property to be sorted
    :param chopper: value which is defining the sorting
    :return: ChopEntry, UnChopentry, Sanity = True
    """

    chop = [val for idx, val in enumerate(toSort) if chopper[idx] < 2]
    unchop = [val for idx, val in enumerate(toSort) if chopper[idx] > 2]

    if len(chop) == 0 or len(unchop) == 0:
        return 0, 0, 1
    else:
        ChopEntry = averageListEntry(chop)
        UnChopEntry = averageListEntry(unchop)
        return ChopEntry, UnChopEntry, 0


def sortAfterChopper(toSort, chopper):
    """
    Return the averaged value for chopped and unchopped values from the list
    (length of each list determined by repeat number).
    The list of the Chopper Diode (returned from the Thorlabs Chopper Trigger
    Out) is reference value for sorting.

    :param toSort: Property to be sorted
    :param chopper: value which is defining the sorting
    :return: ChopEntry, UnChopentry
    """

    chop = [val for idx, val in enumerate(toSort) if chopper[idx] < 2]
    unchop = [val for idx, val in enumerate(toSort) if chopper[idx] > 2]

    ChopEntry = averageListEntry(chop)
    UnChopEntry = averageListEntry(unchop)

    return ChopEntry, UnChopEntry


def averageListEntry(datalist):
    """
    Return the average value of a Python List
    :param datalist:
    :return: average of list
    """

    return sum(datalist)/len(datalist)


def listLength(list1, list2):
    """
    Checks the length of two Python Lists. If the length is not equal,
    the shoerter one is filled with infinite values.
    :param list1: shorter list
    :param list2: list to compare against
    :return: corrected list1
    """

    if len(list1) != len(list2):
        Diff = abs(len(list2) - len(list1))
        list1 = list1 + Diff * [math.inf]
    else:
        list1 = list1
    return list1


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 5) Saving Methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def readLastTimeZero():
    """
    Open the MeasurementList and read the last entry in the column of TimeZero.
    This gets loaded into the GUI. If it didn't change, the User does not need
    to change the input.
    If no value or no Measurementlist can be found, -1 is returned.
    :return: TimeZero, -1 as error return
    """

    filename = "D:\\Data\\TRMOKE_MeasurementParameterList.dat"
    if os.path.isfile(filename):
        fileHandle = open(filename, "r")
        lineList = fileHandle.readlines()
        fileHandle.close()
        try:
            lastline = np.fromstring(lineList[-1], dtype=float, sep=' \t')
            return lastline[5]
        except IndexError:
            return -1
    else:
        return -1


def readFWHMfromBeamprofile():
    """
    Read the calculatet FWHM values from the Beamprofile from the corresponding
    file. If no file is found, Zero is returned.

    :return: FWHMx, FWHMy
    """

    filename = 'D:\Data\BeamProfiles\Pump.txt'
    try:
        with open(filename, 'r') as file:
            lines = file.read().splitlines()
            last_line = lines[-1]
        FWHMx = last_line.split('\t')[0]
        FWHMy = last_line.split('\t')[1]
    except FileNotFoundError:
        FWHMx = '0'
        FWHMy = '0'
    return FWHMx, FWHMy


def partTimeStamp(timeStamp):
    """
    Part the TimeStamp into date and time for writing in
    Measurementparameterlist
    :param timeStamp:
    :return: date, time
    """

    date = timeStamp.split('_')[0]
    time = timeStamp.split('_')[1]
    return date, time


def createOrOpenMeasurementParameterList():
    """
    Method opens the Measurementparameterlist or creates a new one with header,
    if no file is found.
    :return: file object
    """

    header = False
    fn = "D:\\Data\\TRMOKE_MeasurementParameterList.dat"
    file = open(fn, 'a+')
    if os.stat(fn).st_size == 0:
        header = True
    if header:
        file.write('#Date [YYYYMMDD]\t Time [HHMMSS]\t Voltage [V]\t '
                   'Power behind Chopper [mW]\t Temperature [Kelvin]\t t0 [ps]\t'
                   'FWHMx [µm]\t FWHMy [µm]\t angle [degree]\t Samplename\n')

    return file
