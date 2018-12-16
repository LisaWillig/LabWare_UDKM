#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MERedLab_Communication.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
MeasurementCard: Meilhaus MERedLab

Class to handle communication to the MERedLab DAQ Card. Interface cbw64.dll
provided by Meilhaus.

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
try:
    import Meilhaus.cbw as cbw
except ModuleNotFoundError:
    import modules.Meilhaus.cbw as cbw
import time as t
import ctypes
from colorama import Style, Fore

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) DAQ Card Communication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MECard:
    """
    Simple Class for writing a simple digital value to a port to the ME Card.
    """

    def __init__(self):
        """
        Initialize a single Port for Digital Output.
        :return: 1 if error, else None
        """

        self.meDll = ctypes.WinDLL("cbw64.dll")
        self.PortNum = cbw.AUXPORT
        Direction = cbw.DIGITALOUT
        self.BoardNum = 0
        ans = self.meDll.cbDConfigPort(self.BoardNum, self.PortNum, Direction)
        if ans:
            print("Error in Configuration of DO-Channel!: ", ans)
            return 1
        
    def setDigValue(self, value):
        """
        Set Digital value.
        :param value: 0,1
        :return: 1 if error, else 0
        """

        ans = self.meDll.cbDOut(self.BoardNum, self.PortNum, value)
        if ans:
            print("Error Setting DO value for Shutter!: ", ans)
            return 1
        return 0


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Debug Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MECard_Debug:
    """
    Debug Class mimicing Functions from Main class, can be used for Debugging
    purposes without connected Hardware.
    """

    def __init__(self):
        print(f'{Fore.GREEN}Debug! MEReDLab Measurement Card initialized\
        {Style.RESET_ALL}')

    def setDigValue(self, value):
        print(f'{Fore.GREEN}Debug! Shutter value set to:{Style.RESET_ALL} ',
              value)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 4) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the Meilhauscard.
    """

    Test = MECard()

    Test.setDigValue(1)
    t.sleep(0.1)  
    Test.setDigValue(0)
    t.sleep(2)  
    Test.setDigValue(1)
    t.sleep(2)
    Test.setDigValue(0)

    Test2 = MECard_Debug()
    Test2.setDigValue(1)
    Test2.setDigValue(0)


"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()
