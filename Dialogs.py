from PyQt5 import QtWidgets, uic

from Ui_module.Ui_DialogSeq import Ui_DialogSeq
from Ui_module.Ui_DialogOnepoint import Ui_DialogOne

class DialogSeq(QtWidgets.QDialog, Ui_DialogSeq):
    def __init__(self, *args, obj=None, **kwargs):
        super(DialogSeq, self).__init__(*args, **kwargs)

        #qtcreatorによるデザインを読み込む
        self.setupUi(self)

class DialogOne(QtWidgets.QDialog, Ui_DialogOne):
    def __init__(self, *args, obj=None, **kwargs):
        super(DialogOne, self).__init__(*args, **kwargs)

        #qtcreatorによるデザインを読み込む
        self.setupUi(self)
