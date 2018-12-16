#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NI_CardCommunication_V2.py

Author: Lisa Willig
Last Edited: 06.12.2018

Python Version: 3.6.5
nidaqmx Version: 0.5.7
NIDAQ Devices

Class to handle communication with National Instrument Measurement Cards. The
Python Package nidaqmx is provided by National Instruments

"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 1) Imports ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
import time as t
from colorama import Style, Fore


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Class NIDAQ Communication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class NI_CardCommunication:
    """
    Main Class Handeling the Communication between NIDAQ Measurement Cards.
    """

    def reset_device(self, Device):
        """
        Resets the device.
        :param Device:
        """

        Test = nidaqmx.system.device.Device(Device)
        Test.reset_device()

    def create_Task_ai(self, chan, bTrig=True):
        """
        Create a Task which reads Analog Input Channels
        :param chan: channels to include in the task. Can be a collection of
        channels, 2:5 creates a task including channels 2, 3, 4 and 5
        :param bTrig: determines if measurement is supposed to be triggered by
        Trigger Input of DAQ card (PFI0) - here triggered by Laser, shifted by
        500µs
        :return: Task
        """

        task = nidaqmx.Task()
        Channelname = str(chan)
        task.ai_channels.add_ai_voltage_chan(Channelname)
        if bTrig:
            task.timing.cfg_samp_clk_timing(
            1000, source="PFI0", sample_mode=AcquisitionType.CONTINUOUS,
            active_edge=nidaqmx.constants.Edge.RISING, samps_per_chan=1000)
            task.triggers.start_trigger.cfg_dig_edge_start_trig("PFI0")
        else:
            task.timing.cfg_samp_clk_timing(
                1000, sample_mode=AcquisitionType.CONTINUOUS)
        return task

    def create_Task_ao0(self, chan, bTrig=True):
        """
        Create a Task which writes to Analog Output Channels
        :param chan: channels to include in the task. Can be a collection of
        channels, 2:5 creates a task including channels 2, 3, 4 and 5
        :param bTrig: determines if measurement is supposed to be triggered by
        Trigger Input of DAQ card (PFI0) - here triggered by Laser, shifted by
        500µs
        :return: Task
        """

        task = nidaqmx.Task()
        task.ao_channels.add_ao_voltage_chan(
            str(chan), min_val=-10, max_val=10,
            units=nidaqmx.constants.VoltageUnits.VOLTS)
        if bTrig:
            task.timing.cfg_samp_clk_timing(
            1000, source="PFI0", sample_mode=AcquisitionType.CONTINUOUS,
            active_edge=nidaqmx.constants.Edge.RISING, samps_per_chan=1000)
            task.triggers.start_trigger.cfg_dig_edge_start_trig("PFI0")
        else:
            task.timing.cfg_samp_clk_timing(
                1000, sample_mode=AcquisitionType.CONTINUOUS)
        
        return task

    def create_Task_do(self, chan):
        """
        Create a Task which writes to Digital Output Channels
        :param chan: channels to include in the task. Can be a collection of
        channels, 2:5 creates a task including channels 2, 3, 4 and 5
        :param bTrig: determines if measurement is supposed to be triggered by
        Trigger Input of DAQ card (PFI0) - here triggered by Laser, shifted by
        500µs
        :return: Task
        """

        task = nidaqmx.Task()
        task.do_channels.add_do_chan(
            str(chan), "", nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES)
        task.start()
        return task

    def ReadValues_ai(self, task, LoopParams):
        """
        Read values for channels collected in task. The number of samples to be
        read are determined by the dictionary LoopParams['MeasurementPoints']
        values
        :param task:
        :param LoopParams: number of points to measure
        :return: data (list for each channel, length of measurementPoints)
        """

        data = task.read(
            number_of_samples_per_channel=LoopParams['MeasurementPoints'])
        task.stop()
        return data
        
    def WriteDigitalValue(self, value, task):
        """
        write a value to the specified task
        :param value: value to write
        :param task: channels to write to
        """

        task.write(value, auto_start=True)
        
    def WriteValues(self, task, value):
        """
        write a value to the specified task. Depending on the used power supply
        the calculation for the real value that is written to reach the
        goal value needs to be exchanged.

        :param value: value to write
        :param task: channels to write to
        """

        data_Write = self.Write_Constant_36V6A(value)
        task.write(data_Write, auto_start=True)
        task.stop()

    def WriteValuesZero(self, task):
        """
        Write Zero. Used at the end of a measurement to apply zero Voltage to
        reduce magnetic field.
        :param task: channels to write to
        """

        data_Write = self.Write_Zero()
        task.write(data_Write, auto_start=True)
        task.stop()
        
    def Write_SineFunction(self):
        """
        Create a sine funciton to write.
        :param task: channels to write to
        """

        frequency = 1
        amplitude = 1
        x = np.linspace(0, 1, 1000)
        y = amplitude*np.sin(x*np.pi*2*frequency)

        return y
    
    def damped_sineWave(self):
        """
        Create a damped sine funciton to write.
        :param task: channels to write to
        """

        amplitude = 1
        lam = 0.07
        xi = np.arange(0, 50, 2)
        frequency = 1
        yi = amplitude*np.exp(-lam*xi)*np.cos(xi*np.pi*frequency*2)
     
        return xi, yi
        
    def rampMagnetToZero(self, task):
        """
        Create a damped sine funciton to write that is effective in ramping
        the magnet too zero.
        :param task: channels to write to
        """

        x, y = self.damped_sineWave()
        Array = y 
        length = np.size(Array)
        resultList = np.zeros((length, 3))
        resultList[:, 0] = Array
    
        for i in range(length):
        
            self.WriteValues2(Array[i], task)
            t.sleep(0.2)

    def Write_Constant_20V20A(self, value):
        """
        Calculates the samples for the 20V - 20A Kepco Power Supply, when a
        constant value is necessary.
        :param value:
        :return: list with constant value for number of samples
        """

        return[value]*100
   
    def Write_Constant_36V6A(self, value):
        """
        Calculates the samples for the 36V - 6A Kepco Power Supply, when a
        constant value is necessary.
        :param value:
        :return: list with constant value for number of samples
        """

        return [value/0.6070497802]*1000
        
    def Write_Zero(self):
        """
        Calculates the samples for a Zero Signal when a
        constant value is necessary.
        :return: list with 0 for number of samples
        """

        y = 0
        y = [y]*100
        return y

    def CloseTask(self, task):
        """
        Close an opend task.
        :param task: task to close
        """

        task.close()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 2) Debug Class NI_CardCommunication ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class NI_CardCommunication_Debug:
    """
    Debug class for NiDAQ. Methods are mirrord to call them without Hardware
    connection.
    """

    def __init__(self):
        print(f'{Fore.GREEN}Debug! Measurement Card called{Style.RESET_ALL}')

    def reset_device(self, Device):
        print(f'{Fore.GREEN}Device{Style.RESET_ALL} '+str(Device)+' Reseted!')

    def create_Task_ai(self, chan):
        print(f'{Fore.GREEN}Analog In Task created for Channel:'
              f'{Style.RESET_ALL} '+str(chan))
        return 0

    def create_Task_ao0(self, chan):
        print(f'{Fore.GREEN}Analog OutTask created for Channel:'
              f'{Style.RESET_ALL} ' + str(chan))
        return 0

    def create_Task_do(self, chan):
        print(f'{Fore.GREEN}Digital OutTask created for Channel:'
              f'{Style.RESET_ALL} ' + str(chan))
        return 0

    def ReadValues_ai(self, task, LoopParams):
        data1 = np.random.sample((LoopParams['MeasurementPoints'], 3))
        N = LoopParams['MeasurementPoints']/2
        chop = np.array([-4] * int(N) + [4] * int(N))
        np.random.shuffle(chop)
        data3 = np.random.sample((LoopParams['MeasurementPoints'], 2))
        chop2 = chop.reshape(LoopParams['MeasurementPoints'], 1)
        data = np.concatenate((data1, chop2, data3), axis = 1)
        data = data.transpose()
        return data

    def WriteDigitalValue(self, value, task):
        print(f'{Fore.GREEN}NI Card wrote digital value: '+str(value))

    def WriteValues(self, task, value):
        data_Write = self.Write_Constant_36V6A(value)
        print(f'{Fore.GREEN}NI Card wrote AO values: '+str(value))

    def Write_SineFunction(self):
        frequency = 1
        amplitude = 1
        x = np.linspace(0, 1, 1000)
        y = amplitude * np.sin(x * np.pi * 2 * frequency)

        return y

    def damped_sineWave(self):
        amplitude = 1
        lam = 0.07
        xi = np.arange(0, 50, 2)
        frequency = 1
        yi = amplitude * np.exp(-lam * xi) * np.cos(xi * np.pi * frequency * 2)

        return xi, yi

    def rampMagnetToZero(self, task):
        x, y = self.damped_sineWave()
        Array = y
        length = np.size(Array)
        resultList = np.zeros((length, 3))
        resultList[:, 0] = Array

        for i in range(length):
            self.WriteValues2(Array[i], task)
            t.sleep(0.2)

    def Write_Rectanglefunction(self, voltage):
        frequency = 1.0
        amplitude = float(voltage)
        x = np.linspace(0, 1, 1000)
        y = np.sign(amplitude * np.sin(x * np.pi * 2 * frequency))

        return y

    def Write_Constant_20V20A(self, value):
        return [value] * 100  # List with constant Volt Output

    def Write_Constant_36V6A(self, value):
        return [value / 0.6070497802] * 1000  # List with constant Volt Output

    def CloseTask(self, task):
        print(f'{Fore.GREEN}NI Card Closed a task:{Style.RESET_ALL} '+str(task))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~ 3) Main Entry Point ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    main entry point. This gets called when it is not imported as a module.
    This is the environment for testing the StageCommunication Class.
    """
    MeasurementCard=NI_CardCommunication()
    MeasurementCard.reset_device("Dev1")
    WritingTask=MeasurementCard.create_Task_ao0("ao0")
    #NI_CardCommunication.CloseTask_Writing(WritingTask)
    DigitalIOTask=MeasurementCard.create_Task_do("port1/line3")
    MeasurementCard.WriteDigitalValue(True, DigitalIOTask)


"""
call the main() entry point only, if this script is the 
main script called, not imported.
"""

if __name__ == '__main__':
    main()