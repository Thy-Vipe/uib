from PySide.QtCore import *
from PySide.QtGui import *
from widgets import RubberBand
from utils import toClipBoard

class CLWI(QListWidgetItem):
	def __init__(self, text, obj):
		super(CLWI, self).__init__()
		self._obj = obj
		self._referenceId = obj.cid
		font = QFont()
		font.setPointSize(7.5)
		self.setFont(font)
		self.setText(text)
		self.setToolTip("""Double-click to copy corresponding code into ClipBoard.
		Note: holding CTRL while double-clicking will allow a name-specific query of the object,
		allowing a more supple management if the project will tend to change.
		If you use this mode, make sure the specified object has a ~name~ value.""")

	def getid(self): return self._referenceId
	def getobj(self): return self._obj

class CommandEditionLayout(QTextEdit):
	def __init__(self, parent):
		super(CommandEditionLayout, self).__init__(parent)
		self.stringLayout = None
		self.cursorPositionChanged.connect(self.qCursorPos)
		self.cp = 0

	def initStringLayout(self, string):
		pos = self.cursorPos
		layoutGeometry = QRect(pos, QPoint(len(string)*10, 10))
		if self.stringLayout:
			self.stringLayout.deleteLater()
			self.stringLayout = None

		self.stringLayout = RubberBand(self, geo=layoutGeometry)
		self.stringLayout.show()

	def qCursorPos(self): self.cursorPos = self.cursorRect().topLeft()

class Ui_commandEditor(object):
	def setupUi(self, commandEditor):
		commandEditor.setObjectName("commandEditor")
		commandEditor.resize(543, 313)
		commandEditor.setMinimumSize(QSize(543, 313))
		font = QFont()
		font.setWeight(50)
		commandEditor.setFont(font)
		self.horizontalLayoutWidget = QWidget(commandEditor)
		self.horizontalLayoutWidget.setGeometry(QRect(380, 270, 158, 41))
		self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
		self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
		self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
		self.horizontalLayout.setObjectName("horizontalLayout")
		self.applyBtn = QPushButton(self.horizontalLayoutWidget)
		self.applyBtn.setMinimumSize(QSize(50, 30))
		self.applyBtn.setObjectName("applyBtn")
		self.horizontalLayout.addWidget(self.applyBtn)
		self.closeBtn = QPushButton(self.horizontalLayoutWidget)
		self.closeBtn.setMinimumSize(QSize(50, 30))
		self.closeBtn.setObjectName("closeBtn")
		self.horizontalLayout.addWidget(self.closeBtn)
		self.listWidget = QListWidget(commandEditor)
		self.listWidget.setGeometry(QRect(0, 30, 131, 281))
		self.listWidget.setObjectName("listWidget")
		self.avItemsLabel = QLabel(commandEditor)
		self.avItemsLabel.setGeometry(QRect(0, 0, 131, 31))
		font = QFont()
		font.setFamily("MS Shell Dlg 2")
		font.setPointSize(13)
		self.avItemsLabel.setFont(font)
		self.avItemsLabel.setMargin(6)
		self.avItemsLabel.setObjectName("avItemsLabel")
		self.commandLayout = CommandEditionLayout(commandEditor)
		self.commandLayout.setGeometry(QRect(150, 30, 391, 231))
		self.commandLayout.setLineWrapMode(QTextEdit.NoWrap)
		self.commandLayout.setObjectName("commandLayout")
		self.commandLayout.setTabStopWidth(6)
		self.verticalSeparator = QFrame(commandEditor)
		self.verticalSeparator.setGeometry(QRect(130, 0, 20, 311))
		self.verticalSeparator.setFrameShape(QFrame.VLine)
		self.verticalSeparator.setFrameShadow(QFrame.Sunken)
		self.verticalSeparator.setObjectName("verticalSeparator")
		self.funcbtnLabel = QLabel(commandEditor)
		self.funcbtnLabel.setGeometry(QRect(150, 0, 201, 31))
		font = QFont()
		font.setFamily("MS Shell Dlg 2")
		font.setPointSize(13)
		self.funcbtnLabel.setFont(font)
		self.funcbtnLabel.setObjectName("funcbtnLabel")
		self.infoBox = QLabel(commandEditor)
		self.infoBox.setGeometry(QRect(150, 260, 211, 51))
		font = QFont()
		font.setPointSize(7)
		self.infoBox.setFont(font)
		self.infoBox.setWordWrap(True)
		self.infoBox.setMargin(0)
		self.infoBox.setObjectName("infoBox")

		self.retranslateUi(commandEditor)
		QMetaObject.connectSlotsByName(commandEditor)

	def retranslateUi(self, commandEditor):
		commandEditor.setWindowTitle(QApplication.translate("commandEditor", "Command editor.", None, QApplication.UnicodeUTF8))
		self.applyBtn.setText(QApplication.translate("commandEditor", "Apply", None, QApplication.UnicodeUTF8))
		self.closeBtn.setText(QApplication.translate("commandEditor", "Close", None, QApplication.UnicodeUTF8))
		self.avItemsLabel.setText(QApplication.translate("commandEditor", "Available items:", None, QApplication.UnicodeUTF8))
		self.funcbtnLabel.setText(QApplication.translate("commandEditor", "Button\'s Function:", None, QApplication.UnicodeUTF8))
		self.infoBox.setText(QApplication.translate("commandEditor", "Note: You can control other items in the interface. They are accessible via bui.content() which will return the list containing all object instances. Their CIDs are queryable from the left.", None, QApplication.UnicodeUTF8))

