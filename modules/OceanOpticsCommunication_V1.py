#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OceanOpticsCommunication_V1.py

Author: Felix Stete, Lisa Willig
Last Edited: 16.12.2018

Python Version: 3.6.5
OceanOptics Spectrometer

Module for communication with an OceanOptics Spectrometer

"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import seabreeze.spectrometers as sb


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Class OceanOptics Communication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OOSpectrometer():

    def connectSpectrometer(self):
        """
        Connect first Spectrometer in the list of 
        devices returned from seabreeze.
        Set initial integration time. 

        :return: Spectrometer Object
        """

        print('initialising Spectrometer')
        self.devices = sb.list_devices()        
        self.spec = sb.Spectrometer(self.devices[0])
        print('connecting')
        self.spec.integration_time_micros(10000)
        
    def getWave(self):    
        """
        Get the wavelength of the Spectrometer.

        :return: Vector of wavelengths
        """

        return self.spec.wavelengths()

    def setIntTime(self, IntTime): 
         """
         Set the Integration Time of Spectrometer. 
         Unit of GUI entry is milliseconds (ms)
         Unit for Spectrometer is microseconds
         """
         
         IntTime = IntTime*1000 
         self.spec.integration_time_micros(IntTime)
        
    def getSpectrum(self):
        """
        Get a spectrum from the Spectrometer

        :return: Vector with measured Intensities,
        """

        return self.spec.intensities()
        
    def closeSpectrometer(self):
        """
        Close Spectrometer Communication.

        """
        self.spec.close()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the StageCommunication Class.
    """
    print('No test currently present')


"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()