import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime
import sys
import os
from datetime import datetime
from PyQt5 import QtGui, uic
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from pyqtgraph.Qt import QtGui, QtCore
import time as t
from matplotlib import cm
from scipy.optimize import curve_fit

from MirrorCommunication import MirrorCom
from BaslerCommunication import BaslerMultiple as Basler


CamsToUse = 2
exposureTime = 75000 #muS
SavingDestination = "C:\\PythonSoftware\\BeamStabilization"
camMirror = {0: {"cam1": "mirror1"}, 1: {"cam2": "mirror2"}}
lineInfinite={}
Mirror_Calculations = dict()
MirrorStatus = dict()
imgColormap = "inferno"


class Worker(PyQt5.QtCore.QRunnable):

    def __init__(self):
        super(Worker, self).__init__()

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        '''
        Your code goes in this function
        '''
        print("Thread start")
        self.mirror = MirrorCom()
        #self.resetMirrroSettings()
        for i in range(CamsToUse):
            self.mirror.setSettings((i+1), 50)

        self.moveMirrors()
        print("Thread complete")


    def centerOffset(self, i, coordinate, variable):
        return Mirror_Calculations[i][coordinate]-len(
            Mirror_Calculations[0][variable])/2

    def moveMirrors(self):
        while 'true' in MirrorStatus[0].values():
            if MirrorStatus[0]["bMoveX"]:
                    if self.centerOffset(0, "CenterGauss_X", "SumX") < 0:
                        self.mirror.moveChannel(1, 1, -1)
                    else:
                        self.mirror.moveChannel(1, 1, 1)

            if MirrorStatus[0]["bMoveY"]:
                    if self.centerOffset(0, "CenterGauss_Y", "SumY") < 0:
                        self.mirror.moveChannel(1, 2, 1)
                    else:
                        self.mirror.moveChannel(1, 2, -1)

        while 'true' in MirrorStatus[1].values():
            if not MirrorStatus[0]["bMoveX"]:
                if MirrorStatus[1]["bMoveX"]:
                    if self.centerOffset(1, "CenterGauss_X", "SumX") < 0:
                        self.mirror.moveChannel(2, 1, 1)
                    else:
                        self.mirror.moveChannel(2, 1, -1)

            if not MirrorStatus[0]["bMoveY"]:
                if MirrorStatus[1]["bMoveY"]:
                    if self.centerOffset(1, "CenterGauss_Y", "SumY") < 0:
                        self.mirror.moveChannel(2, 2, 1)
                    else:
                        self.mirror.moveChannel(2, 2, -1)


