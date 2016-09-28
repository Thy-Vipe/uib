from PySide.QtCore import *
from PySide.QtGui import *
from utils import distance
import os

class Ui_bOpt(object):
	def setupUi(self, bOpt):
		bOpt.setObjectName("bOpt")
		bOpt.setMinimumSize(102, 342)
		bOpt.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
		self.verticalLayoutWidget = QWidget(bOpt)
		self.verticalLayoutWidget.setGeometry(QRect(0, 0, 102, 149))
		self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
		self.optionsBtnLayout = QVBoxLayout(self.verticalLayoutWidget)
		self.optionsBtnLayout.setSpacing(2)
		self.optionsBtnLayout.setContentsMargins(0, 0, 0, 0)
		self.optionsBtnLayout.setObjectName("optionsBtnLayout")
		self.loadUiBtn = QPushButton(self.verticalLayoutWidget)
		self.loadUiBtn.setMinimumSize(QSize(100, 28))
		self.loadUiBtn.setMaximumSize(QSize(16777215, 28))
		self.loadUiBtn.setObjectName("loadUiBtn")
		self.optionsBtnLayout.addWidget(self.loadUiBtn)
		self.saveUiBtn = QPushButton(self.verticalLayoutWidget)
		self.saveUiBtn.setMinimumSize(QSize(100, 28))
		self.saveUiBtn.setMaximumSize(QSize(100, 28))
		self.saveUiBtn.setObjectName("saveUiBtn")
		self.optionsBtnLayout.addWidget(self.saveUiBtn)
		self.setBgBtn = QPushButton(self.verticalLayoutWidget)
		self.setBgBtn.setMinimumSize(QSize(100, 28))
		self.setBgBtn.setMaximumSize(QSize(100, 28))
		self.setBgBtn.setObjectName("setBgBtn")
		self.optionsBtnLayout.addWidget(self.setBgBtn)
		self.resetUiBtn = QPushButton(self.verticalLayoutWidget)
		self.resetUiBtn.setMinimumSize(QSize(100, 28))
		self.resetUiBtn.setMaximumSize(QSize(100, 28))
		self.resetUiBtn.setObjectName("resetUiBtn")
		self.optionsBtnLayout.addWidget(self.resetUiBtn)
		self.startupBtnEdit = QPushButton(self.verticalLayoutWidget)
		self.startupBtnEdit.setMinimumSize(QSize(100, 28))
		self.startupBtnEdit.setMaximumSize(QSize(100, 28))
		self.startupBtnEdit.setObjectName("startupCmdEditorBtn")
		self.optionsBtnLayout.addWidget(self.startupBtnEdit)
		self.listWidget = QListWidget(bOpt)
		self.listWidget.setGeometry(QRect(0, 148, 101, 164))
		self.listWidget.setObjectName("listWidget")
		with open("%s\\ui_listwidget.qss"%(os.path.dirname(os.path.realpath(__file__))), "r") as lw_stylesheet:
			self.listWidget.setStyleSheet(lw_stylesheet.read())
			lw_stylesheet.close()

		bOpt.resize(102, 342)
		self.setWindowFlags(Qt.Tool)

		self.retranslateUi(bOpt)
		QMetaObject.connectSlotsByName(bOpt)

	def retranslateUi(self, bOpt):
		bOpt.setWindowTitle(QApplication.translate("bOpt", "Builder Options", None, QApplication.UnicodeUTF8))
		self.loadUiBtn.setText(QApplication.translate("bOpt", "Load Ui", None, QApplication.UnicodeUTF8))
		self.saveUiBtn.setText(QApplication.translate("bOpt", "Save Ui", None, QApplication.UnicodeUTF8))
		self.setBgBtn.setText(QApplication.translate("bOpt", "Set Background", None, QApplication.UnicodeUTF8))
		self.resetUiBtn.setText(QApplication.translate("bOpt", "Reset Ui", None, QApplication.UnicodeUTF8))
		self.startupBtnEdit.setText(QApplication.translate("bOpt", "Startup Script...", None, QApplication.UnicodeUTF8))

class BuilderOptions(Ui_bOpt, QDialog):
	def __init__(self, parent):
		super(BuilderOptions, self).__init__(parent)
		self.setupUi(self)
		self.parent = parent
		self._isSnaped = False
		self.__currentState = 1
		pos = parent.pos()
		pos.setX(pos.x() - self.width() - 15)
		self.initMode = True
		self.move(pos)
		self.show()
		self.initMode = False
		self.setMaximumSize(self.width(), self.parent.height())
		self.setBgBtn.clicked.connect(self.parent.setUiBackground)
		self.saveUiBtn.clicked.connect(self.parent.saveUi)
		self.loadUiBtn.clicked.connect(self.parent.loadUi)
		self.resetUiBtn.clicked.connect(self.parent.resetUi)
		self.startupBtnEdit.clicked.connect(self.parent.initStartupCmdDialog)

	def moveEvent(self, event):
		dist = distance(self.parent.pos(), QPoint(self.pos().x() + self.width(), self.pos().y()))
		if (dist <= 60 and not self._isSnaped) or self.initMode:
			self._isSnaped = True
			self.move(self.parent.pos().x() - self.width() - 15, self.parent.pos().y())
		elif dist > 60:
			self._isSnaped = False

	def closeEvent(self, event):
		if self.__currentState == 1:
			self.setMinimumSize(102,1)
			self.resize(102,1)
			self.__currentState = 0
		elif self.__currentState == 0:
			self.resize(102, 314)
			self.setMinimumSize(102,314)
			self.__currentState = 1
		event.ignore()

	def resizeEvent(self, event):
		self.listWidget.resize(101, 164+(self.height()-342))

	def isSnaped(self): return self._isSnaped
	def setSnaped(self, b): 
		if isinstance(b, bool): 
			self._isSnaped = b
			self.move(self.parent.pos().x() - self.width() - 15, self.parent.pos().y())
		else: raise TypeError("Invalid value for snap attribute. Must be boolean.")
