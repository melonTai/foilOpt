#!python3.6
import multiprocessing
from PyQt5 import QtGui, QtWidgets, QtCore

from Dialogs import DialogSeq, DialogOne

class Slot_MainWindow(object):
    def setup_param(self):
        self.foilfiles = []
        self.itemsValue = []
        self.itemsConstraint = []
        self.itemsPenalty = []
        self.itemsObject = []
        self.thread_num = 1
        self.MaxGen = 200
        self.cx_pb = 0.7
        self.mut_pb = 1.0
        self.cx_eta = 10
        self.mut_eta = 20
        self.pop = 100
        self.re = 150000
        self.error = ''
        self.start = ''
        self.end = ''
        self.step = ''
        self.onepoint = ''
        self.assignText = ''
        self.number = 0

        #スロット

    def foilOpen(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open file','/home')
        self.foilfiles = fname[0]
        foils = ''
        for foil in fname[0]:
            foils += foil + '\n'
        self.textBrowser.setText(foils)

    def getTable3Item(self):
        n_row = self.tableWidget_3.rowCount()
        items_object = [self.tableWidget_3.item(i,0) for i in range(n_row)]
        items_object2 = [self.tableWidget_3.item(i,1) for i in range(n_row)]
        self.itemsConstraint = [item.text() if item != None else item for item in items_object]
        self.itemsPenalty = [item.text() if item != None else item for item in items_object2]

    def getTable2Item(self):
        n_row = self.tableWidget_2.rowCount()
        items_object = [self.tableWidget_2.item(i,0) for i in range(n_row)]
        self.itemsObject = [item.text() if item != None else item for item in items_object]

    def _getLineVal(self, obj):
        """
        受け取ったlineEditオブジェクトの値を取得するメソッド
        #argument
            *obj
                -lineEditオブジェクト
        """
        val = obj.text()
        return val
    

    def errorPopup(self):
        dlg = QtWidgets.QDialog(self)
        dlg.resize(500, 300)
        textBrowser = QtWidgets.QTextBrowser(dlg)
        textBrowser.setGeometry(QtCore.QRect(10, 10, 470, 280))
        textBrowser.setText(self.error)
        dlg.setWindowTitle("ErrorMessage")
        dlg.exec_()

    def seqPopup(self,s):
        self.dlg = DialogSeq(self)
        self.dlg.setWindowTitle(s)
        v = QtGui.QDoubleValidator()
        self.dlg.lineEdit.setValidator(v)
        self.dlg.lineEdit_2.setValidator(v)
        self.dlg.lineEdit_3.setValidator(v)
        self.dlg.lineEdit.editingFinished.connect(self.get_seq)
        self.dlg.lineEdit_2.editingFinished.connect(self.get_seq)
        self.dlg.lineEdit_3.editingFinished.connect(self.get_seq)
        print(s)
        self.dlg.buttonBox.accepted.connect(lambda: self.addToAssign_seq(s = s))
        self.dlg.exec_()

    def onePointPopup(self,s):
        self.dlg = DialogOne(self)
        self.dlg.setWindowTitle(s)
        self.dlg.lineEdit.editingFinished.connect(self.get_one)
        self.dlg.buttonBox.accepted.connect(lambda: self.addToAssign_one(s = s))
        self.dlg.exec_()

    def addToAssign_seq(self,s):
        self.assignText = self.textEdit.toPlainText()
        self.assignText += "a{0}, cl{0}, cd{0}, cm{0}, cp{0} = xf.{1}({2}, {3}, {4});\n".format(self.number,s,self.start,self.end,self.step)
        self.number += 1
        self.textEdit.setText(self.assignText)

    def addToAssign_one(self,s):
        self.assignText = self.textEdit.toPlainText()
        self.assignText += "a{0}, cl{0}, cd{0}, cm{0}, cp{0} = xf.{1}({2});\n".format(self.number,s,self.onepoint)
        self.number += 1
        self.textEdit.setText(self.assignText)

    def get_seq(self):
        line = self.dlg.sender()
        if line is self.dlg.lineEdit:
            self.start = line.text()
        elif line is self.dlg.lineEdit_2:
            self.end = line.text()
        elif line is self.dlg.lineEdit_3:
            self.step = line.text()
        else:
            print("fatal error")

    def get_one(self):
        line = self.dlg.sender()
        if line is self.dlg.lineEdit:
            self.onepoint = line.text()

    def validate_input(self):
        """
        lineEditに入力された値が有効か無効かを判定し、
        判定結果に応じて値を属性に代入するメソッド
        """
        vthread = QtGui.QIntValidator(0, multiprocessing.cpu_count())
        vgen = QtGui.QIntValidator(1, 2000)
        vpop = QtGui.QIntValidator(1, 1000)
        veta = QtGui.QDoubleValidator(0, 100, 3)
        vpb = QtGui.QDoubleValidator(0, 1, 3)
        vre = QtGui.QDoubleValidator()

        line = self.sender()
        val = self._getLineVal(line)
        if line is self.lineEdit:
            if (vthread.validate(val,3)[0] == 2):
                self.thread_num = int(val)
            else:
                line.setText(str(4))

        elif line is self.lineEdit_2:
            if (vgen.validate(val,3)[0] == 2):
                self.MaxGen = int(val)
            else:
                line.setText(str(200))

        elif line is self.lineEdit_3:
            if (vpb.validate(val,3)[0] == 2):
                self.cx_pb = float(val)
            else:
                line.setText(str(1.0))

        elif line is self.lineEdit_4:
            if (vpb.validate(val,3)[0] == 2):
                self.mut_pb = float(val)
            else:
                line.setText(str(0.5))

        elif line is self.lineEdit_5:
            if (veta.validate(val,3)[0] == 2):
                self.cx_eta = float(val)
            else:
                line.setText(str(20.0))

        elif line is self.lineEdit_6:
            if (vthread.validate(val,3)[0] == 2):
                self.mut_eta = float(val)
            else:
                line.setText(str(30.0))
        elif line is self.lineEdit_7:
            if (vpop.validate(val,3)[0] == 2):
                self.pop = int(val)
            else:
                line.setText(str(200))
        elif line is self.lineEdit_8:
            if (vre.validate(val,3)[0] == 2):
                self.re = float(val)
            else:
                line.setText(str(150000))
