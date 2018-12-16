#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
StageCommunication_V2.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
Newport XPS Controller

Class to handle communication with Newport XPS Controller and the attached
stages. The low-level interface XPS() is provided by Newport.

"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
from XPS.XPS_ import XPS
import numpy as np
import sys
from colorama import Style, Fore

# globale Variablen
StageParams_mm = {}
Offset_mm = 75

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Class Stage Communication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class StageCommunication():
    """
    Main Class Handeling the Communication between XPS controller via XPS
    interface and the main program.
    """

    def __init__(self, groupname, positionername):
        """
        Initilize the Stage. groupname and positionername are set in the Web
        interface of XPS.
        :param groupname: string
        :param positionername: string
        """

        self.groupname = groupname
        self.positionername = '.'+str(positionername)
    
    def connectStage(self):
        """
        connect the stage: Open communication with the XPS controller.
        The stage needs to serach for home every time the communication is
        opened again, so be aware of possible dangers (waveplate rotating
        through maximum etc.)
        """

        self.myxps = XPS()
        self.socketId = self.myxps.TCP_ConnectToServer(b'10.10.1.2', 5001, 20)
        XPS.TCP_ConnectToServer
        if self.socketId == -1:
            print('Connection to XPS failed, check IP & Port')
            sys.exit()

        self.group = self.groupname.encode(encoding='utf-8')
        self.positioner = self.group + self.positionername.encode()
        self.myxps.GroupKill(self.socketId, self.group)
        self.myxps.GroupInitialize(self.socketId, self.group)
        self.searchForHome()

    def searchForHome(self):
        """
        Search for Home
        """

        [errorCode, returnString] =\
            self.myxps.GroupHomeSearch(self.socketId, self.group)

    def moveStage_absolute(self, value):
        """
        Move stage about an absolute value. This step is moved independent from
        the current Position.
        Steps to move = value
        :param value: absolute move value [mm]
        """

        [errorCode, returnString] = \
            self.myxps.GroupMoveAbsolute(self.socketId, self.positioner, [value])
        if errorCode != 0:
            print("Error: ", returnString)

    def moveStage(self, RelativeMoveX):
        """
        Move Stage relative to current position. The current Position is called
        and the movement necessary to reach the new position is calculated by:
        StepsToMove = RelativeMoveX - currentPosition
        :param RelativeMoveX [mm]
        """

        [errorCode, currentPosition] = \
            self.myxps.GroupPositionCurrentGet(self.socketId,
                                               self.positioner, 1)
        if errorCode != 0:
            print("Error: ", returnString)

        try:
            self.myxps.GroupMoveRelative(
            self.socketId, self.positioner,
            [(float(RelativeMoveX) - float(currentPosition))])
        except ValueError:
            pass

    def setStageParams(self, Stage_SpeedParams):
        """
        Set the Velocity and Acceleration of the Stage.
        :param Stage_SpeedParams['Velocity' [mm/s], 'Acceleration' [mm/s^2]]:
        """

        self.myxps.GroupJogParametersSet(self.socketId, self.group,
                                         Stage_SpeedParams['Velocity'],
                                         Stage_SpeedParams['Acceleration'])

    def getCurrPos(self):
        """
        Ask stage for current position in mm.
        :return: currentPosition
        """

        [errorCode, currentPosition] = \
            self.myxps.GroupPositionCurrentGet(self.socketId,
                                               self.positioner, 1)
        if errorCode != 0:
            print("Error: ", returnString)
        return currentPosition

    def closeStage(self):
        """
        Close Communication, kill the group of the Stage and free the XPS
        socket.
        """
    
        self.myxps.GroupKill(self.socketId, self.group)
        self.myxps.TCP_CloseSocket(self.socketId)

    def CalculateParameters_StageMove(self, StageParams_ps):
        """
        From an incoming Dictionary with Start and Stop of the stage values in
        Pikoseconds (ps) calculate the Milimeter movement needed for stage.
        Besides the calulation from the ps to mm values it is also necessary to
        subtract the offset of the stage. The "Home" and "0mm" value is set to
        the center of the stage, the lightway Zero point is set to the beginning
        of the stage. Additionally the light passes the delay of the stage two
        times.

        mm = ((pikolightway [ps] * 3/10 ) / 2) - Offset [mm]

        :param StageParams_ps:
        :return: StageParams_mm
        """
        for key, value in StageParams_ps.items():
            mm_value = (value*3/10)/2
            StageParams_mm[key] = mm_value

        StageParams_mm['StartPoint'] = StageParams_mm['StartPoint']-Offset_mm
        StageParams_mm['EndPoint'] = StageParams_mm['EndPoint']-Offset_mm

        return StageParams_mm

    def calculateStagemmFromps(self, Vec):
        """
        From an incoming Pikosecondsvector calculate the Millimeter Movement
        Vector for the stage.

        mm = ((pikolightway [ps] * 3/10 ) / 2) - Offset [mm]

        :param Vec: Stagepositionvector in ps
        :return: Stagepositionvektor in mm
        """

        Vec_Stagemm = np.copy(Vec)
        for idx, value in enumerate(Vec):
            mm_value = (value*3/10)/2
            Vec_Stagemm[idx] = mm_value-Offset_mm
        return Vec_Stagemm

    def calcLightWay(self, position):
        """
        Calculate the position in ps from an incoming mm value.

        pos [ps] = pos [mm] * 10/3 *2 + Offset [ps]
        :param position: in mm
        :return: position in ps
        """

        Offset_ps = (Offset_mm*10/3)*2
        return (float(position)*10/3)*2+Offset_ps

    def calcStageWay(self, position):
        """
        Calculate the position in mm from an incoming ps value.

        pos [mm] = pos [ps] * 3/10 / 2 - Offset [mm]
        :param position: in ps
        :return: position in mm
        """

        mm_value = (float(position) * 3 / 10) / 2 - Offset_mm
        return mm_value


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Debug Class StageCommunication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class StageCommunication_Debug():
    """
    Debug class for Stage. Methods are mirrord to call them without Hardware
    connection.
    """
    def __init__(self, groupname, positionername):

        print(f'{Fore.GREEN}Debug! \n Stage: Initialized{Style.RESET_ALL}')
        self.groupname = groupname
        self.positionername = '.' + str(positionername)

    def connectStage(self):
        print(f'{Fore.GREEN}Stage: connected!{Style.RESET_ALL}')

    def searchForHome(self):
        print(f'{Fore.GREEN}Stage: Searched for Home!{Style.RESET_ALL}')

    def moveStage_absolute(self, value):
        print(f'{Fore.GREEN}Stage: Moved absolute{Style.RESET_ALL}')

    def setStageParams(self, Stage_SpeedParams):
        print(f'{Fore.GREEN}Stage: did set Parameters{Style.RESET_ALL}')

    def getCurrPos(self):
        print(f'{Fore.GREEN}Stage: got current Position{Style.RESET_ALL}')
        return -100

    def moveStage(self, RelativeMoveX):
        print(f'{Fore.GREEN}Stage: Moved relative{Style.RESET_ALL}')

    def closeStage(self):
        print(f'{Fore.GREEN}Stage: Closed Connection{Style.RESET_ALL}')

    def CalculateParameters_StageMove(self, StageParams_ps):

        for key, value in StageParams_ps.items():
            mm_value = (value * 3 / 10) / 2
            StageParams_mm[key] = mm_value

        StageParams_mm['StartPoint'] = StageParams_mm['StartPoint'] - Offset_mm
        StageParams_mm['EndPoint'] = StageParams_mm['EndPoint'] - Offset_mm

        return StageParams_mm

    def calcStagemoveVector(self, Vec):

        Vec_Stagemm = np.copy(Vec)

        for idx, value in enumerate(Vec):
            mm_value = (value * 3 / 10) / 2
            Vec_Stagemm[idx] = mm_value - Offset_mm

        return Vec_Stagemm

    def calculateStagemmFromps(self, Vec):

        Vec_Stagemm = np.copy(Vec)

        for idx, value in enumerate(Vec):
            mm_value = (value * 3 / 10) / 2
            Vec_Stagemm[idx] = mm_value - Offset_mm

        return Vec_Stagemm

    def calcLightWay(self, Position):

        Offset_ps = (Offset_mm * 10 / 3) * 2
        Position_ps = (Position * 10 / 3) * 2 + Offset_ps

        return Position_ps


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the StageCommunication Class.
    """

    Stage = StageCommunication()

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()