# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TrendViewer.ui'
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

class Ui_TrendViewer(object):
    def setupUi(self, TrendViewer):
        TrendViewer.setObjectName(_fromUtf8("TrendViewer"))
        TrendViewer.resize(355, 180)
        TrendViewer.setMinimumSize(QtCore.QSize(355, 180))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        TrendViewer.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TrendViewer.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(TrendViewer)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.webView_weewx = QtWebKit.QWebView(TrendViewer)
        self.webView_weewx.setUrl(QtCore.QUrl(_fromUtf8("http://localhost/weewx/")))
        self.webView_weewx.setRenderHints(QtGui.QPainter.Antialiasing|QtGui.QPainter.HighQualityAntialiasing|QtGui.QPainter.SmoothPixmapTransform|QtGui.QPainter.TextAntialiasing)
        self.webView_weewx.setObjectName(_fromUtf8("webView_weewx"))
        self.verticalLayout.addWidget(self.webView_weewx)

        self.retranslateUi(TrendViewer)
        QtCore.QMetaObject.connectSlotsByName(TrendViewer)

    def retranslateUi(self, TrendViewer):
        TrendViewer.setWindowTitle(_translate("TrendViewer", "CoSESWeather Trend-Viewer", None))

from PyQt4 import QtWebKit
import icon_rc
