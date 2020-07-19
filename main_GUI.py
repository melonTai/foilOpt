import sys
from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSizePolicy

import multiprocessing

import random
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np

import traceback
import re

#自作モジュール
from nsga3 import nsga3
import foilConductor as fc

#翼型解析ライブラリ
from xfoil import XFoil
from xfoil.model import Airfoil

#Uiデザインを読み込み
from Ui_module.Ui_MainWindow_v9 import Ui_MainWindow
#Uiスロットを読み込み
from Ui_module.Slot_MainWindow_v2 import Slot_MainWindow

class nsga3ForApp(nsga3):
    def __init__(self):
        super(nsga3ForApp, self).__init__()
        self.gs = []
        self.penalties = []
        self.Os = []
        self.assigns = []

    def evaluate(self,individual):
        ratios = self.decoder(individual, self.code_division)
        datlist_list = [fc.read_datfile(file) for file in self.datfiles]
        datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
        newdat = fc.interpolate_dat(datlist_shaped_list,ratios)

        foil_para = fc.get_foil_para(newdat)

        datx = np.array([ax[0] for ax in newdat])
        daty = np.array([ax[1] for ax in newdat])
        newfoil = Airfoil(x = datx, y = daty)

        mt, mta, mc, mca, s = foil_para

        penalty = 0
        for g, p in zip(self.gs, self.penalties):
            if(not g):
                penalty += p

        xf = XFoil()
        xf.airfoil = newfoil
        xf.Re = self.re
        xf.max_iter = 60

        print(self.assigns,self.datfiles)
        scope = locals()
        exec(self.assigns,scope)
        #----------------------------------
        #目的値
        #----------------------------------
        try:
            obj1,obj2,obj3 = [eval(o) for o in self.Os]
        except IndexError as e:
            obj1,obj2,obj3=[1.0]*self.NOBJ
            traceback.print_exc()
        except SyntaxError as e:
            raise ValueError("invalid objection")



        if (np.isnan(obj1) or obj1 > 1):
            obj1 = 1
        if (np.isnan(obj2) or obj2 > 1):
            obj2 = 1
        if (np.isnan(obj3) or obj3 > 1):
            obj3 = 1

        obj1 += penalty
        obj2 += penalty
        obj3 += penalty

        return [obj1, obj2, obj3]
    #いじるのここまで)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow, Slot_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #qtcreatorによるデザインを読み込む
        self.setupUi(self)
        #シグナルをスロットにつなげる
        self.connectSlots(MainWindow)

        self.setup_param()
        self.lineEdit.setText(str(4))
        self.lineEdit_2.setText(str(200))
        self.lineEdit_3.setText(str(1.0))
        self.lineEdit_4.setText(str(0.5))
        self.lineEdit_5.setText(str(20.0))
        self.lineEdit_6.setText(str(30.0))
        self.lineEdit_7.setText(str(200))
        self.lineEdit_8.setText(str(150000))

        #=========================================
        #uiに変更を加える
        #=========================================
    def setup_plot(self):
        #プロット先をgroupBox_4に設定
        self.canvas = MplCanvas(self, width=3, height=2, dpi=100)
        toolbar = NavigationToolbar(self.canvas, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(toolbar)
        self.groupBox_4.setLayout(layout)

        self.canvas2 = MplCanvas(self, width=3, height=2, dpi=100)
        toolbar2 = NavigationToolbar(self.canvas2, self)
        layout2 = QtWidgets.QVBoxLayout()
        layout2.addWidget(self.canvas2)
        layout2.addWidget(toolbar2)
        self.groupBox_3.setLayout(layout2)
        ratios = [0.4,0.1,0.1,0.3]
        datlist_list = [fc.read_datfile(file) for file in self.foilfiles]
        datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
        newdat = fc.interpolate_dat(datlist_shaped_list,ratios)
        self.datx = [dat[0] for dat in newdat]
        self.daty = [dat[1] for dat in newdat]
        print(self.datx)
        print(self.daty)
        self.canvas2.axes.set_xlim(0,1)
        self.canvas2.axes.set_ylim(-0.5,0.5)
        self.canvas2.axes.set_title('gen1')
        self.canvas2.axes.plot(self.datx, self.daty, 'r')
        self.canvas2.draw()

        #プロットデータ設定
        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 10) for i in range(n_data)]
        self.update_plot()

        #プロット更新頻度設定
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


        #プロットアップデート関数
    def update_plot(self):
        self.ydata = self.ydata[1:] + [random.randint(0, 10)]
        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.plot(self.xdata, self.ydata, 'r')
        self.canvas.draw()

        #シグナルをスロットにつなげる
    def connectSlots(self,MainWindow):
        self.pushButton.clicked.connect(self.foilOpen)
        self.listWidget.itemDoubleClicked.connect(lambda x: self.seqPopup(x.text()) if re.match(r'.seq',x.text()) else self.onePointPopup(x.text()))
        self.tableWidget_2.cellChanged.connect(self.getTable2Item)
        self.tableWidget_3.cellChanged.connect(self.getTable3Item)
        self.lineEdit.editingFinished.connect(self.validate_input)
        self.lineEdit_2.editingFinished.connect(self.validate_input)
        self.lineEdit_3.editingFinished.connect(self.validate_input)
        self.lineEdit_4.editingFinished.connect(self.validate_input)
        self.lineEdit_5.editingFinished.connect(self.validate_input)
        self.lineEdit_6.editingFinished.connect(self.validate_input)
        self.lineEdit_7.editingFinished.connect(self.validate_input)
        self.lineEdit_8.editingFinished.connect(self.validate_input)
        self.pushButton_3.clicked.connect(self.main)



    def main(self):
        self.setup_plot()
        ng = nsga3ForApp()
        try:
            print(self.itemsObject)
            if len(self.foilfiles) == 0:
                raise ValueError("empty aerofoil")
            elif not all([i != None or i == '' for i in self.itemsObject]) or len(self.itemsObject) == 0:
                raise ValueError("empty objection")

            ng.datfiles = self.foilfiles
            ng.NDIM = len(ng.datfiles)*ng.code_division
            ng.MU = self.pop
            ng.NGEN = self.MaxGen
            ng.CXPB = self.cx_pb
            ng.MUTPB = self.mut_pb
            ng.cx_eta = self.cx_eta
            ng.mut_eta = self.mut_eta
            ng.thread = self.thread_num
            ng.re = self.re
            ng.gs = [True if g == None or g == '' else eval(g) for g in self.itemsConstraint]
            ng.penalties = self.itemsPenalty
            ng.Os = self.itemsObject
            self.assignText = str(self.textEdit.toPlainText())
            ng.assigns = self.assignText
            ng.main()
        except ValueError as e:
            self.error = str(e)
            self.errorPopup()
        except Exception as e:
            self.error = str(e)
            self.errorPopup()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
