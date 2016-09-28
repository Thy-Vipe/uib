from PySide import QtCore, QtGui
import sys
import popupMenu as pp


class testUI(QtGui.QMainWindow):
	def __init__(self):
		super(testUI, self).__init__()
		self.resize(640,480)
		self.show()
		self.setMouseTracking(True)
		self.menu = None

	def mousePressEvent(self, event):
		if event.button() == QtCore.Qt.RightButton:
			print event.pos()
			if self.menu is not None: self.menu.close()

			self.menu = pp.popupMenu(self, event.pos(), abstractOffset=(40,40))
			#self.menu.setStyleSheet("background-color: #456")
			self.menu.initButtons(['test', 'pd', 'QtGui', 'abcd', 'efgh', 'ijkl'])
			self.menu.btnClicked.connect(self.receivedMessage)
			# print self.menu, self.menu.content


	def receivedMessage(self, message, menuPos):
		print message, 'at', menuPos

	def mouseMoveEvent(self, event):
		if self.menu is not None:
			if not self.menu.abstractRect.contains(event.pos().x(), event.pos().y()):
				self.menu.close()
				self.menu = None

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	win = testUI()
	sys.exit(app.exec_())