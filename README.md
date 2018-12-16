# LabWare_UDKM
Labratory Framework for several Experiments and Hardware Devices used in the research group [Ultrafast Dynamics of Condensed Matter](http://www.udkm.physik.uni-potsdam.de/).

## Status 

This is a snapshot of the Ongoing development of the software developed for performing communication with different Hardware devices in several experiments and labratories. 

## Application Structures

In this repository the overall structure is as follows: the single application files are in the root directory. User Interfaces are stored in the src\GUI subfolder. 
The interfaces between Hardware and main application can be found in the src\modules subfolder, together with some calculation modules. 
The main application "TimeResolvedMOKE.py" also requires Calibration Files, found in the respective folders, as well as measurement 
parameters, placed in the subfolder "MeasureParams". Parts of the Hardware Communication provided by the respective Company are omitted. 

### Time Resolved MOKE Measurement

The main experiment is realted to the file "TimeResolvedMOKE.py". 
It controls the Hardware Communication, Data Acquisition and Data Analysis for the experimental ultrafast laser setup for measuring 
the Magneto-Optical Kerr Effect (MOKE) both static and Time-Resolved in the Pump-Probe Configuration. Related to that experiment is the 
reading of signals from the DAQ Measurement Card: "SimpleDAQSignal.py". Additionally the single elements of the main application can be used seperately:

src\
  * TimeResolvedMOKE
    * modules
      * [HardwareCommunications]
    * GUI
    * MeasureParams
    * [Calibration_Files]
  
  * SimpleDAQSignal
  * SimpleShutter
  * SimpleHysteresis

![Automated Time Resolved MOKE Measurement](/images/TRMOKE_Screenshot.png)

### Other Applications

For Pump-Probe measurements with an OceanOptics spectrometer the file "SpectroPumpProbe.py" is written. 
The same experiment structure is also in development for spectrometers from Avantes. 
The beamstabilization is used for continuous monitoring of laser movement during measurement and correction of the laser path in case of thermal drifts.

![PumpProbe Spectroscopy](/images/PumpProbeFrog_Screenshot.png)

