from PySide import QtCore, QtGui



class MenuButton(QtGui.QPushButton):
	Clicked = QtCore.Signal(int)
	Released = QtCore.Signal(int)
	def __init__(self, parent, cid, text, size):
		super(MenuButton, self).__init__(parent)
		self.id = cid
		self.setText(text)
		self.setMinimumSize(QtCore.QSize(size[0], size[1]))
		self.setMaximumSize(QtCore.QSize(size[0], size[1]))
		self.show()

	def mousePressEvent(self, event):
		super(MenuButton, self).mousePressEvent(event)
		self.Clicked.emit(self.id)

	def mouseReleaseEvent(self, event):
		super(MenuButton, self).mouseReleaseEvent(event)
		self.Released.emit(self.id)

class MenuChkb(QtGui.QCheckBox):
	StateChanged = QtCore.Signal(int)
	def __init__(self, parent, cid, text, size):
		super(MenuChkb, self).__init__(parent)
		self.id = cid
		self.setText(text)
		self.setMaximumSize(QtCore.QSize(size[0], size[1]))
		self.setMaximumSize(QtCore.QSize(size[0], size[1]))
		self.stateChanged.connect(self.currentState)
		self.show()

	def currentState(self):
		StateChanged.emit(self.id)

class PopupMenu(QtGui.QFrame):
	btnClicked = QtCore.Signal(int, QtCore.QPoint)
	btnReleased = QtCore.Signal(int, QtCore.QPoint)
	checkBoxStateChange = QtCore.Signal(int, QtCore.QPoint)
	def __init__(self, parent, pos, size=None, abstractOffset=(20,20), destroyAfterClick=False):
		super(PopupMenu, self).__init__(parent)

		if size is None: size = (100,80)
		self.setGeometry(pos.x(), pos.y(), size[0], size[1])

		self.__visibleRect = self.geometry()
		self.__abstractRect = QtCore.QRect(self.__visibleRect.x()-abstractOffset[0], self.__visibleRect.y()-abstractOffset[1],\
		 self.__visibleRect.width()+abstractOffset[0]*2, self.__visibleRect.height()+abstractOffset[1]*2)
		self.__abstractOffset = abstractOffset
		self.setFrameShape(QtGui.QFrame.Box)
		self.setFrameShadow(QtGui.QFrame.Raised)

		self.destroyAfterClick = destroyAfterClick
		self.__menuPos = pos
		
		self.wid = QtGui.QWidget(self)
		self.contentLayout = QtGui.QVBoxLayout(self.wid)
		self.contentLayout.setContentsMargins(0, 0, 2, 2)
		self.contentLayout.setSpacing(0)
		self.children = None
		self.childrenPosOffset = None
		
		self.content = []
		self.show()

	def initButtons(self, content, ids=None, styleSheet=None, styleSheets=None, btnDim=(100,25)):
		lenght = len(content)
		if ids is None: ids = range(lenght)

		if lenght != len(ids): 
			raise TypeError, "Invalid amount of parameters. There must be as much IDs than names."
		if styleSheets is not None: 
			if lenght != len(styleSheets): 
				raise TypeError, "Invalid amount of parameters. There must be as much stylesheets than names.\nIf you use the same styleSheet, use 'styleSheet' as param instead."

		for name, cid, row in zip(content, ids, range(lenght)):
			self.content.append(MenuButton(self.wid, cid=cid, text=name, size=btnDim))
			self.contentLayout.addWidget(self.content[row])
			if styleSheets is not None: btn.setStyleSheet(styleSheets[row])
			elif styleSheet is not None: btn.setStyleSheet(styleSheet)
			self.content[row].Clicked.connect(self.btnClickedMessage)
			self.content[row].Released.connect(self.btnReleasedMessage)

		self.resize(QtCore.QSize(btnDim[0]+5, btnDim[1]*lenght+3))
		self.updateGeom()

	def initCheckBoxes(self, content, ids=None, styleSheet=None, stylesheets=None, chkbDim=(100,20)):
		lenght = len(content)
		if ids is None: ids = range(lenght)

		if lenght != len(ids): 
			raise TypeError, "Invalid amount of parameters. There must be as much IDs than names."
		if styleSheets is not None: 
			if lenght != len(styleSheets): 
				raise TypeError, "Invalid amount of parameters. There must be as much stylesheets than names.\nIf you use the same styleSheet, use 'styleSheet' as param instead."

		for name, cid, row in zip(content, ids, range(lenght)):
			self.content.append(MenuChkb(self.wid, cid=cid, text=name, size=chkbDim))
			self.contentLayout.addWidget(self.content[row])
			if styleSheets is not None: btn.setStyleSheet(styleSheets[row])
			elif styleSheet is not None: btn.setStyleSheet(styleSheet)
			self.content[row].Clicked.connect(self.btnClickedMessage)
			self.content[row].Released.connect(self.btnReleasedMessage)

		self.resize(QtCore.QSize(chkbDim[0]+5, chkbDim[1]*lenght+3))
		self.updateGeom()

	def updateGeom(self):
		self.setGeometry(self.__menuPos.x(), self.__menuPos.y(), self.width(), self.height())
		self.__visibleRect = self.geometry()
		self.__abstractRect = QtCore.QRect(self.__visibleRect.x()-self.__abstractOffset[0], self.__visibleRect.y()-self.__abstractOffset[1],\
		 self.__visibleRect.width()+self.__abstractOffset[0]*2, self.__visibleRect.height()+self.__abstractOffset[1]*2)
		self.wid.setGeometry(3,3, self.__visibleRect.width()-3, self.__visibleRect.height()-3)

	def btnClickedMessage(self, message):
		self.btnClicked.emit(message, self.__menuPos)

	def btnReleasedMessage(self, message):
		self.btnReleased.emit(message, self.__menuPos)

		if self.destroyAfterClick:
			self.close()

	def getPos(self): return self.__menuPos
	def getRect(self): return self.__visibleRect
	def getAbstractRect(self): return self.__abstractRect
	def getOffset(self): return self.__abstractOffset
	def getContent(self): return self.content
	def query(self, type_, copy=False):
		output = []
		types = {
			"button":MenuButton,
			"checkbox":MenuChkb
		}
		if type_ not in types.keys(): raise TypeError("Invalid type. Type must be \'checkbox\' or \'button\'")
		for item in self.content:
			if isinstance(item, types[type_]):
				output.append(item)
		if copy: output = tuple(output)
		return output

	def move(self, pos):
		super(PopupMenu, self).move(pos)
		self.__menuPos = pos
		self.updateGeom()
		if self.children:
			childrenPos = QtCore.QPoint(self.__menuPos.x()+self.childrenPosOffset.x(), self.__menuPos.y()+self.childrenPosOffset.y())
			self.children.move(childrenPos)

	def setChildren(self, children):
		self.children = children
		self.childrenPosOffset = QtCore.QPoint(children.pos().x()-self.__menuPos.x(), children.pos().y()-self.__menuPos.y())

	def killChildren(self):
		self.children.deleteLater()
		self.childrenPosOffset = None
		self.children = None