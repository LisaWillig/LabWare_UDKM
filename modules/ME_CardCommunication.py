#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BaslerCommunication.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
Meilhaus Measurement Card

Template for Communication with the ME DAW Measurement Card. Only the reading
of the analog input is created.

"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import ctypes
import time as t


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Definitions of C++ Structures and Variables ~~~~~~~~~~~~~~~~~~~~~~~~~ #

class struct_meIOSingle(ctypes.Structure):
    pass

struct_meIOSingle.__slots__ = [
    'iDevice',
    'iSubdevice',
    'iChannel',
    'iDir',
    'iValue',
    'iTimeOut',
    'iFlags',
    'iErrno',
]
struct_meIOSingle._fields_ = [
    ('iDevice', ctypes.c_int),
    ('iSubdevice', ctypes.c_int),
    ('iChannel', ctypes.c_int),
    ('iDir', ctypes.c_int),
    ('iValue', ctypes.c_int),
    ('iTimeOut', ctypes.c_int),
    ('iFlags', ctypes.c_int),
    ('iErrno', ctypes.c_int),
]

meIOSingle_t = struct_meIOSingle

# Constants
ME_DEVICE_NAME_MAX_COUNT = 64
ME_REF_AI_GROUND = 327681
ME_TRIG_CHAN_DEFAULT = 458753
ME_TRIG_TYPE_SW = 524289
ME_VALUE_NOT_USED = 0
ME_IO_RESET_DEVICE_NO_FLAGS = 0
ME_IO_SINGLE_CONFIG_NO_FLAGS = 0
ME_TRIG_TYPE_EDGE = 589831
ME_IO_SINGLE_NO_FLAGS = 0


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Class ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class MECard():
    """
    Class calling the Meilhaus main .dll Function for this group of measurement
    cards.
    - open communication
    - set C++ Structures and Variables
    - set measurement parameters
    - measure signal
    """

    def __init__(self):
        self.meDll = ctypes.CDLL ("Meilhaus\\meIDSmain.dll")

        #Close OPen Connection, Open New Connection, Reset Task
        self.meDll.meClose()
        self.meDll.meOpen(ctypes.c_int32(ME_IO_RESET_DEVICE_NO_FLAGS))
        self.meDll.meIOResetDevice(ctypes.c_int32(0),
                                   ctypes.c_int32(ME_IO_RESET_DEVICE_NO_FLAGS))

        #Definition Read Function
        self.meIOSingle = self.meDll.meIOSingle
        self.meIOSingle.argtypes = [ctypes.POINTER(struct_meIOSingle),
                                    ctypes.c_int, ctypes.c_int]
        self.meIOSingle.restype = ctypes.c_int

        #Definition Convert Function
        self.convert=self.meDll.meUtilityDigitalToPhysical
        self.convert.argtypes=[ctypes.c_double, ctypes.c_double, ctypes.c_int,
                               ctypes.c_int, ctypes.c_int,
                               ctypes.c_double,
                               ctypes.POINTER(ctypes.c_double)]
        self.convert.restype = ctypes.c_int

        #Definition Configuration Function
        meIOSingleConfig = self.meDll.meIOSingleConfig
        meIOSingleConfig.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, ctypes.c_int]
        meIOSingleConfig.restype = ctypes.c_int

        #Configure Device
        i_me_error = meIOSingleConfig(  0,			         # Device index
							    4,		                     # Subdevice index, 4: Analog Input
							    1,							 # Channel index
								0,							 # Range index
								ME_REF_AI_GROUND,			 # Reference
								ME_TRIG_CHAN_DEFAULT,		 # Trigger channel - standard
								ME_TRIG_TYPE_SW,			 # Trigger type - software
                                ME_TRIG_TYPE_EDGE,
								ME_VALUE_NOT_USED,			 # Trigger edge - not applicable
								ME_IO_SINGLE_CONFIG_NO_FLAGS)# Flags

    def getSingleAIValue(self):
        """
        read out C++ Structure. The variables correspond to:
            Device, Subdevice, Channel, Direction (read or write), value,
            Timeout, Flags
        :return: value
        """

        io_single=meIOSingle_t(0,4,1,983041,0,0)
        i_me_error2 = self.meIOSingle(ctypes.byref(io_single),	    # Output list
		    	    						1,						# Number of elements in the above list
			    	    					ME_IO_SINGLE_NO_FLAGS)  # Flags
        return io_single.iValue

    def convertDigitalToPhysical(self, value):
        """
        Call function to convert digital value to physically meaningful.
        :param value: read digital value
        :return: physical value
        """

        b=ctypes.c_double()
        self.meDll.meUtilityDigitalToPhysical(-10,10,65535,value,0, 0,
                                              ctypes.byref(b))
        return(b.value)
        
    def measure(self):
        """
        start measurement, set parameters, convert read digital value to
        physically meaningfull.
        :return: measurement value in Volt
        """

        digitalvalue=self.getSingleAIValue()
        value=self.convertDigitalToPhysical(digitalvalue)
        return value

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the Powermeterclass.
    """
    test=MECard()
    print(test.measure())

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
        main()