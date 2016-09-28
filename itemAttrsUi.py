from PySide.QtCore import *
from PySide.QtGui import *
from widgets import *
from commandEditor import CommandEditor
from stylesheetEditor import StylesheetEditor

CLASSES_ENUM = {
	"label":Label,
	"command_button":CommandButton,
	"selector":Selector,
	"checkbox":CheckBox,
	"line_edit":LineEdit,
	"text_edit":TextEdit,
	"slider":Slider,
	"frame":Frame,
	"float_field":FloatField
}

COMPLEXSTRING_EDITOR = {
	"command": CommandEditor,
	"stylesheet": StylesheetEditor
}
class BoolEditor(QComboBox):
	def __init__(self, parent, val, et=False, t=None):
		super(BoolEditor, self).__init__(parent)
		self.setMinimumSize(QSize(50,20))
		self.parent = parent
		if not et: self.addItems(["True","False"])
		else: self.addItems(t)
		if val: self.setCurrentIndex(0)
		elif not val: self.setCurrentIndex(1) 
		self.show()

	def get(self):
		val = self.currentText()
		response = {
			'True':True,
			'False':False,
			'U':'U',
			'V':'V'
		} 
		val = response[val]
		return val

class IntEditor(QSpinBox):
	def __init__(self, parent, val):
		super(IntEditor, self).__init__(parent)
		self.parent = parent
		self.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
		self.setMinimumSize(QSize(50,20))
		self.setMinimum(-999999)
		self.setMaximum(999999)
		self.setValue(val)
		self.show()

	def get(self): return self.value()

class FloatEditor(QDoubleSpinBox):
	def __init__(self, parent, val):
		super(FloatEditor, self).__init__(parent)
		self.parent = parent
		self.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
		self.setMinimumSize(QSize(50,20))
		self.setMinimum(-999999.0)
		self.setMaximum(999999.0)
		self.setValue(val)
		self.show()

	def get(self): return self.value()

class TextEditor(QLineEdit):
	def __init__(self, parent, txt):
		super(TextEditor, self).__init__(parent)
		self.parent = parent
		self.setMinimumSize(QSize(50,20))
		self.setPlaceholderText("Arg...")
		self.setText(txt)
		self.show()

	def get(self): return str(self.text())

	def wheelEvent(self, event):
		text = self.selectedText()
		p = self.selectionStart()
		ep = p + len(text)
		allText = self.text()
		try:
			value = int(text)
		except:
			return

		if QApplication.keyboardModifiers() == Qt.ControlModifier: mult = 10
		elif QApplication.keyboardModifiers() == Qt.ShiftModifier: mult = 5
		else: mult = 1
		if event.delta() < 0:
			value -= 1*mult
		elif event.delta() > 0:
			value += 1*mult
		value = str(value)
		l = len(value)
		newText = "%s%s%s"%(allText[:p], value, allText[ep:])
		self.setText(newText)
		self.setSelection(p, l)

class AttrsDialItem(QWidget):
	def __init__(self, parent, Y, inputAttr, inputAttrStr):
		super(AttrsDialItem, self).__init__(parent)
		self.parent = parent
		self.setGeometry(0, Y, parent.width(), 30)
		self.layout = QHBoxLayout(self)
		self.layout.setContentsMargins(10, -1, 6, -1)
		self.attrLabel = QLabel(self)
		self.attrLabel.setMinimumSize(QSize(170, 25))
		self.attrLabel.setText(inputAttrStr)
		self.attrValue = self.getAttrEditor(inputAttr)
		self.layout.addWidget(self.attrLabel)
		self.layout.addWidget(self.attrValue)
		if inputAttrStr in ("cmd", "stylesheet", "valueChanged_cmd"):
			self.moreBtn = QPushButton(self)
			self.moreBtn.setMinimumSize(QSize(25,20))
			self.moreBtn.setMaximumSize(QSize(25,20))
			self.moreBtn.setText("...")
			self.moreBtn.clicked.connect(self.onButtonClicked)
			self.layout.addWidget(self.moreBtn)
		self.show()

	def getAttrEditor(self, inputAttr):
		print inputAttr
		if inputAttr in ('U', 'V'): return BoolEditor(self, inputAttr, et=True, t=['U', 'V'])
		elif isinstance(inputAttr, bool): return BoolEditor(self, inputAttr)
		elif isinstance(inputAttr, float): return FloatEditor(self, inputAttr)
		elif isinstance(inputAttr, (str, unicode)): return TextEditor(self, str(inputAttr))
		elif isinstance(inputAttr, int): return IntEditor(self, inputAttr)
		else: 
			error = QLabel(self)
			error.setMinimumSize(QSize(120, 25))
			error.setText("Unsupported type.")
			return error

	def onButtonClicked(self):
		if "cmd" in self.attrLabel.text(): self.editor = COMPLEXSTRING_EDITOR["command"](self.parent.parent, self.attrValue) #We climb up to the main UI to access everything.
		elif self.attrLabel.text() == "stylesheet": self.editor = COMPLEXSTRING_EDITOR["stylesheet"](self.parent.parent, self.attrValue)

class ItemAttrsDial(QDialog):
	def __init__(self, parent, widget):
		super(ItemAttrsDial, self).__init__(parent)
		self.setObjectName("AttrEditor")
		self.setWindowModality(Qt.ApplicationModal) # Lock app while window is active. 
		self.setWindowTitle("{} Attributes".format(widget.objectType))
		self.resize(340, 30)
		self.wid = widget
		self.parent = parent
		self.attributes = widget.serialize()[widget.objectType]
		self.attributesWidgets = []
		offset = 50
		attrs = self.attributes.keys()
		skippedValues = ['label', 'geo', 'cid', 'tags']
		for delete in skippedValues:
			try:
				attrs.remove(delete)
			except:
				pass

		for attr, i in zip(attrs, range(len(self.attributes))):
		 	offset = 30*i+2
			newHolder = AttrsDialItem(self, offset, self.attributes[attr], attr)
		 	self.attributesWidgets.append(newHolder)
		offset += 40

		self.separator = QFrame(self)
		self.separator.setFrameShape(QFrame.VLine)
		self.separator.setFrameShadow(QFrame.Sunken)
		self.saveButton = QPushButton(self)
		self.saveButton.setGeometry(QRect(self.width()-128, offset, 60, 30))
		self.saveButton.setText("Apply")
		self.saveButton.clicked.connect(self.applyAttrs)
		self.closeButton = QPushButton(self)
		self.closeButton.setGeometry(QRect(self.width()-66, offset, 60, 30))
		self.closeButton.setText("Close")
		self.closeButton.clicked.connect(self.close)
		self.resize(340, offset+32)
		self.separator.setGeometry(QRect(160, 0, 20, self.height()))
		self.setMinimumSize(QSize(340, offset+32))
		self.setMaximumSize(QSize(340, offset+32))
		QMetaObject.connectSlotsByName(self)
		self.saveButton.setFocus()
		self.show()

	def applyAttrs(self):
		attributes = self.wid.serialize()[self.wid.objectType]
		newAttributes = self.attributesWidgets

		for new in newAttributes:
			attributes[new.attrLabel.text()] = new.attrValue.get()

		print attributes
		self.wid.deserialize(attributes)


		