class Logging():

    def __init__(self):
        self.createFolderAndFile()

    def createFolderAndFile(self):
        if not os.path.exists(SavingDestination+"\\Logging"):
            os.makedirs(SavingDestination+"\\Logging")
        os.chdir(SavingDestination+"\\Logging")
        self.timeStamp = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.file = open(str(self.timeStamp), 'a+')

        self.file.write('# timeStamp\t FWHMX1\t FWHMY1\t FWHMX2\t '
                        'FWHMY2\tGausscenterX1\t '
                        'GausscenterX2\t '
                   'GausscenterY1\t GausscenterY2\t CoM_X1\t CoM_X2\t '
                        'CoM_Y1\tCoM_Y2\n')

    def saveValues(self, ):
        self.file.write(str(datetime.now().strftime("%Y%m%d_%H%M%S")) + '\t')

        self.file.write(str(Mirror_Calculations[0]["FWHM_X"])+'\t')
        self.file.write(str(Mirror_Calculations[0]["FWHM_Y"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["FWHM_X"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["FWHM_Y"]) + '\t')

        self.file.write(str(Mirror_Calculations[0]["CenterGauss_X"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["CenterGauss_X"]) + '\t')

        self.file.write(str(Mirror_Calculations[0]["CenterGauss_Y"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["CenterGauss_Y"]) + '\t')

        self.file.write(str(Mirror_Calculations[0]["Index_CoM_X"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["Index_CoM_X"]) + '\t')

        self.file.write(str(Mirror_Calculations[0]["Index_CoM_Y"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["Index_CoM_Y"]) + '\t')

        self.file.write(str(Mirror_Calculations[0]["Center_GaussFitX"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["Center_GaussFitX"]) + '\t')

        self.file.write(str(Mirror_Calculations[0]["Center_GaussFitY"]) + '\t')
        self.file.write(str(Mirror_Calculations[1]["Center_GaussFitY"]) + '\n')

    def closeFile(self):

        self.file.close()


class MyWindow(PyQt5.QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        super(MyWindow, self).__init__(parent)
        self.ui = uic.loadUi('GUI\\Beamstabilization_V1.ui', self)

        self.init_ui()
        self.show()

        self.status = "Adjusting"
        self.log = None
        self.config=None
        self.setNew = None

        self.blog = 0

        self.btn_Exit.clicked.connect(self.close)
        self.btn_Start.clicked.connect(self.startAligning)
        self.btn_SetNewPos.clicked.connect(self.newCenter)

        self.Main()
        #self.btn_Stop.clicked.connect(self.OnlyRead)

    def startAligning(self):
        self.threadpool = PyQt5.QtCore.QThreadPool()
        workerThread = Worker()
        self.threadpool.start(workerThread)

    def newCenter(self):

        self.setNew = True
        for idx in range(CamsToUse):
            self.setCenterValue(idx)

    def setCenterValue(self, mirror):

        if self.btn_FitValue.isChecked():
            Mirror_Calculations[mirror]["GoalPixel_X"] = Mirror_Calculations[
                mirror]["Center_GaussFitX"]
            Mirror_Calculations[mirror]["GoalPixel_Y"] = Mirror_Calculations[
                mirror]["Center_GaussFitY"]
        else:
            Mirror_Calculations[mirror]["GoalPixel_X"] = Mirror_Calculations[
                mirror]["CoM_X"]
            Mirror_Calculations[mirror]["GoalPixel_Y"] = Mirror_Calculations[
                mirror]["CoM_Y"]

    def init_ui(self):

        self.vb = self.ImageBox.addViewBox(row=0, col=0)
        self.Image = pg.ImageItem()
        self.Plot = pg.PlotItem()
        self.xCenter = pg.InfiniteLine(pen=(215, 128, 26))
        self.yCenter = pg.InfiniteLine(pen=(215, 128, 26), angle=0)
        self.xThresholdLinePlus_0 = pg.InfiniteLine()
        self.yThresholdLinePlus_0 = pg.InfiniteLine(angle=0)
        self.xThresholdLineMinus_0 = pg.InfiniteLine()
        self.yThresholdLineMinus_0 = pg.InfiniteLine(angle=0)
        self.vb.addItem(self.Image)
        self.vb.addItem(self.xCenter)
        self.vb.addItem(self.yCenter)
        self.vb.addItem(self.xThresholdLinePlus_0)
        self.vb.addItem(self.yThresholdLinePlus_0)
        self.vb.addItem(self.xThresholdLineMinus_0)
        self.vb.addItem(self.yThresholdLineMinus_0)
        self.PlotY = self.ImageBox.addPlot(row=0, col=1)
        self.PlotX = self.ImageBox.addPlot(row=1, col=0)
        self.ImageBox.ci.layout.setColumnMaximumWidth(1, 100)
        self.ImageBox.ci.layout.setRowMaximumHeight(1, 100)
        self.vb2 = self.ImageBox2.addViewBox(row=0, col=0)
        self.Image2 = pg.ImageItem()
        self.Plot2 = pg.PlotItem()
        self.xCenter2 = pg.InfiniteLine(pen=(215, 128, 26))
        self.yCenter2 = pg.InfiniteLine(pen=(215, 128, 26), angle=0)
        self.xThresholdLinePlus_1 = pg.InfiniteLine()
        self.yThresholdLinePlus_1 = pg.InfiniteLine(angle=0)
        self.xThresholdLineMinus_1 = pg.InfiniteLine()
        self.yThresholdLineMinus_1 = pg.InfiniteLine(angle=0)
        self.vb2.addItem(self.Image2)
        self.vb2.addItem(self.yCenter2)
        self.vb2.addItem(self.xCenter2)
        self.vb2.addItem(self.xThresholdLinePlus_1)
        self.vb2.addItem(self.yThresholdLinePlus_1)
        self.vb2.addItem(self.xThresholdLineMinus_1)
        self.vb2.addItem(self.yThresholdLineMinus_1)
        self.PlotY2 = self.ImageBox2.addPlot(row=0, col=1)
        self.PlotX2 = self.ImageBox2.addPlot(row=1, col=0)
        self.ImageBox2.ci.layout.setColumnMaximumWidth(1, 100)
        self.ImageBox2.ci.layout.setRowMaximumHeight(1, 100)

    def Main(self):
        self.Image.clear()

        self.mirror = MirrorCom()
        #self.resetMirrroSettings()
        for i in range(CamsToUse):
            self.mirror.setSettings((i+1), 50)
        self.cam = Basler(CamsToUse)
        self.cam.openCommunications()
        self.cam.setCameraParameters(exposureTime)
        self.cam.startAquisition()

        self.Plot_PP0()
        self.Plot_PP1()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update(self):

        if self.btn_Logging.isChecked() and self.blog ==0:
            self.blog = 1
            self.log = Logging()

        if not self.btn_Logging.isChecked() and self.blog ==1:
            self.blog = 0
            self.log.closeFile()
            self.log = None

        for i in range(CamsToUse):
            img, nbCam = self.cam.getImage()
            self.updateMirrorDictionary(nbCam[i], img[i])
            if nbCam[i] == 0:
                self.update_PP0(img[i])
                print(np.max(img[i]))
            elif nbCam[i] ==1:
                self.update_PP1(img[i])
                print(np.max(img[i]))
        if self.log:
            self.log.saveValues()
        QtGui.QApplication.processEvents()

        self.checkStatus()

        self.updateThresholds()
        self.checkBoundaries()
        self.moveMirrors()

    def checkStatus(self):
        if self.status == "Adjust":
            self.label.setStyleSheet('background: yellow; color: black')
            self.label.setText("Adjusting")
        elif self.status == "Observing":
            self.label.setStyleSheet('background: green; color: black')
            self.label.setText("Observing")
        elif self.status == "Error":
            self.label.setStyleSheet('background: red; color: black')
            self.label.setText("Error")
        elif self.status == "StandBy":
            self.label.setStyleSheet('background: grey; color: white')
            self.label.setText("StandBy")


    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:

            self.timer.stop()
            if self.log:
                self.log.closeFile()

            event.accept()

        else:
            event.ignore()

    def updateMirrorDictionary(self, mirror, img):
        Mirror_Calculations[mirror] = {}
        Mirror_Calculations[mirror]["Image"] = img

        Mirror_Calculations[mirror]["SumY"] = np.sum(img, axis = 1)
        Mirror_Calculations[mirror]["SumX"] = np.sum(img, axis = 0)

        ygauss = self.fitGauss(Mirror_Calculations[mirror]["SumY"], [10000,
                                                                     0.001,
                                                                     200])
        xgauss = self.fitGauss(Mirror_Calculations[mirror]["SumX"],[10000,
                                                                     0.001,
                                                                     200])

        Mirror_Calculations[mirror]["GausYA"] = ygauss[0]
        Mirror_Calculations[mirror]["GausYB"] = ygauss[1]
        Mirror_Calculations[mirror]["GausYC"] = ygauss[2]

        Mirror_Calculations[mirror]["GausXA"] = xgauss[0]
        Mirror_Calculations[mirror]["GausXB"] = xgauss[1]
        Mirror_Calculations[mirror]["GausXC"] = xgauss[2]

        Mirror_Calculations[mirror]["CenterGauss_X"] = np.argmax(
            Mirror_Calculations[mirror]["SumX"])
        Mirror_Calculations[mirror]["CenterGauss_Y"] = np.argmax(
            Mirror_Calculations[mirror]["SumY"])

        Mirror_Calculations[mirror]["GaussX"] = self.gaus(
            np.linspace(0,
                        len(Mirror_Calculations[mirror]["SumX"]),
                        len(Mirror_Calculations[mirror]["SumX"])),
                        xgauss[0], xgauss[1], xgauss[2])

        Mirror_Calculations[mirror]["GaussY"] = self.gaus(
            np.linspace(0,
                        len(Mirror_Calculations[mirror]["SumY"]),
                        len(Mirror_Calculations[mirror]["SumY"])),
                        ygauss[0], ygauss[1], ygauss[2])

        Mirror_Calculations[mirror]["FWHM_Y"] = abs(ygauss[2] * 2.354)
        Mirror_Calculations[mirror]["FWHM_X"] = abs(xgauss[2] * 2.354)

        Mirror_Calculations[mirror]["Center_GaussFitY"] = ygauss[1]
        Mirror_Calculations[mirror]["Center_GaussFitX"] = xgauss[1]

        Mirror_Calculations[mirror]["Center_X"] = len(Mirror_Calculations[
            mirror]["SumX"])/2
        Mirror_Calculations[mirror]["Center_Y"] = len(Mirror_Calculations[
                                                          mirror]["SumY"]) / 2

        Mirror_Calculations[mirror]["CoM_X"] = np.average(Mirror_Calculations[
            mirror]["SumX"], weights=Mirror_Calculations[
            mirror]["SumX"])
        Mirror_Calculations[mirror]["CoM_Y"] = np.average(Mirror_Calculations[
            mirror]["SumY"], weights=Mirror_Calculations[
            mirror]["SumY"])

        Mirror_Calculations[mirror]["Index_CoM_X"] = np.searchsorted(
            Mirror_Calculations[mirror]["SumX"],
            Mirror_Calculations[mirror]["CoM_X"],)
        Mirror_Calculations[mirror]["Index_CoM_Y"] = np.searchsorted(
            Mirror_Calculations[mirror]["SumY"],
            Mirror_Calculations[mirror]["CoM_Y"])

        if not self.config and not self.setNew:
            Mirror_Calculations[mirror]["GoalPixel_X"] = \
                len(Mirror_Calculations[0]["SumY"])/2
            Mirror_Calculations[mirror]["GoalPixel_Y"] =\
                len(Mirror_Calculations[0]["SumX"])/2
        elif self.setNew:
            self.newCenter()

        if self.btn_IntensityValue.isChecked():
            Mirror_Calculations[mirror]["Threshold_X"] = 0.05 * \
                                                         Mirror_Calculations[mirror]["FWHM_Y"]
            Mirror_Calculations[mirror]["Threshold_Y"] = 0.05 * \
                                                         Mirror_Calculations[mirror]["FWHM_X"]
        else:
            Mirror_Calculations[mirror]["Threshold_X"] = 0.05 * \
                                                         Mirror_Calculations[
                                                             mirror]["Center_GaussFitX"]
            Mirror_Calculations[mirror]["Threshold_Y"] = 0.05 * \
                                                         Mirror_Calculations[
                                                             mirror][
                                                             "Center_GaussFitY"]

        Mirror_Calculations[mirror]["ThresholdPlus_Y"] = Mirror_Calculations[
            mirror]["GoalPixel_X"]+Mirror_Calculations[mirror]["Threshold_X"]
        Mirror_Calculations[mirror]["ThresholdMinus_Y"] = Mirror_Calculations[
            mirror]["GoalPixel_X"]-Mirror_Calculations[mirror]["Threshold_X"]
        Mirror_Calculations[mirror]["ThresholdPlus_X"] = Mirror_Calculations[
            mirror]["GoalPixel_Y"]+Mirror_Calculations[mirror]["Threshold_Y"]
        Mirror_Calculations[mirror]["ThresholdMinus_X"] = Mirror_Calculations[
            mirror]["GoalPixel_Y"]-Mirror_Calculations[mirror]["Threshold_Y"]
    def gaus(self, x, a, x0, sigma):
        return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

    def fitGauss(self, data, init):
        popt, pcov = curve_fit(self.gaus, np.linspace(0, len(data),
                                                      len(data)), data, p0=init)
        return popt

    def Plot_PP0(self):

        colormap = cm.get_cmap(imgColormap)  # cm.get_cmap("CMRmap")
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
        #lut = color
        # Apply the colormap
        self.Image.setLookupTable(lut)
        self.curve = self.PlotY.plot(pen=(215, 128, 26))
        self.curve2 = self.PlotX.plot(pen=(215, 128, 26))
        self.curve6 = self.PlotX.plot(pen=(255, 0, 0))
        self.curve7 = self.PlotY.plot(pen=(255, 0, 0))

        self.XCenter0 = self.PlotX.addLine(x=0, movable=True)
        self.YCenter0 = self.PlotY.addLine(y=0, movable=True)

        self.XThresholdPlus0 = self.PlotX.addLine(x=0, movable=True)
        self.XThresholdMinus0 = self.PlotX.addLine(x=0, movable=True)
        self.YThresholdPlus0 = self.PlotY.addLine(y=0, movable=True)
        self.YThresholdMinus0 = self.PlotY.addLine(y=0, movable=True)

    def update_PP0(self, img):

        mirror = 0
        self.Image.setImage(img)
        self.curve.setData(x=Mirror_Calculations[mirror]["SumX"],
                           y=np.arange(len(Mirror_Calculations[mirror]["SumX"])))
        self.curve2.setData(Mirror_Calculations[mirror]["SumY"])
        self.curve7.setData(x=Mirror_Calculations[mirror]["GaussX"],
                            y=np.arange(len(Mirror_Calculations[mirror][
                                                "GaussX"])))
        self.curve6.setData(Mirror_Calculations[mirror]["GaussY"])

        self.XCenter0.setValue(Mirror_Calculations[mirror]["GoalPixel_X"])
        self.YCenter0.setValue(Mirror_Calculations[mirror]["GoalPixel_Y"])

        self.XThresholdPlus0.setValue(Mirror_Calculations[mirror][
                                          "ThresholdPlus_X"])
        self.XThresholdMinus0.setValue(Mirror_Calculations[mirror][
                                           "ThresholdMinus_X"])
        self.YThresholdPlus0.setValue(Mirror_Calculations[mirror][
                                          "ThresholdPlus_Y"])
        self.YThresholdMinus0.setValue(Mirror_Calculations[mirror][
                                           "ThresholdMinus_Y"])

    def Plot_PP1(self):
        colormap = cm.get_cmap(imgColormap)  # cm.get_cmap("CMRmap")
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
            # lut = color
            # Apply the colormap
        self.Image2.setLookupTable(lut)
        self.curve3 = self.PlotY2.plot(pen=(215, 128, 26))
        self.curve4 = self.PlotX2.plot(pen=(215, 128, 26))
        self.curve8 = self.PlotY2.plot(pen=(255, 0, 0))
        self.curve9 = self.PlotX2.plot(pen=(255, 0, 0))

        self.XCenter1 = self.PlotX2.addLine(x=0, movable=True)
        self.YCenter1 = self.PlotY2.addLine(y=0, movable=True)

        self.XThresholdPlus1 = self.PlotX2.addLine(x=0, movable=True)
        self.XThresholdMinus1 = self.PlotX2.addLine(x=0, movable=True)
        self.YThresholdPlus1 = self.PlotY2.addLine(y=0, movable=True)
        self.YThresholdMinus1 = self.PlotY2.addLine(y=0, movable=True)


    def update_PP1(self, img):
        mirror = 1
        self.Image2.setImage(img)
        self.curve3.setData(x=Mirror_Calculations[mirror]["SumX"],
                            y=np.arange(
                                len(Mirror_Calculations[mirror]["SumX"])))
        self.curve4.setData(Mirror_Calculations[mirror]["SumY"])
        self.curve8.setData(x=Mirror_Calculations[mirror]["GaussX"],
                            y=np.arange(len(Mirror_Calculations[mirror][
                                                "GaussX"])))
        self.curve9.setData(Mirror_Calculations[mirror]["GaussY"])


        self.XCenter1.setValue(Mirror_Calculations[mirror]["GoalPixel_X"])
        self.YCenter1.setValue(Mirror_Calculations[mirror]["GoalPixel_Y"])

        self.XThresholdPlus1.setValue(Mirror_Calculations[mirror][
            "ThresholdPlus_X"])
        self.XThresholdMinus1.setValue(Mirror_Calculations[mirror][
            "ThresholdMinus_X"])
        self.YThresholdPlus1.setValue(Mirror_Calculations[mirror][
            "ThresholdPlus_Y"])
        self.YThresholdMinus1.setValue(Mirror_Calculations[mirror][
            "ThresholdMinus_Y"])

    def checkBoundaries(self):
        MirrorStatus[0] = {}
        MirrorStatus[1] = {}

        for i in range(2):
            yOffset = self.centerOffset(i, "CenterGauss_Y","SumY")
            xOffset = self.centerOffset(i, "CenterGauss_X","SumX")


            if abs(Mirror_Calculations[i]["Threshold_Y"]) - abs(yOffset)\
                    < 0:
                MirrorStatus[i]["bMoveY"] = True
            else:
                MirrorStatus[i]["bMoveY"] = False

            if abs(Mirror_Calculations[i]["Threshold_X"]) - abs(xOffset) < 0:
                MirrorStatus[i]["bMoveX"] = True
            else:
                MirrorStatus[i]["bMoveX"] = False


    def centerOffset(self, i, coordinate, variable):
        return Mirror_Calculations[i][coordinate]-len(
            Mirror_Calculations[0][variable])/2

    def moveMirrors(self):

        if MirrorStatus[0]["bMoveX"]:
            for i in range(1):
                self.checkBoundaries()
                if self.centerOffset(0, "CenterGauss_X", "SumX") < 0:
                    self.mirror.moveChannel(1, 1, -1)
                else:
                    self.mirror.moveChannel(1, 1, 1)

        if MirrorStatus[0]["bMoveY"]:
            for i in range(1):
                self.checkBoundaries()
                if self.centerOffset(0, "CenterGauss_Y", "SumY") < 0:
                    self.mirror.moveChannel(1, 2, 1)
                else:
                    self.mirror.moveChannel(1, 2, -1)
        """
        #if not MirrorStatus[0]["bMoveX"]:
        for i in range(10):
            self.checkBoundaries()
            if MirrorStatus[1]["bMoveX"]:
                if self.centerOffset(1, "CenterGauss_X", "SumX") < 0:
                    self.mirror.moveChannel(2, 1, 1)
                else:
                    self.mirror.moveChannel(2, 1, -1)

        #if not MirrorStatus[0]["bMoveY"]:
        for i in range(10):
            self.checkBoundaries()
            if MirrorStatus[1]["bMoveY"]:
                if self.centerOffset(1, "CenterGauss_Y", "SumY") < 0:
                    self.mirror.moveChannel(2, 2, 1)
                else:
                    self.mirror.moveChannel(2, 2, -1)

        """
        print('test')

    def resetMirrroSettings(self):
        self.mirror.resetMirror()

    def updateThresholds(self):

        CenterToX_0 = Mirror_Calculations[0]["GoalPixel_X"]
        CenterToY_0 = Mirror_Calculations[0]["GoalPixel_Y"]
        CenterToX_1 = Mirror_Calculations[1]["GoalPixel_X"]
        CenterToY_1 = Mirror_Calculations[1]["GoalPixel_Y"]
        self.xCenter.setPos(CenterToX_0)
        self.xCenter2.setPos(CenterToX_1)
        self.yCenter.setPos(CenterToY_0)
        self.yCenter2.setPos(CenterToY_1)

        self.yThresholdLinePlus_0.setPos(Mirror_Calculations[0][
                                             "ThresholdPlus_Y"])
        self.xThresholdLinePlus_0.setPos(Mirror_Calculations[0][
                                             "ThresholdPlus_X"])
        self.yThresholdLineMinus_0.setPos(Mirror_Calculations[0][
            "ThresholdMinus_X"])
        self.xThresholdLineMinus_0.setPos(Mirror_Calculations[0][
            "ThresholdMinus_Y"])

        self.yThresholdLinePlus_1.setPos(Mirror_Calculations[1][
                                             "ThresholdPlus_Y"])
        self.xThresholdLinePlus_1.setPos(Mirror_Calculations[1][
                                             "ThresholdPlus_X"])
        self.yThresholdLineMinus_1.setPos(Mirror_Calculations[1][
            "ThresholdMinus_X"])
        self.xThresholdLineMinus_1.setPos(Mirror_Calculations[1][
            "ThresholdMinus_Y"])


def main():

    app = QApplication(sys.argv)
    MyWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
