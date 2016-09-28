from PySide import QtCore, QtGui
from utils import convert_to_str, convert_to_list

class itemOptionsWidget(QtGui.QWidget):
	output = QtCore.Signal(dict)
	def __init__(self, parent, pos):
		super(itemOptionsWidget, self).__init__(parent)

		self.setGeometry(QtCore.QRect(pos.x(), pos.y(), 181, 181))
		self.setObjectName("widget")
		self.hLabel = QtGui.QLabel(self)
		self.hLabel.setGeometry(QtCore.QRect(10, 42, 41, 21))
		self.hLabel.setTextFormat(QtCore.Qt.AutoText)
		self.hLabel.setObjectName("wLabel_2")
		self.wLabel = QtGui.QLabel(self)
		self.wLabel.setGeometry(QtCore.QRect(10, 10, 41, 21))
		self.wLabel.setTextFormat(QtCore.Qt.AutoText)
		self.wLabel.setObjectName("wLabel_3")
		self.nameLabel = QtGui.QLabel(self)
		self.nameLabel.setGeometry(QtCore.QRect(10, 69, 46, 13))
		self.nameLabel.setObjectName("nameLabel")
		self.itemNameLE = QtGui.QLineEdit(self)
		self.itemNameLE.setGeometry(QtCore.QRect(60, 67, 113, 21))
		self.itemNameLE.setObjectName("itemNameLE")
		self.wSB = QtGui.QSpinBox(self)
		self.wSB.setGeometry(QtCore.QRect(60, 10, 51, 22))
		self.wSB.setObjectName("wSB")
		self.hSB = QtGui.QSpinBox(self)
		self.hSB.setGeometry(QtCore.QRect(60, 40, 51, 22))
		self.hSB.setObjectName("hSB")
		self.tagsLabel = QtGui.QLabel(self)
		self.tagsLabel.setGeometry(QtCore.QRect(10, 92, 41, 16))
		self.tagsLabel.setObjectName("tagsLabel")
		self.itemTagsLE = QtGui.QLineEdit(self)
		self.itemTagsLE.setGeometry(QtCore.QRect(60, 90, 113, 20))
		self.itemTagsLE.setObjectName("itemTagsLE")
		self.attrsEditBtn = QtGui.QPushButton(self)
		self.attrsEditBtn.setGeometry(QtCore.QRect(45, 125, 90, 23))
		self.xLabel = QtGui.QLabel(self)
		self.xLabel.setGeometry(QtCore.QRect(120, 10, 16, 21))
		self.xLabel.setObjectName("xLabel")
		self.yLabel = QtGui.QLabel(self)
		self.yLabel.setGeometry(QtCore.QRect(120, 42, 16, 21))
		self.yLabel.setObjectName("yLabel")
		self.xSB = QtGui.QSpinBox(self)
		self.xSB.setGeometry(QtCore.QRect(130, 10, 51, 22))
		self.xSB.setObjectName("xSB")
		self.ySB = QtGui.QSpinBox(self)
		self.ySB.setGeometry(QtCore.QRect(130, 40, 51, 22))
		self.ySB.setObjectName("ySB")

		self.hLabel.setText("Height:")
		self.wLabel.setText("Width:")
		self.nameLabel.setText("Label:")
		self.tagsLabel.setText("Tag(s):")
		self.attrsEditBtn.setText("Set attributes...")
		self.xLabel.setText("X:")
		self.yLabel.setText("Y:")
		self.wSB.setMaximum(999999)
		self.wSB.setMinimum(-999999)
		self.hSB.setMaximum(999999)
		self.hSB.setMinimum(-999999)
		self.xSB.setMaximum(999999)
		self.xSB.setMinimum(-999999)
		self.ySB.setMaximum(999999)
		self.ySB.setMinimum(-999999)

		self.initSignals()
		self.show()

	def initSignals(self):
		self.wSB.valueChanged.connect(self.updateObjectMessage)
		self.hSB.valueChanged.connect(self.updateObjectMessage)
		self.xSB.valueChanged.connect(self.updateObjectMessage)
		self.ySB.valueChanged.connect(self.updateObjectMessage)
		self.itemNameLE.textChanged.connect(self.updateObjectMessage)
		self.itemTagsLE.textChanged.connect(self.updateObjectMessage)

	def updateObjectMessage(self):
		dic = {
			"width":self.wSB.value(),
			"height":self.hSB.value(),
			"posX":self.xSB.value(),
			"posY":self.ySB.value(),
			"tags":self.itemTagsLE.text(),
			"name":self.itemNameLE.text()
		}
		self.output.emit(dic)

	def updateValues(self, **values):
		self.wSB.setValue(values['geo'].width())
		self.hSB.setValue(values['geo'].height())
		self.xSB.setValue(values['geo'].x())
		self.ySB.setValue(values['geo'].y())
		self.itemNameLE.setText(values.get('label', self.itemNameLE.text()))
		self.itemTagsLE.setText(convert_to_str(values.get('tags', convert_to_list(self.itemTagsLE.text()))))
