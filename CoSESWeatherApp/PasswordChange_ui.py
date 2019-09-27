# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PasswordChange.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_PassChangerDialog(object):
    def setupUi(self, PassChangerDialog):
        PassChangerDialog.setObjectName(_fromUtf8("PassChangerDialog"))
        PassChangerDialog.resize(350, 231)
        PassChangerDialog.setMinimumSize(QtCore.QSize(350, 231))
        PassChangerDialog.setMaximumSize(QtCore.QSize(350, 231))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        PassChangerDialog.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        PassChangerDialog.setWindowIcon(icon)
        self.groupBox = QtGui.QGroupBox(PassChangerDialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 5, 331, 151))
        font = QtGui.QFont()
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(0, 30, 331, 20))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.lineEdit_newPass1 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_newPass1.setGeometry(QtCore.QRect(70, 53, 191, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setBold(True)
        font.setUnderline(False)
        font.setWeight(75)
        self.lineEdit_newPass1.setFont(font)
        self.lineEdit_newPass1.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_newPass1.setObjectName(_fromUtf8("lineEdit_newPass1"))
        self.lineEdit_newPass2 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_newPass2.setGeometry(QtCore.QRect(70, 109, 191, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setBold(True)
        font.setUnderline(False)
        font.setWeight(75)
        self.lineEdit_newPass2.setFont(font)
        self.lineEdit_newPass2.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_newPass2.setObjectName(_fromUtf8("lineEdit_newPass2"))
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(0, 86, 331, 20))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.groupBox_2 = QtGui.QGroupBox(PassChangerDialog)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 163, 331, 61))
        self.groupBox_2.setTitle(_fromUtf8(""))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.pushButton_changePass = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_changePass.setGeometry(QtCore.QRect(78, 30, 75, 23))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_changePass.setFont(font)
        self.pushButton_changePass.setObjectName(_fromUtf8("pushButton_changePass"))
        self.pushButton_cancelPass = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_cancelPass.setGeometry(QtCore.QRect(178, 30, 75, 23))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_cancelPass.setFont(font)
        self.pushButton_cancelPass.setObjectName(_fromUtf8("pushButton_cancelPass"))
        self.label_3 = QtGui.QLabel(self.groupBox_2)
        self.label_3.setGeometry(QtCore.QRect(0, 5, 331, 20))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName(_fromUtf8("label_3"))

        self.retranslateUi(PassChangerDialog)
        QtCore.QMetaObject.connectSlotsByName(PassChangerDialog)

    def retranslateUi(self, PassChangerDialog):
        PassChangerDialog.setWindowTitle(_translate("PassChangerDialog", "New Password", None))
        self.groupBox.setTitle(_translate("PassChangerDialog", "Change your account password", None))
        self.label.setText(_translate("PassChangerDialog", "Please enter a new password below:", None))
        self.lineEdit_newPass1.setToolTip(_translate("PassChangerDialog", "Please enter your new password", None))
        self.lineEdit_newPass1.setPlaceholderText(_translate("PassChangerDialog", "New Password", None))
        self.lineEdit_newPass2.setToolTip(_translate("PassChangerDialog", "Please re-enter your new password", None))
        self.lineEdit_newPass2.setPlaceholderText(_translate("PassChangerDialog", "Re-enter new Password", None))
        self.label_2.setText(_translate("PassChangerDialog", "Please re-enter your new password below:", None))
        self.pushButton_changePass.setToolTip(_translate("PassChangerDialog", "Click to change password", None))
        self.pushButton_changePass.setText(_translate("PassChangerDialog", "Apply", None))
        self.pushButton_cancelPass.setToolTip(_translate("PassChangerDialog", "Abort", None))
        self.pushButton_cancelPass.setText(_translate("PassChangerDialog", "Cancel", None))
        self.label_3.setText(_translate("PassChangerDialog", "Click on Apply in order to change your password.", None))

import icon_rc
