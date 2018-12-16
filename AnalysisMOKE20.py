import os
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from collections import OrderedDict
import matplotlib.pyplot as plt
import matplotlib.cm as cm

data = {}
normHysteresis_all = {}
normHysteresis_average = {}
timeHysteresis = {}
MOKE_Data = {}
Averaged_Data = {}
AllData = {}
PumpProbeData = {}
Information = {}
TeslaDict = {}


class DataAnalysisMOKE:

    def __init__(self, path, timeStamp):
        self.root = path
        self.filename = timeStamp
        self.textfilename = "AllData_Reduced"
        self.saveFilePath = str(self.root)+"//"+str(self.filename)+"//Analysis//"
        self.makeFolder(self.saveFilePath)
        self.makeFolder(self.saveFilePath+str("CompareLoops"))

    def readData(self):

        """
        read all the data files from one measurement series
        (saved as one timestamp)
        finds all files with the name (self.textfilename = "AllData_Reduced")
        and reads fluence as well as Voltage for the measurement.
        finds all hysteresis measurements (if they exist): static and
        time resolved
        saves all of the data in dictionaries
        :return: data in dictionaries
        """

        readFromPath = str(self.root) + "\\" + str(self.filename)
        rootdir = Path(readFromPath)
        AllData_List = [
            f for f in rootdir.resolve().glob('**/**/**/' +
                                              str(self.textfilename) +
                                              '.txt') if f.is_file()
                        ]
        Filelist = [0] * len(AllData_List)
        for idx, val in enumerate(AllData_List):
            Information[idx] = {}
            index = str(AllData_List[idx])
            head, tail = os.path.split(index)
            Filelist[idx] = head
            head, tailnew = head.split(str(self.filename) + str("\\"))

            InfoList = tailnew.split("\\")
            Information[idx]['Fluence'] = InfoList[1]
            Information[idx]['Voltage'] = InfoList[2]

        for idx, val in enumerate(AllData_List):
            os.chdir(str(Filelist[idx]))
            data[idx] = \
                pd.read_table(str(self.textfilename) + '.txt', delimiter='\t',
                              comment='%', header=0, skiprows=0,
                              error_bad_lines=False)

            # if no Hysteresis was measured (e.g. no Hysteresis folder exists):
            # stop reading data at this point
            try:
                os.chdir("../Hysteresis")
            except FileNotFoundError:
                return

            # read the static Hysteresis for each fluence measurement
            '''
            try:
                staticHyst = glob.glob('*_Staticps.txt')
                normHysteresis[idx] = \
                    pd.read_table(staticHyst[0], delimiter='\t', comment='%',
                                  header=0, skiprows=0, error_bad_lines=False)
            except FileNotFoundError:
                normHysteresis[idx] = 0
            '''
            try:
                staticHyst = glob.glob('*_6.666666666666686ps.txt')
                normHysteresis_all[idx] = \
                    pd.read_table(staticHyst[0], delimiter='\t', comment='%',
                                  header=0, skiprows=0, error_bad_lines=False)
            except FileNotFoundError:
                normHysteresis[idx] = 0

            # read the time resolved hysteresis for this measurement
            try:
                timeHyst = glob.glob('*ps.txt')
                timeHysteresis[idx] = {}
                for idx2, val2 in enumerate(timeHyst):
                    timeHysteresis[idx][idx2] = \
                        pd.read_table(timeHyst[idx2], delimiter='\t',
                                      comment='%', header=0, skiprows=0,
                                      error_bad_lines=False)
            except FileNotFoundError:
                timeHysteresis[idx] = 0


    def readLastTimeZero():
        """
        read t0 from the MeasurementParameterList
        if empty: return -1
        :return: t0
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

    def findNormValue():
        col = get_color_list(len(data.keys()), 'plasma')
        for key, value in data.items():
            frame = normHysteresis[key]
            frame['average'] = frame.iloc[:, 1:3].mean(axis=1)
            firstmax = frame['# #Voltage (V)'].idxmax()
            firstmin = frame['# #Voltage (V)'].idxmin()
            secondmax = frame['# #Voltage (V)'].loc[firstmin:].idxmax()

            branchStart = pd.DataFrame(
                {"Voltage": frame['# #Voltage (V)'].loc[0:firstmax],
                 "Hyst": ""})
            branchdown = pd.DataFrame(
                {"Voltage": frame['# #Voltage (V)'].loc[firstmax:firstmin],
                 "Hyst": ""})
            branchUp = pd.DataFrame(
                {"Voltage": frame['# #Voltage (V)'].loc[firstmin:secondmax],
                 "Hyst": ""})

            for i in range(0, firstmax + 1):
                branchStart['Hyst'].iloc[i] = frame['average'].iloc[i]

            newidx = 0

            for i in range(firstmax, firstmin + 1):
                branchdown['Hyst'].iloc[newidx] = frame['average'].iloc[i]
                newidx = newidx + 1

            newidx = 0
            for i in range(firstmin, secondmax + 1):
                branchUp['Hyst'].iloc[newidx] = frame['average'].iloc[i]
                newidx = newidx + 1

            newidx = 0
            for i in range(secondmax, len(frame['# #Voltage (V)'])):
                branchdown['Hyst'].iloc[newidx] = (branchdown['Hyst'].iloc[
                                                       newidx] +
                                                   frame['average'].iloc[i]) / 2
                newidx = newidx + 1

            AvgHyst = pd.concat([branchStart, branchUp[::-1], branchdown[::-1]])
            AvgHyst.set_index('Voltage', inplace=True)

            plotNormHysteresis(AvgHyst, firstmax, firstmin, key, col)
            plotAllNormHysteresis(AvgHyst, firstmax, firstmin, key, col)

    def averageHysteresis(self):

        for key, value in normHysteresis_all.items():
            data = value.values
            data[:, 0] = np.round(data[:, 0], 6)
            data1 = data[50:, :]

            selectIncreasing = np.diff(data1[:, 0]) > 0
            selectDecreasing = np.diff(data1[:, 0]) < 0
            data1 = data1[1:, :]
            currents = np.unique(data1[:, 0])
            results = np.zeros((np.size(currents), 6))

            counter = 0
            for c in currents:
                results[counter, 0] = c
                selectCurrent = data1[:, 0] == c
                select1 = selectCurrent & selectIncreasing
                select2 = selectCurrent & selectDecreasing
                results[counter, 1] = np.mean(data1[select1, 1])
                results[counter, 2] = np.mean(data1[select2, 1])
                results[counter, 3] = np.mean(data1[select1, 2])
                results[counter, 4] = np.mean(data1[select2, 2])
                #results[counter, 5] = TeslaDict[c] if c in TeslaDict else TeslaDict[
                #    min(TeslaDict.keys(), key=lambda k: abs(float(k) - float(c)))]
                results[counter, 5] = np.copy(results[counter, 1])

                counter += 1

            offset = np.mean(np.append(results[np.invert(np.isnan(
                results[:, 1])), 1],
                                       results[
                                           np.invert(np.isnan(results[:, 2])), 2]))

            t0 = 183
            results[:, 1] = results[:, 1]-offset
            results[:, 2] = results[:, 2]-offset
            results[:, 3] = results[:, 3]-offset
            results[:, 4] = results[:, 4]-offset
    def MOKE(self, dataframe, t0=readLastTimeZero(), deleteLoop=[]):

        for key, value in dataframe.items():
            print(key)
            # set timeZero
            if t0 == -1:
                Information[key]['t0'] = 0
            else:
                Information[key]['t0'] = t0

            # remove index column
            del value['Unnamed: 0']

            # calculate a time axis with coorected Zero and insert column
            # in dataframe
            StagePos = (value['StagePosition']).convert_objects(
                convert_numeric=True)
            StagePos = StagePos - float(Information[key]['t0'])
            value.insert(0, 'StagePos', StagePos)

            # round original column of magnetic field to either
            # positiv or negativ
            value['MagneticField'] = np.where(value['MagneticField'] > 0,
                                              1 *
                                              np.round(value['MagneticField'][0]),
                                              (-1 *
                                               np.round(value['MagneticField'][0]))
                                              )

            # Sort the values for Chopped and Unchopped as well as
            # positive and negative field
            ChopMPlus = value.loc[(value.loc[:, 'Chopper'] > 0) & (
                    value.loc[:, 'MagneticField'] > 0)]
            UnChopMPlus = value.loc[(value.loc[:, 'Chopper'] <= 0) & (
                    value.loc[:, 'MagneticField'] > 0)]
            ChopMMinus = value.loc[(value.loc[:, 'Chopper'] > 0) & (
                    value.loc[:, 'MagneticField'] < 0)]
            UnChopMMinus = value.loc[(value.loc[:, 'Chopper'] <= 0) & (
                    value.loc[:, 'MagneticField'] < 0)]

            # set loop and stage position as index

            ChopMPlus.set_index(['Loops', 'StagePos'], inplace=True)
            UnChopMPlus.set_index(['Loops', 'StagePos'], inplace=True)
            ChopMMinus.set_index(['Loops', 'StagePos'], inplace=True)
            UnChopMMinus.set_index(['Loops', 'StagePos'], inplace=True)

            PumpProbe = ChopMPlus.copy(deep=True)

            del PumpProbe['Diodesignal']
            #del PumpProbe['MinusDiode']
            #del PumpProbe['PlusDiode']
            #del PumpProbe['ReferenzDiode']
            del PumpProbe['Background']
            del PumpProbe['Chopper']
            del PumpProbe['MagneticField']

            AllData = PumpProbe.copy(deep=True)
            PumpProbe['Diodesignal_Plus'] = (ChopMPlus['Diodesignal'].values -
                                           UnChopMPlus['Diodesignal'].values)

            PumpProbe['Diodesignal_Minus'] = (ChopMMinus['Diodesignal'].values -
                                            UnChopMMinus['Diodesignal'].values)

            PumpProbe['Diodesignal_Minus'] = \
                PumpProbe['Diodesignal_Minus'].values[::-1]

            '''
            PumpProbe['Diode_Minus_Minus'] = (ChopMMinus['MinusDiode'].values -
                                            UnChopMMinus['MinusDiode'].values)

            PumpProbe['Diode_Minus_Plus'] = (ChopMPlus['MinusDiode'].values -
                                             UnChopMPlus['MinusDiode'].values)

            PumpProbe['Diode_Plus_Minus'] = (ChopMMinus['PlusDiode'].values -
                                              UnChopMMinus['PlusDiode'].values)

            PumpProbe['Diode_Plus_Plus'] = (ChopMPlus['PlusDiode'].values -
                                             UnChopMPlus['PlusDiode'].values)

            PumpProbe['ReferenceDiode_Plus_Minus'] = (ChopMMinus['ReferenzDiode'].values -
                                              UnChopMMinus['ReferenzDiode'].values)

            PumpProbe['ReferenceDiode_Plus_Minus'] = (ChopMPlus['ReferenzDiode'].values -
                                             UnChopMPlus['ReferenzDiode'].values)
            '''



            # drop specified loops
            for entry in deleteLoop:

                ChopMPlus = self.dropLoops(ChopMPlus, entry)
                UnChopMPlus = self.dropLoops(UnChopMPlus, entry)
                ChopMMinus = self.dropLoops(ChopMMinus, entry)
                UnChopMMinus = self.dropLoops(UnChopMMinus, entry)

            # Average All Loops
            ChopMPlus_AverageOverLoop = ChopMPlus.groupby(level=[1]).mean()
            ChopMMinus_AverageOverLoop = ChopMMinus.groupby(level=[1]).mean()
            UnChopMPlus_AverageOverLoop = UnChopMPlus.groupby(level=[1]).mean()
            UnChopMMinus_AverageOverLoop = UnChopMMinus.groupby(level=[1]).mean()

            # create MOKE dataframe
            MOKE_Average = ChopMPlus_AverageOverLoop.copy(deep=True)
            del MOKE_Average['Chopper']
            del MOKE_Average['MagneticField']

            Data_Average = pd.DataFrame(index=MOKE_Average.index,
                                        columns=['MOKESignal',
                                                 'ElectronicSignal',
                                                 'MinusDiode', 'PlusDiode',
                                                 'ReferenzDiode'])

            MOKE_Average['Diodesignal'] = (ChopMPlus_AverageOverLoop[
                                               'Diodesignal'].values -
                                           UnChopMPlus_AverageOverLoop[
                                               'Diodesignal'].values) - (
                                                  ChopMMinus_AverageOverLoop[
                                                      'Diodesignal'].values -
                                                  UnChopMMinus_AverageOverLoop[
                                                      'Diodesignal'].values)

            Data_Average['MOKESignal'] = MOKE_Average['Diodesignal']
            #Data_Average.set_index(['StagePos'], inplace=True)
            Data_Average['ElectronicSignal'] = (ChopMPlus_AverageOverLoop[
                                               'Diodesignal'].values -
                                           UnChopMPlus_AverageOverLoop[
                                               'Diodesignal'].values) + (
                                                  ChopMMinus_AverageOverLoop[
                                                      'Diodesignal'].values -
                                                  UnChopMMinus_AverageOverLoop[
                                                      'Diodesignal'].values)
            '''Data_Average['MinusDiode'] = (ChopMPlus_AverageOverLoop[
                                               'MinusDiode'].values +
                                          ChopMMinus_AverageOverLoop[
                                              'MinusDiode'].values) - (
                                          UnChopMPlus_AverageOverLoop[
                                            'MinusDiode'].values +
                                          UnChopMMinus_AverageOverLoop[
                                            'MinusDiode'].values) /\
                                         (UnChopMPlus_AverageOverLoop[
                                            'MinusDiode'].values +
                                          UnChopMMinus_AverageOverLoop[
                                            'MinusDiode'].values)
            Data_Average['PlusDiode'] = (ChopMPlus_AverageOverLoop[
                                               'PlusDiode'].values +
                                          ChopMMinus_AverageOverLoop[
                                              'PlusDiode'].values) - (
                                          UnChopMPlus_AverageOverLoop[
                                            'PlusDiode'].values +
                                          UnChopMMinus_AverageOverLoop[
                                            'PlusDiode'].values) /\
                                         (UnChopMPlus_AverageOverLoop[
                                            'PlusDiode'].values +
                                          UnChopMMinus_AverageOverLoop[
                                            'PlusDiode'].values)
            '''
            MOKE_Data[key] = MOKE_Average
            PumpProbeData[key]= PumpProbe
            Averaged_Data[key] = Data_Average

        return MOKE_Data, Data_Average

    def dropLoops(self, frame, loop):
        return frame.drop([loop], level='Loops')

    def plotCompareLoops_PumpProbe(self, PlotFrame, name= 'noName', xmin=np.inf,
                                   xmax=np.inf, ymin=np.inf, ymax=np.inf):
        for key, value in PlotFrame.items():
            if PlotFrame[key].empty == False:
                fig = plt.figure()
                fig.set_size_inches(18.5, 10.5)
                for loop in range(value.index.get_level_values(0).nunique()):
                    col = self.get_color_list(value.index.get_level_values(0).nunique(), 'viridis')
                    plt.plot(value.xs(loop+1, level='Loops').index.values, value.xs(loop+1, level='Loops')['Diodesignal_Plus'],
                             label=str(
                                 Information[key][
                                     'Fluence']) + "mJcm2 Loop:" + str(loop),
                                         color=col[loop], alpha=0.75)
                    plt.plot(value.xs(loop + 1, level='Loops').index.values, value.xs(loop + 1, level='Loops')['Diodesignal_Minus'],
                             label=str(
                                 Information[key]['Fluence']) + "mJcm2 Loop:" + str(loop),
                                color=col[loop], alpha=0.75)
                    if (xmin and xmax !=np.inf):
                        plt.xlim(xmin, xmax)
                    if (ymin and ymax != np.inf):
                        plt.ylim(ymin, ymax)
                    plt.legend()
                    handles, labels = plt.gca().get_legend_handles_labels()
                    by_label = OrderedDict(zip(labels, handles))
                    plt.legend(by_label.values(), by_label.keys())
                plt.savefig(str(self.saveFilePath)+str("CompareLoops\\")+'MOKE_CompareLoops_' + str(Information[key]['Fluence']) + 'mJcm2_.png', dpi=300,
                transparent=False)
            plt.close()

    def get_color_list(self, N, cmap):
        # returns a list of N rgb values extracted from the cmap
        cmap = cm.get_cmap(cmap, N)
        return cmap(np.arange(N))

    def makeFolder(self, Name):
        if not os.path.exists(Name):
            os.makedirs(Name)
            """
            This procedure creates an empty folder if the target Folder does not already exist. 
            Parameters
        ----------
        PathToFolder : string
            Path to the newly created folder

        Example
        -------
        >>> makeFolder("SubFolder/NewFolderName")
        Creates a new folder with the name "NewFolder" in the directory "SubFolder" 
        relative to the working path but only if this folder does not already exist.
        """

    def plotDataframeUnit(self, PlotFrame, unit, name ='', xmin=np.inf,
                                   xmax=np.inf, ymin=np.inf, ymax=np.inf):
        plt.figure()
        plt.clf()
        col = self.get_color_list(len(PlotFrame.keys()), 'plasma')
        for key, value in PlotFrame.items():
            if not PlotFrame[key].empty:
                y = pd.to_numeric(value[unit].values.tolist())
                x = pd.to_numeric(value.index.values.tolist())
                plt.plot(x, y,  label=str(Information[key]['Fluence']),
                        color=col[key])
                if (xmin and xmax != np.inf):
                    plt.xlim(xmin, xmax)
                if (ymin and ymax != np.inf):
                    plt.ylim(ymin, ymax)
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = OrderedDict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys())
                plt.savefig(str(self.saveFilePath)+str(unit)+str(name)+'.png', dpi=300)
        plt.show()
        plt.close()

    def readMagenticFieldFromLastFile(self):
        list_of_files = glob.glob('D:\\PythonSkripts\\MagnetfieldCalibration\\*.dat')
        latest_file = max(list_of_files, key=os.path.getctime)
        magRef = np.genfromtxt(latest_file)
        TeslaDict = dict(magRef)
        return TeslaDict

def main():
    analysis = DataAnalysisMOKE("D:\\Data\\MOKE_PumpProbe", "20180812_171227")
    analysis.readData()
    TeslaDict = analysis.readMagenticFieldFromLastFile()
    analysis.MOKE(data)
    analysis.averageHysteresis()
    #analysis.plotCompareLoops_PumpProbe(PumpProbeData)
    #analysis.plotDataframeUnit(Averaged_Data, 'MOKESignal')
    #analysis.plotDataframeUnit(Averaged_Data, 'ElectronicSignal')
    #analysis.plotDataframeUnit(Averaged_Data, 'ElectronicSignal',
     #                          name='_zoomed', xmin=-10, xmax=50)
    #analysis.plotDataframeUnit(Averaged_Data, 'ElectronicSignal',
     #                          name='_zoomed2', xmin=-10, xmax=200)



if __name__ == '__main__':
    main()
