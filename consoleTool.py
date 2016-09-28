

from PySide import QtCore, QtGui

class ConsoleLayout(QtGui.QTextEdit):
	numEnterPressed = QtCore.Signal()
	rollBack = QtCore.Signal(int)
	def __init__(self, p):
		super(ConsoleLayout, self).__init__(p)
		font = QtGui.QFont()
		font.setPointSize(10)
		font.setFamily("MS Shell Dlg 2")
		self.setFont(font)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Enter:
			self.numEnterPressed.emit()
			self.clear()
		elif event.key() == QtCore.Qt.Key_Up:
			self.rollBack.emit(-1)
		elif event.key() == QtCore.Qt.Key_Down:
			self.rollBack.emit(1)
		else:
			super(ConsoleLayout, self).keyPressEvent(event)

class Ui_consoleDialog(object):
	def setupUi(self, consoleDialog):
		consoleDialog.setObjectName("consoleDialog")
		consoleDialog.resize(401, 202)
		self.consoleLayout = ConsoleLayout(consoleDialog)
		self.consoleLayout.setGeometry(QtCore.QRect(0, 0, 401, 201))
		self.consoleLayout.setObjectName("consoleLayout")
		self.consoleLayout.setTabStopWidth(14)

		self.retranslateUi(consoleDialog)
		QtCore.QMetaObject.connectSlotsByName(consoleDialog)

	def retranslateUi(self, consoleDialog):
		consoleDialog.setWindowTitle(QtGui.QApplication.translate("consoleDialog", "Console ", None, QtGui.QApplication.UnicodeUTF8))

class ConsoleDialog(Ui_consoleDialog, QtGui.QDialog):
	def __init__(self, parent=None, libs={}):
		super(ConsoleDialog, self).__init__(parent)
		self.setupUi(self)
		self.consoleLayout.numEnterPressed.connect(self.execCommand)
		self.consoleLayout.rollBack.connect(self.getLastCommand)
		self.libraries = libs
		self.lastCommand = []
		self.currentCommandIndex = -1
		self.show()

	def execCommand(self):
		cmd = self.consoleLayout.toPlainText()
		self.lastCommand.append(str(cmd))
		self.currentCommandIndex = len(self.lastCommand)
		exec cmd in self.libraries

	def getLastCommand(self, direction):
		try:
			self.consoleLayout.setText(self.lastCommand[self.currentCommandIndex+direction])
			self.currentCommandIndex += direction
		except IndexError:
			print "Nothing left to undo."

	def resizeEvent(self, event):
		self.consoleLayout.setGeometry(QtCore.QRect(0,0, self.width(), self.height()))