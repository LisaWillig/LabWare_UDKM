#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MagnetCommunication.py

Author: Lisa Willig
Created on Mon Dec 18 15:35:21 2017
Last Edited: 06.12.2018

Python Version: 3.6.5
4G Magnet Power Supply

Class for sending commands to 4G Magnet Power Supply

IMPORTANT: Magnet has to be in remote mode, can only 
be set locally
________________________________________
LIST OF COMMANDS:

IMAG? : Query Manget Current
IOUT? : Query Power Supply Output current
LLIM? : Query Low Current sweep limit
ULIM? : Query High Current sweep limit
VLIM? : Query Voltage limit
VMAG? : Query Magnet Voltage
VOUT? : Query Output Voltage
NAME? : Query Magnet Coil Name
RANGE?: Query range limit for seep rate boundary
RATE? : Query sweep rate for selected sweep range
UNITS?: Query selected Units
________________________________________
Available if magnet is set to remote

LLIM : Set Low Current sweep Limit
ULIM : Set High Current sweep limit
VLIM : Set Voltage limit
NAME : Set magnet coil name
RANGE : set range limit for seep rate boundary
RATE : Set sweep rate for selected sweep range
UNITS : Select Units
QRESET : Reset Quench condition

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import socket


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Network Communication Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MagnetController:
    """
    Class desinged for setting up and communicating with a 4G Magnet through
    Network connection.
    """

    BUFFER_SIZE = 4094

    def __init__(self):
        """
        Initialize communication with Network.
        """

        self.mysocket = socket.socket()

    def openConnection(self):
        """
        Open Communication with Magnet Controller. Host and Port can be found
        and set in the local controller display.
        """

        self.mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = '10.10.1.7'
        port = 4444
        self.mysocket.connect((host, port))

    def sendCommand(self, command):
        """
        Send the command with \r as EndOfLine Char.
        :param command: can be found in Magnet Manual.
        """

        self.mysocket.send((str(command)+" \r").encode())

    def receiveAnswer(self):
        """
        Read answer from device. Buffer Size is 4094.
        :return: answer as string
        """

        return self.mysocket.recv(self.BUFFER_SIZE).decode()

    def closeConnection(self):
        """
        Close Connection with Magnet and Network.
        """

        self.mysocket.close()

    def resetQuenchCondition(self):
        """
        QRESET Reset Quench Condition
        Availability: Remote Mode
        Command Syntax: QRESET

        Description: The QRESET command resets a power supply quench condition
        and returns the supply to STANDBY
        """

        self.sendCommand("QRESET")
        return 0

    def setMagnetCurrent(self, value):
        """
        IMAG Sets the magnet current (or magnetic field strength).
        Availability: Remote Mode
        Command Syntax: IMAG [value]
        Example: IMAG 47.1123
        Default Parameter: 0.0

        Parameter Range: ±Maximum Magnet Current
        Description: The IMAG command sets the magnet current shown on the
        display. The supply must be in standby or a command error will be
        returned. The value must be supplied in the selectedu nits - amperes
        or field (kG). If Shim Mode is enabled, the persistent mode current
        displayed for the named shim is set if the shim parameter is provided.

        :param value: ±Maximum Magnet Current
        """

        self.sendCommand("IMAG "+str(value))
        return self.receiveAnswer()

    def getMagnetCurrent(self):
        """
        IMAG? Query magnet current (or magnetic field strength)
        Availability: Always
        Command Syntax: IMAG?
        Response: <Magnet Current> <Units>
        Response Example: 87.9350 A

        Description: The IMAG? query returns the magnet current (or magnetic
        field strength) in the present units. If the persistent switch heater is
        ON the magnet current returned will be the same as the power supply
        output current. If the persistent switch heater is off, the magnet
        current will be the value of the power supply output current when the
        persistent switch heater was last turned off. The magnet current will
        be set to zero if the power supply detects a quench. If in SHIM mode,
        the IMAG? query reports the present current of the shim selected by
        the SHIM command in Amps. If the optional Shim ID is provided while
        in shim mode, the present current of the specified shim will
        be reported
        """

        self.sendCommand("IMAG?")
        return self.receiveAnswer()

    def getCurrentOutPowerSupply(self):

        """
        IOUT? Query power supply output current
        Availability: Always
        Command Syntax: IOUT?
        :return: <Output Current> <Units>
        Response Example: 87.935 A

        Description: The IOUT? query returns the power supply output current
        (or magnetic field strength) in the present units
        """

        self.sendCommand("IOUT?")
        return self.receiveAnswer()

    def setCurrentSweepLow(self, limit):
        """
        LLIM Set current sweep lower limit
        Availability: Remote Mode
        Command Syntax: LLIM [Limit]
        Example: LLIM 20.1250
        Default Parameter: 0.0

        Description: The LLIM command sets the current limit used when the next
        SWEEP DOWN command is issued. The value must be supplied in the
        selected units - amperes or field (kG). An error will be returned if
        this value is greater than the upper sweep limit

        :param limit: ±Maximum Magnet Current
        """
        self.sendCommand("LLIM "+str(limit))
        return 0

    def getCurrentSweepLowLimit(self):
        """
        LLIM? Query current sweep lower limit
        Availability: Always
        Command Syntax: LLIM?
        :return: <Limit> <Units>
        Response Example: 20.1250 A
        Response Range: ±Maximum Magnet Current

        Description: The LLIM? query returns the current limit used with the
        SWEEP DOWN command. It is issued in the selected units - amperes or
        field (kG).
        """

        self.sendCommand("LLIM?")
        return self.receiveAnswer()

    def setRangeLimitForSweep(self, select, limit):
        """
        RANGE Set range limit for sweep rate boundary
        Availability: Remote
        Command Syntax: RANGE <Select> <Limit>
        Example: RANGE 0 25.0
        Default Parameter: None

        Description: The RANGE command sets the upper limit for a charge rate
        range in amps. Range 0 starts at zero and ends at the limit provided.
        Range 1 starts at the Range 0 limit and ends at the Range 1 limit
        provided. Range 2 starts at the Range 1 limit and ends at the Range 2
        limit provided. Range 3 starts at the Range 2 limit and ends at the
        Range 3 limit provided. Range 4 starts at the Range 3 limit and ends
        at the supply output capacity

        :param select: 0 to 4
        :param limit: 0 to Max Supply Current
        """
        self.sendCommand("RANGE "+str(select)+" "+str(limit))
        return 0

    def getRangeLimitForSweep(self, select):
        """
        RANGE? Query range limit for sweep rate boundary
        Availability: Always
        Command Syntax: RANGE? <Select>
        Example: RANGE? 1 Parameter Range: 0 to 4
        :return:: <Limit>

        Response Example: 75.000 Response Range: 0 to Max Magnet Current
        Description: The RANGE? query returns the upper limit for a charge rate
        range in amps. See RANGE for further details.

        """
        self.sendCommand("RANGE? "+str(select))
        return self.receiveAnswer()

    def setRateForSweep(self, select, rate):
        """
        RATE Set sweep rate for selected sweep range
        Availability: Remote
        Command Syntax: RATE <Range> <Sweep Rate>
        Example: RATE 0 0.250
        Default Parameter: None

        Description: The RATE command sets the charge rate in amps/second for a
        selected range. A range parameter of 0, 1, 2, 3, and 4 will select
        Range 1, 2, 3, 4, or 5 sweep rates as displayed in the Rates Menu. A
        range parameter of 5 selects the Fast mode sweep rate.

        :param select:  0 to 5
        :param rate: 0 to Max Magnet Current
        """
        self.sendCommand("RATE "+str(select)+" "+str(rate))
        return 0

    def getRateForSweep(self, select):
        """
        RATE? Query range limit for sweep rate boundary
        Availability: Always
        Command Syntax: RATE? <Range>
        Example: RATE? 1
        Response Example: 0.125

        Description: The RATE? command queries the charge rate in amps/second
        for a selected range. A range parameter of 0 to 4 will select Range 1
        through 5 sweep rates as displayed in the Rates Menu. A range
        parameter of 5 queries the Fast mode sweep rate.

        :param select: 0 to 4
        :return:: <Rate>, 0 to Max Magnet Current
        """

        self.sendCommand("RATE? "+str(select))
        return self.receiveAnswer()

    def startSweep(self, mode, speed="SLOW"):
        """
        SWEEP Start output current sweep
        Availability: Remote Mode
        Command Syntax: SWEEP <Sweep Mode> [fast or slow]
        Examples: SWEEP UP
                  SWEEP UP FAST
        Default Parameter: None

        Description: The SWEEP command causes the power supply to sweep the
        output current from the present current to the specified limit at the
        applicable charge rate set by the range and rate
        commands. If the FAST parameter is given, the fast mode rate will be
        used instead of a rate selected from the output current range. SLOW
        is required to change from fast sweep. SWEEP UP sweeps to the Upper
        limit, SWEEP DOWN sweeps to the Lower limit, and SWEEP ZERO
        discharges the supply. If in Shim Mode, SWEEP LIMIT sweeps to the shim
        target current.

        :param mode: UP, DOWN, PAUSE, or ZERO
        :param speed: FAST, SLOW
        """

        self.sendCommand("SWEEP "+str(mode)+" "+str(speed))
        return 0

    def getSweepMode(self):
        """
        SWEEP? Query sweep mode
        Availability: Always
        Command Syntax: SWEEP?
        :return: <Mode> [fast]
        Response Example: sweep up fast
        Response Range: standby, sweep up, sweep down, sweep paused, or zeroing

        Description: The SWEEP? query returns the present sweep mode. If sweep
        is not active then 'sweep paused' is returned.
        """

        self.sendCommand("SWEEP?")
        return self.receiveAnswer()

    def setCurrentUpperLimitSweep(self, limit):
        """
        ULIM Set current sweep upper limit
        Availability: Remote Mode
        Command Syntax: ULIM [Limit]
        Example: ULIM 65.327
        Default Parameter: 0.0

        Description: The ULIM command sets the current limit used when the next
        SWEEP UP command is issued. The value must be supplied in the
        selected units - amperes or field (kG). An error will be
        returned if this value is less than the lower sweep limit

        :param limit: ±Maximum Supply Current
        """

        self.sendCommand("ULIM "+str(limit))
        return 0

    def getCurrentUpperLimitSweep(self):
        """
        ULIM? Query current sweep upper limit
        Availability: Always
        Command Syntax: ULIM?
        :return: <Limit> <Units>
        Response Example: 65.327 A
        Response Range: ±Maximum Supply Current

        Description: The ULIM? query returns the current limit used for the S
        WEEP UP command. It is issued in the selected units - amperes or
        field (kG).
        """

        self.sendCommand("ULIM?")
        return self.receiveAnswer()

    def setUnits(self, unit):
        """
        UNITS Select units
        Availability: Remote Mode
        Command Syntax: UNITS <Unit Selection>
        Example: UNITS A
        Parameter Range: A, G

        Description: The UNITS command sets the units to be used for all input
        and display operations. Units may be set to Amps or Gauss. The unit
        will autorange to display Gauss, Kilogauss or Tesla.

        :param unit: A, G
        """

        self.sendCommand("UNITS "+str(unit)+" ")
        print("UNITS "+str(unit))
        return 0

    def getUnits(self):
        """
        UNITS? Query selected units
        Availability: Always
        Command Syntax: UNITS?
        :return: <Selected Units>
        Response Example: G
        Response Range: A, G

        Description: The UNITS? command returns the units used for all input
        and display operations
        """

        self.sendCommand("UNITS?")
        return self.receiveAnswer()

    def setVoltageLimit(self, limit):
        """
        VLIM Set voltage limit
        Availability: Remote Mode
        Command Syntax: VLIM <Voltage Limit>
        Example: VLIM 5.0

        Description: The VLIM command sets the power supply output voltage
        limit to the voltage provided.
        :param limit: 0.0 to 10.0
        """

        self.sendCommand("VLIM "+str(limit))
        return 0

    def getVoltageLimit(self):
        """
        VLIM? Query voltage limit
        Availability: Always
        Command Syntax: VLIM?
        :return: <Voltage Limit>
        Response Example: 4.75 V
        Response Range: 0 to 10.00

        Description: The VLIM? command returns the power supply output voltage
        limit.
        """

        self.sendCommand("VLIM?")
        return self.receiveAnswer()

    def getMagnetVoltage(self):
        """
        VMAG? Query magnet voltage
        Availability: Always
        Command Syntax: VMAG?
        Response: <Magnet Voltage>
        Response Example: 4.75 V
        Response Range: -10.00 to +10

        Description: The VMAG? command returns the present magnet voltage
        """

        self.sendCommand("VMAG?")
        return self.receiveAnswer()

    def getOutputVoltage(self):
        """
        VOUT? Query output voltage
        Availability: Always
        Command Syntax: VOUT?
        :return: <Output Voltage>
        Response Example: 4.75 V
        Response Range: -12.80 to +12.80

        Description: The VOUT? command returns the present power supply
        output voltage
        """

        self.sendCommand("VOUT?")
        return self.receiveAnswer()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the StageCommunication Class.
    """
    Magnet = MagnetController()
    Magnet.openConnection()
    Magnet.resetQuenchCondition()

    print(Magnet.getMagnetCurrent())
    print(Magnet.getCurrentOutPowerSupply())

    Magnet.setCurrentSweepLow(1)
    print(Magnet.getCurrentSweepLowLimit())

    Magnet.setRangeLimitForSweep(0, 0.5)
    print(Magnet.getRangeLimitForSweep(0))

    Magnet.setCurrentUpperLimitSweep(1)
    print(Magnet.getCurrentUpperLimitSweep())

    Magnet.setRateForSweep(0, 1)
    print(Magnet.getRateForSweep(0))
    print(Magnet.getSweepMode())

    print(Magnet.getUnits())
    Magnet.setUnits("G")
    print(Magnet.getUnits())

    print(Magnet.getVoltageLimit())
    Magnet.setVoltageLimit("1.000V")
    print(Magnet.getVoltageLimit())

    print(Magnet.getMagnetVoltage())
    print(Magnet.getOutputVoltage())

    Magnet.closeConnection()

    #Magnet.setMagnetCurrent(value)
    #Magnet.startSweep(mode)


"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()