class CommandEditor(Ui_commandEditor, QDialog):
	def __init__(self, parent, cmdWidget):
		super(CommandEditor, self).__init__(parent)
		self.setWindowModality(Qt.ApplicationModal)
		self.setupUi(self)
		self.parent = parent #parent is the main UI, NOT the attributes editor.
		self.lastItem = None
		self.listWidget.itemSelectionChanged.connect(self.displayObj)
		self.listWidget.itemDoubleClicked.connect(self.copyToClipboard)
		self.closeBtn.clicked.connect(self.close)
		self.applyBtn.clicked.connect(self.applyNew)
		self.source = cmdWidget
		self.show()
		self.updateUi()

	def updateUi(self):
		for item in self.parent.items:
			self.listWidget.addItem(CLWI("%s @ID %d"%(item.objectType, item.cid), item))
		self.commandLayout.setText(self.source.text())

	def displayObj(self):
		if self.lastItem: self.lastItem.getobj().highlight(k=True)
		item = self.listWidget.selectedItems()[0]
		item.getobj().highlight(self.parent.viewport().UVLinesLayer)
		self.lastItem = item

	def copyToClipboard(self):
		item = self.listWidget.selectedItems()[0].getobj()
		if QApplication.keyboardModifiers() == Qt.ControlModifier:
			code = "uib.getByName(\"{n}\")[0]".format(n=item.objectName())
		else:
			code = "uib.content()[{i}]".format(i=item.cid)
		toClipBoard(code)
		print "Copied into Clip."

	def closeEvent(self, event):
		super(CommandEditor, self).closeEvent(event)
		if self.lastItem: self.lastItem.getobj().highlight(k=True)

	def applyNew(self):
		self.source.setText(self.commandLayout.toPlainText())
		if self.parent.attrsDialog: self.parent.attrsDialog.applyAttrs()

	def resizeEvent(self, event):
		defaultSize = (543, 313)
		defaultListWidgetSize = (131, 281)
		defaultLayoutSize = (391, 231)
		defaultButtonsPos = (380, 270)
		defaultInfoBoxPos = (150, 260)
		defaultSeparatorSize = (20, 311)
		currentSize = (self.width(), self.height())
		offset = (currentSize[0]-defaultSize[0],currentSize[1]-defaultSize[1])
		self.listWidget.resize(QSize(defaultListWidgetSize[0], defaultListWidgetSize[1]+offset[1]))
		self.verticalSeparator.resize(QSize(defaultSeparatorSize[0], defaultSeparatorSize[1]+offset[1]))
		self.commandLayout.resize(QSize(defaultLayoutSize[0]+offset[0], defaultLayoutSize[1]+offset[1]))
		self.infoBox.move(QPoint(defaultInfoBoxPos[0], defaultInfoBoxPos[1]+offset[1]))
		self.horizontalLayoutWidget.move(QPoint(defaultButtonsPos[0]+offset[0], defaultButtonsPos[1]+offset[1]))