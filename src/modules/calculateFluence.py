#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
calculateFluence.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5

Class to handle all calculations regarding Fluence and Power. Reads the FWHM
values from Beamprofile script. Checks the Calibration file of the rotational
Waveplate Motor for angle and reference value for power.

"""

# Imports
import numpy as np
import utilities


class Fluence:
    """
    Class calulating fluence and power. Returns reference value and angle of
    waveplate. Reads FWHM values from file. Calculates x0 and y0 values.
    """

    def calculateWaveplateAngle(self, P_c):
        """
        Returns a given Waveplate Angle and the reference diode value from
        calibration file. Returns 0 if no Calibration File is found.

        :param P_c: mW, value behind chopper
        :return: angleToMoveTo, goalReference
        """

        calibration = np.genfromtxt('D:\\PythonSkripts\\MOKE_TimeAndHysteresis_Fluence\\Calibration_PowerWaveplate\\Calibration\\Calibration_PowervsWaveplateAngle.txt')
        """Calibration_PowervsWaveplateAngle
        except OSError:
            try:
                calibration = \
                    np.genfromtxt('..\Calibration_PowerWaveplate\Calibration\Calibration_PowervsWaveplateAngle.txt')
            except OSError:
                print('Calibrationfile not found!')
                return 0, 0
        """
        powerInWatt = P_c*0.001
        calibration = calibration[calibration[:, 1].argsort()]
        try:
            index = np.searchsorted(calibration[:, 1], powerInWatt)
        except IndexError:
            calibration = calibration[:-1]
            index = np.searchsorted(calibration[:, 1], powerInWatt)

        angleToMoveTo = calibration[index, 0]
        goalReference = calibration[index, 2]
        
        return angleToMoveTo, goalReference

    def calculateFluenceFromPower(self, power):
        """
        Calculate the Fluence from a given Power value (behind the chopper, in
        mW). Reads FWHM from the BeamProfile Lists
        calculates x0 and y0 as the value of 1/e instead of 1/2 to not
        overestimate the fluence.

        Angle and Repetitionrate are hardcoded!

        Pulse Energy [Ws] = Power [W] / (Repitition Rate [Hz])
        Area of Pump [µm^2] = pi * y0 [µm] * x0 [µm]
        F [J/m^2] = Pulse Energy [Ws] /
                    ([Area [µm^2] * 10^-12] [m^2] * sin(angle))

        FmJ [mJ/cm^2] = F [J/m^2] * 10^-3 [mJ] * 10^4 [cm^2]
                      = F [J/m^2] + 10

        :param power: in mW after chopper
        :return: FmJ: Fluence in mJ/cm^2
        """

        FWHMx, FWHMy = utilities.readFWHMfromBeamprofile()
        repitionRate = 1000
        anglePump = 90
        x0, y0 = self.calculateX0(FWHMx, FWHMy)
        Ep = (2*power)/(repitionRate*1000);
        Area=np.pi*x0*y0
        F = Ep/(Area*1e-12)*np.sin(np.deg2rad(anglePump))
        FmJ=(F)/10
        return FmJ

    def calculateFluence(self, fluence):
        """
        Calculate the necessary Power (behind the chopper, in mW) from a goal
        fluence. Reads FWHM from the BeamProfile Lists
        calculates x0 and y0 as the value of 1/e instead of 1/2 to not
        overestimate the fluence.

        Angle and Repetitionrate are hardcoded!

        F [J/m^2] = fluence [mJ/cm^2] * 10
        Area of Pump [µm^2] = pi * y0 [µm] * x0 [µm]
        Pulse Energy [Ws] = F [J/m^2] * Area [µm^2] * 10^-12 / sin(angle)
        Power (behind Chopper) [mW] = Pulse Energy [J] * Repetition [Hz] *
                                    1000 [mW] / 2 (bc behind Chopper)

        :param power: in mW after chopper
        :return: FmJ: Fluence in mJ/cm^2
        """

        FWHMx, FWHMy = utilities.readFWHMfromBeamprofile()
        repitionRate = 1000
        anglePump = 90
        x0, y0 = self.calculateX0(FWHMx, FWHMy)
        F = float(fluence)*10
        Area = np.pi*x0*y0
        Ep = F*Area*1e-12/np.sin(np.deg2rad(anglePump))
        P_c = Ep*repitionRate*1000/2
        return P_c
 
    def getFWHM(self):
        """
        Read fitted FWHM values from Textfile with Pumpentries
        :return: FWHMx, FWHMy in µm
        """

        FWHMx, FWHMy = self.readFWHMfromBeamprofile()
        return FWHMx, FWHMy

    def calculateX0(self, FWHMx, FWHMy):
        """
        Calculate the 1/e values from the measured Full Width Half Maximum
        values
        :param FWHMx: µm value fitted from Beamprofile
        :param FWHMy: µm value fitted from Beamprofile
        :return: 1/e x, 1/e y
        """

        Variante2Factor = 2*np.sqrt(np.log(2))
        x0 = float(FWHMx)/Variante2Factor
        y0 = float(FWHMy)/Variante2Factor
        return x0, y0

def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the results of the calculations and
    other operations for accuracy.
    """

    flu = Fluence()
    P_c=flu.calculateFluence(5)
    print(P_c)
    F = flu.calculateFluenceFromPower(45)
    flu.calculateWaveplateAngle(P_c)

"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()