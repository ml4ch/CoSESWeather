# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CoSESWeatherApp_LOGIN_ui.ui'
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

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName(_fromUtf8("LoginDialog"))
        LoginDialog.resize(558, 411)
        LoginDialog.setMinimumSize(QtCore.QSize(558, 411))
        LoginDialog.setMaximumSize(QtCore.QSize(558, 411))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        LoginDialog.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginDialog.setWindowIcon(icon)
        self.groupBox_login = QtGui.QGroupBox(LoginDialog)
        self.groupBox_login.setGeometry(QtCore.QRect(0, 90, 554, 318))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.groupBox_login.setFont(font)
        self.groupBox_login.setObjectName(_fromUtf8("groupBox_login"))
        self.groupBox_login_3 = QtGui.QGroupBox(self.groupBox_login)
        self.groupBox_login_3.setGeometry(QtCore.QRect(10, 264, 531, 41))
        font = QtGui.QFont()
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.groupBox_login_3.setFont(font)
        self.groupBox_login_3.setTitle(_fromUtf8(""))
        self.groupBox_login_3.setObjectName(_fromUtf8("groupBox_login_3"))
        self.pushButton_login_MAIN = QtGui.QPushButton(self.groupBox_login_3)
        self.pushButton_login_MAIN.setGeometry(QtCore.QRect(191, 10, 75, 23))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.pushButton_login_MAIN.setFont(font)
        self.pushButton_login_MAIN.setObjectName(_fromUtf8("pushButton_login_MAIN"))
        self.pushButton_login_close = QtGui.QPushButton(self.groupBox_login_3)
        self.pushButton_login_close.setGeometry(QtCore.QRect(275, 10, 75, 23))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.pushButton_login_close.setFont(font)
        self.pushButton_login_close.setObjectName(_fromUtf8("pushButton_login_close"))
        self.label_welcome = QtGui.QLabel(self.groupBox_login)
        self.label_welcome.setGeometry(QtCore.QRect(0, 90, 558, 20))
        font = QtGui.QFont()
        font.setBold(True)
        font.setUnderline(False)
        font.setWeight(75)
        self.label_welcome.setFont(font)
        self.label_welcome.setAlignment(QtCore.Qt.AlignCenter)
        self.label_welcome.setObjectName(_fromUtf8("label_welcome"))
        self.label_welcome_2 = QtGui.QLabel(self.groupBox_login)
        self.label_welcome_2.setGeometry(QtCore.QRect(0, 106, 558, 20))
        font = QtGui.QFont()
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        self.label_welcome_2.setFont(font)
        self.label_welcome_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_welcome_2.setObjectName(_fromUtf8("label_welcome_2"))
        self.label_welcome_3 = QtGui.QLabel(self.groupBox_login)
        self.label_welcome_3.setGeometry(QtCore.QRect(0, 120, 558, 20))
        font = QtGui.QFont()
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        self.label_welcome_3.setFont(font)
        self.label_welcome_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_welcome_3.setObjectName(_fromUtf8("label_welcome_3"))
        self.label_2 = QtGui.QLabel(self.groupBox_login)
        self.label_2.setGeometry(QtCore.QRect(0, 16, 558, 71))
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.groupBox_11 = QtGui.QGroupBox(self.groupBox_login)
        self.groupBox_11.setGeometry(QtCore.QRect(10, 150, 531, 108))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.groupBox_11.setFont(font)
        self.groupBox_11.setObjectName(_fromUtf8("groupBox_11"))
        self.lineEdit_user = QtGui.QLineEdit(self.groupBox_11)
        self.lineEdit_user.setGeometry(QtCore.QRect(150, 32, 231, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        self.lineEdit_user.setFont(font)
        self.lineEdit_user.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_user.setObjectName(_fromUtf8("lineEdit_user"))
        self.lineEdit_pass = QtGui.QLineEdit(self.groupBox_11)
        self.lineEdit_pass.setGeometry(QtCore.QRect(150, 62, 231, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        self.lineEdit_pass.setFont(font)
        self.lineEdit_pass.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_pass.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_pass.setObjectName(_fromUtf8("lineEdit_pass"))
        self.label_27 = QtGui.QLabel(self.groupBox_11)
        self.label_27.setGeometry(QtCore.QRect(-40, 33, 171, 20))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.label_27.setFont(font)
        self.label_27.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_27.setObjectName(_fromUtf8("label_27"))
        self.label_29 = QtGui.QLabel(self.groupBox_11)
        self.label_29.setGeometry(QtCore.QRect(-40, 64, 171, 20))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.label_29.setFont(font)
        self.label_29.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_29.setObjectName(_fromUtf8("label_29"))
        self.label_3 = QtGui.QLabel(self.groupBox_11)
        self.label_3.setGeometry(QtCore.QRect(435, 32, 91, 51))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.pushButton_addTUM = QtGui.QPushButton(self.groupBox_11)
        self.pushButton_addTUM.setGeometry(QtCore.QRect(381, 30, 51, 23))
        font = QtGui.QFont()
        font.setUnderline(False)
        self.pushButton_addTUM.setFont(font)
        self.pushButton_addTUM.setObjectName(_fromUtf8("pushButton_addTUM"))
        self.label_wait = QtGui.QLabel(self.groupBox_login)
        self.label_wait.setGeometry(QtCore.QRect(0, 234, 558, 20))
        font = QtGui.QFont()
        font.setBold(True)
        font.setUnderline(False)
        font.setWeight(75)
        self.label_wait.setFont(font)
        self.label_wait.setStyleSheet(_fromUtf8("color: rgb(0, 101, 189);"))
        self.label_wait.setAlignment(QtCore.Qt.AlignCenter)
        self.label_wait.setObjectName(_fromUtf8("label_wait"))
        self.label_header = QtGui.QLabel(LoginDialog)
        self.label_header.setGeometry(QtCore.QRect(0, 0, 561, 88))
        self.label_header.setObjectName(_fromUtf8("label_header"))
        self.label_header.raise_()
        self.groupBox_login.raise_()

        self.retranslateUi(LoginDialog)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)
        LoginDialog.setTabOrder(self.lineEdit_user, self.lineEdit_pass)
        LoginDialog.setTabOrder(self.lineEdit_pass, self.pushButton_login_MAIN)
        LoginDialog.setTabOrder(self.pushButton_login_MAIN, self.pushButton_login_close)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(_translate("LoginDialog", "CoSESWeather: Login", None))
        self.groupBox_login.setTitle(_translate("LoginDialog", "Login", None))
        self.pushButton_login_MAIN.setToolTip(_translate("LoginDialog", "Click to login", None))
        self.pushButton_login_MAIN.setText(_translate("LoginDialog", "Login", None))
        self.pushButton_login_close.setToolTip(_translate("LoginDialog", "Close the app", None))
        self.pushButton_login_close.setText(_translate("LoginDialog", "Close", None))
        self.label_welcome.setText(_translate("LoginDialog", "Welcome to CoSESWeather", None))
        self.label_welcome_2.setText(_translate("LoginDialog", "Please enter your login data below in order to connect to the server.", None))
        self.label_welcome_3.setText(_translate("LoginDialog", "Please note that you must have an active account on the server in order to login.", None))
        self.label_2.setText(_translate("LoginDialog", "<html><head/><body><p><img src=\":/logo/logo.png\"/></p></body></html>", None))
        self.groupBox_11.setTitle(_translate("LoginDialog", "Please enter your user data", None))
        self.lineEdit_user.setToolTip(_translate("LoginDialog", "Please enter your email address", None))
        self.lineEdit_user.setPlaceholderText(_translate("LoginDialog", "Email-Address", None))
        self.lineEdit_pass.setToolTip(_translate("LoginDialog", "Please enter your password", None))
        self.lineEdit_pass.setPlaceholderText(_translate("LoginDialog", "Password", None))
        self.label_27.setText(_translate("LoginDialog", "User [eMail]:", None))
        self.label_29.setText(_translate("LoginDialog", "Password:", None))
        self.label_3.setText(_translate("LoginDialog", "<html><head/><body><p><img src=\":/key/key.png\"/></p></body></html>", None))
        self.pushButton_addTUM.setToolTip(_translate("LoginDialog", "Click to add TUM-email format", None))
        self.pushButton_addTUM.setText(_translate("LoginDialog", "TUM", None))
        self.label_wait.setText(_translate("LoginDialog", "Please wait, logging in ...", None))
        self.label_header.setText(_translate("LoginDialog", "<html><head/><body><p><img src=\":/header/header.png\"/></p></body></html>", None))

import header_rc
import icon_rc
import key_rc
import logo_rc
import tum_logo_rc
