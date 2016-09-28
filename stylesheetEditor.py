from PySide.QtCore import *
from PySide.QtGui import *
from widgets import RubberBand
from utils import toClipBoard

USER_COMMANDS = {
	"Linear gradient":("qlineargradient(x1:?, y1:?, x2:?, y2:?, stop:??, stop:??)",\
		"""
		Gradients are specified in a Bounding Box. Imagine the box in which the gradient is rendered,
		to have its top left corner at (0, 0) and its bottom right corner at (1, 1). Gradient parameters
		are then specified as percentages from 0 to 1. These values are extrapolated to actual box coordinates at runtime. 
		It is possible specify values that lie outside the bounding box (-0.6 or 1.8, for instance).

		> Linear gradients interpolate colors between start and end points.
		> x1 and y1 define the start position of the gradient.
		> x2 and y2 define its end. Both are parameters between 0.0 and 1.0.
		> You can add as many <stop> as you wish. It must be followed by two values: 
			-a position parameter (value between 0.0 and 1.0)
			-a color value in hex, hsv, hsva, rgb or rgba.
		For instance: 'stop:0.5 rgba(42, 84, 168, 125)'
		> Warning: The stops have to appear sorted in ascending order.
		"""),
	"Conical gradient":("qconicalgradient(cx:?, cy:?, angle:?, stop:??, stop:??",\
		"""
		Gradients are specified in a Bounding Box. Imagine the box in which the gradient is rendered,
		to have its top left corner at (0, 0) and its bottom right corner at (1, 1). Gradient parameters
		are then specified as percentages from 0 to 1. These values are extrapolated to actual box coordinates at runtime. 
		It is possible specify values that lie outside the bounding box (-0.6 or 1.8, for instance).

		> Conical gradients interpolate colors around a center point.
		> cx and cy define the center point.
		> You can add as many <stop> as you wish. It must be followed by two values: 
			-a position parameter (value between 0.0 and 1.0)
			-a color value in hex, hsv, hsva, rgb or rgba.
		For instance: 'stop:0.5 rgba(42, 84, 168, 125)'
		> Warning: The stops have to appear sorted in ascending order.
		"""),
	"Radial gradient":("qradialgradient(cx:?, xy:?, radius:?, fx:?, fy:?, stop:??, stop:??",\
		"""
		Gradients are specified in a Bounding Box. Imagine the box in which the gradient is rendered,
		to have its top left corner at (0, 0) and its bottom right corner at (1, 1). Gradient parameters
		are then specified as percentages from 0 to 1. These values are extrapolated to actual box coordinates at runtime. 
		It is possible specify values that lie outside the bounding box (-0.6 or 1.8, for instance).

		> Radial gradients interpolate colors between a focal point and end points on a circle surrounding it.
		> cx and cy define the focal point.
		> fx and fy define the end point.
		> You can add as many <stop> as you wish. It must be followed by two values: 
			-a position parameter (value between 0.0 and 1.0)
			-a color value in hex, hsv, hsva, rgb or rgba.
		For instance: 'stop:0.5 rgba(42, 84, 168, 125)'
		> Warning: The stops have to appear sorted in ascending order.
		"""),
	"URL/Path":("url(<path>)",\
		"""
		Allows using images using a path/link. Path must be written like for instance: url('C:/user/documents/image.jpg') 
		"""),
	"Color RGB":("rgb(r, g, b",\
		"""
		Specifies a color as RGB. The values can be used with integer values in the range 0-255 or with percentages.
		For instance: 'rgb(42%, 21%, 84%)' or 'rgb(220, 12, 128)'.
		"""),
	"Color RGBA":("rgba(r, g, b, a",\
		"""
		Specifies a color as RGBA. The values can be used with integer values in the range 0-255 or with percentages.
		For instance: 'rgba(42%, 21%, 84%, 75%)' or 'rgba(220, 12, 128, 184)'.       
		"""),
	"Color HSV":("hsv(h, s, v)",\
		"""
		Hue, Saturation, Value.
		Specifies a color as HSV. The values of s, v must be used with integer values in the range 0-255
		while the value of h must be in the range 0-359.
		"""),
	"Color HSVA":("hsva( h, s, v, a%",\
		"""
		Hue, Saturation, Value, Alpha.
		Specifies a color as HSVA. The values of s, v must be used with integer values in the range 0-255
		while the value of h must be in the range 0-359 and the value of a must be with percentage.        
		"""),
	"Color HEX":("#RRGGBB",\
		"""
		Hexadecimal color (base 16). Can be written #RGB, #RRGGBB and even #RRRGGGBBB. Does not support alpha channel.
		For instance: '#1FA5B8'.
		"""),
	"More...":("http://doc.qt.io/qt-4.8/stylesheet-reference.html",\
		"""
		Check Qt Documentation for more informations about stylesheets...
		""")
}

USER_SETTINGS = {
	"BG repeat mode":("background-repeat: ",\
		"""
		Repeat setting for the background if it's an image.
		Available values are:
			> repeat (default), no need to specify this property if so.
			> no-repeat
			> repeat-y
			> repeat-z
		"""
		),
	"Shorthand BG":("background: ",\
		"""
		Shorthand notation for setting the background. Equivalent to specifying bg-color, bg-image,
		bg-repeat and/or bg-position.
		For instance: 'background: qlineargradient([...]) url(image.jpg) no-repeat top;'.
		"""
		),
	"BG color":("background-color: ",\
		"""
		Specifies background color. RGB/HSV/RGBA/HSVA/HEX
		"""
		),
	"BG image":("background-image: ",\
		"""
		Background image specified using an URL.
		If the image appears to have Alpha Channel, the transparency will let appear the background color.
		"""
		),
	"BG position":("background-position: ",\
		"""
		Background's alignment. Available values are:
			> top
			> bottom
			> left
			> right
			> center
		"""
		),
	"BG attachment":("background-attachment: ",\
		"""
		Determines if wether or not the background-image is fixed in a scroll area. 
		By default, the background-image scrolls with the viewport. 
		Available values are:
			> fixed
			> scroll
		"""
		),
	"BG clip":("background-clip: ",\
		"""
		The widget's rectangle, in which the background is drawn.
		This property specifies the rectangle to which the background-color and background-image are clipped.
		Available values are:
			> margin
			> border (default)
			> padding
			> content
		"""),
	"BG origin":("background-origin: ",\
		"""
		The widget's background rectangle, to use in conjunction with background-position and background-image.
		Available values are:
			> margin
			> border
			> padding (default)
			> content
		"""
		),
	"Border":("border: ",\
		"""
		Syntax is border: <width> <style> <brush>
		Example: 'border: 3px solid rgb(15%, 25%, 42%);'
		<solid> is a style. Available styles are:
			> dashed
			> dot-dash
			> dot-dot-dash
			> dotted
			> double
			> groove
			> inset
			> outset
			> ridge
			> solid
			> none
		"""
		),
	"Top Border":("border-top: ",\
		"""
		Shorthand notation for setting the widget's top border. Equivalent to specifying border-top-color,
		border-top-style, and/or border-top-width.
		Syntax: 'border-top: <width> <style> <color>'
		Example: 'border-top: 2px inset #FFC5FF'
		"""
		),
	"Right Border":("border-right: ",\
		"""
		Shorthand notation for setting the widget's right border. Equivalent to specifying border-right-color,
		border-right-style, and/or border-right-width.
		Syntax: 'border-right: <width> <style> <color>'
		Example: 'border-right: 2px inset #FFC5FF'
		"""
		),
	"Left Border":("border-left: ",\
		"""
		Shorthand notation for setting the widget's left border. Equivalent to specifying border-left-color,
		border-left-style, and/or border-left-width.
		Syntax: 'border-left: <width> <style> <color>'
		Example: 'border-left: 2px inset #FFC5FF'
		"""
		),
	"Bottom Border":("border-bottom: ",\
		"""
		Shorthand notation for setting the widget's bottom border. Equivalent to specifying border-bottom-color,
		border-bottom-style, and/or border-bottom-width.
		Syntax: 'border-bottom: <width> <style> <color>'
		Example: 'border-bottom: 2px inset #FFC5FF'
		"""
		),
	"Border Color":("border-color: ",\
		"""
		The color of all the border's edges. Equivalent to specifying border-top-color, 
		border-right-color, border-bottom-color, and border-left-color.
		Example: 'border-color: #F00'
		"""
		),
	"Border Radius":("border-radius: ",\
		"""
		The radius of the border's corners. Equivalent to specifying border-top-left-radius, 
		border-top-right-radius, border-bottom-right-radius, and border-bottom-left-radius.
		Must be specified in px. For instance: 8px
		"""
		),
	"Top Left border Radius":("border-top-left-radius: ",\
		"""
		Must be specified in px. For instance: 8px
		"""
		),
	"Top Right border Radius":("border-top-right-radius: ",\
		"""
		Must be specified in px. For instance: 8px
		"""
		),
	"Bottom Left border Radius":("border-bottom-left-radius: ",\
		"""
		Must be specified in px. For instance: 8px
		"""
		),
	"Bottom Right border Radius":("border-bottom-right-radius: ",\
		"""
		Must be specified in px. For instance: 8px
		"""
		),
	"Border Style":("border-style: ",\
		"""
		Available styles are:
			> dashed
			> dot-dash
			> dot-dot-dash
			> dotted
			> double
			> groove
			> inset
			> outset
			> ridge
			> solid
			> none        
		"""
		),
	"Margin":("margin: ",\
		"""
		Shorthand notation for setting the widget's margins. Margin must be provided in px.,
		for instance: "margin: 15px" 
		"""),
	"Margin Left":("margin-left: ",\
		"""
		The widget's left margin. Margin must be provided in px. 
		"""),
	"Margin Right":("margin-right: ",\
		"""
		The widget's right margin. Margin must be provided in px. 
		"""),
	"Margin Top":("margin-top: ",\
		"""
		The widget's top margin. Margin must be provided in px. 
		"""),
	"Margin Bottom":("margin-bottom: ",\
		"""
		The widget's right margin. Margin must be provided in px. 
		"""),
	"Font": ("font: ",\
		"""
		Shorthand notation for setting the text's font. Equivalent to specifying font-family, 
		font-size, font-style, and/or font-weight.
		Syntax: 'font: <fontFamily> <fontSize> <fontStyle> *<fontWeight>'
			> Available fonts families are registered in your computer.
			> fontSize in points (default is 8)
			> fontStyle:
				- normal
				- italic
				- oblique
			> fontWeight:
				- normal
				- bold
				- any value in the range 100-900
		"""
		),
	"More...": ("http://doc.qt.io/qt-4.8/stylesheet-reference.html",\
		"""
		Check Qt's stylesheet documentation for more.
		""")
}
class SLWI(QListWidgetItem):
	def __init__(self, text, command, details=""):
		super(SLWI, self).__init__()
		self._cmd = command
		font = QFont()
		font.setItalic(True)
		font.setPointSize(8)
		self.setFont(font)
		self.setText(text)
		self.setToolTip(
			"""
			Double-click to copy corresponding command into ClipBoard.
			{commandInfo}
			""".format(commandInfo=details)
			)

	def getCommand(self): return self._cmd

class Ui_stylesheetEditor(object):
	def setupUi(self, stylesheetEditor):
		stylesheetEditor.setObjectName("stylesheetEditor")
		stylesheetEditor.resize(543, 313)
		stylesheetEditor.setMinimumSize(QSize(543, 313))
		font = QFont()
		font.setWeight(50)
		stylesheetEditor.setFont(font)
		self.horizontalLayoutWidget = QWidget(stylesheetEditor)
		self.horizontalLayoutWidget.setGeometry(QRect(380, 270, 158, 41))
		self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
		self.acHLayout = QHBoxLayout(self.horizontalLayoutWidget)
		self.acHLayout.setContentsMargins(0, 0, 0, 0)
		self.acHLayout.setObjectName("acHLayout")
		self.applyBtn = QPushButton(self.horizontalLayoutWidget)
		self.applyBtn.setMinimumSize(QSize(50, 30))
		self.applyBtn.setObjectName("applyBtn")
		self.acHLayout.addWidget(self.applyBtn)
		self.closeBtn = QPushButton(self.horizontalLayoutWidget)
		self.closeBtn.setMinimumSize(QSize(50, 30))
		self.closeBtn.setObjectName("closeBtn")
		self.acHLayout.addWidget(self.closeBtn)
		self.listWidget = QListWidget(stylesheetEditor)
		self.listWidget.setGeometry(QRect(0, 30, 131, 126))
		self.listWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
		self.listWidget.setObjectName("listWidget")
		self.avFuncsLabel = QLabel(stylesheetEditor)
		self.avFuncsLabel.setGeometry(QRect(0, 0, 131, 31))
		font = QFont()
		font.setFamily("MS Shell Dlg 2")
		font.setPointSize(11)
		self.avFuncsLabel.setFont(font)
		self.avFuncsLabel.setMargin(3)
		self.avFuncsLabel.setObjectName("avFuncsLabel")
		self.verticalSeparator = QFrame(stylesheetEditor)
		self.verticalSeparator.setGeometry(QRect(130, 0, 20, 311))
		self.verticalSeparator.setFrameShape(QFrame.VLine)
		self.verticalSeparator.setFrameShadow(QFrame.Sunken)
		self.verticalSeparator.setObjectName("verticalSeparator")
		self.itemStylesheetLabel = QLabel(stylesheetEditor)
		self.itemStylesheetLabel.setGeometry(QRect(150, 0, 201, 31))
		font = QFont()
		font.setFamily("MS Shell Dlg 2")
		font.setPointSize(13)
		self.itemStylesheetLabel.setFont(font)
		self.itemStylesheetLabel.setObjectName("itemStylesheetLabel")
		self.infoBox = QLabel(stylesheetEditor)
		self.infoBox.setGeometry(QRect(150, 260, 211, 51))
		font = QFont()
		font.setPointSize(7)
		self.infoBox.setFont(font)
		self.infoBox.setWordWrap(True)
		self.infoBox.setMargin(0)
		self.infoBox.setObjectName("infoBox")
		self.commandLayout = QTextEdit(stylesheetEditor)
		self.commandLayout.setGeometry(QRect(150, 30, 391, 231))
		self.commandLayout.setLineWrapMode(QTextEdit.NoWrap)
		self.commandLayout.setTabStopWidth(6)
		self.commandLayout.setObjectName("commandLayout")
		self.settingsListWidget = QListWidget(stylesheetEditor)
		self.settingsListWidget.setGeometry(QRect(0, 180, 131, 126))
		self.settingsListWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
		self.settingsListWidget.setObjectName("settingsListWidget")
		self.avSettingsLabel = QLabel(stylesheetEditor)
		self.avSettingsLabel.setGeometry(QRect(0, 150, 131, 31))
		font = QFont()
		font.setFamily("MS Shell Dlg 2")
		font.setPointSize(11)
		self.avSettingsLabel.setFont(font)
		self.avSettingsLabel.setMargin(3)
		self.avSettingsLabel.setObjectName("avSettingsLabel")

		self.retranslateUi(stylesheetEditor)
		QMetaObject.connectSlotsByName(stylesheetEditor)

	def retranslateUi(self, stylesheetEditor):
		stylesheetEditor.setWindowTitle(QApplication.translate("stylesheetEditor", "stylesheetEditor", None, QApplication.UnicodeUTF8))
		self.applyBtn.setText(QApplication.translate("stylesheetEditor", "Apply", None, QApplication.UnicodeUTF8))
		self.closeBtn.setText(QApplication.translate("stylesheetEditor", "Close", None, QApplication.UnicodeUTF8))
		self.avFuncsLabel.setText(QApplication.translate("stylesheetEditor", "Available functions:", None, QApplication.UnicodeUTF8))
		self.itemStylesheetLabel.setText(QApplication.translate("stylesheetEditor", "Item\'s stylesheet:", None, QApplication.UnicodeUTF8))
		self.infoBox.setText(QApplication.translate("stylesheetEditor", "Note: You can use bui.userValues.set(<valueName>, <value>) to store different values for communication purposes. ", None, QApplication.UnicodeUTF8))
		self.avSettingsLabel.setText(QApplication.translate("stylesheetEditor", "Available settings:", None, QApplication.UnicodeUTF8))

class StylesheetEditor(Ui_stylesheetEditor, QDialog):
	def __init__(self, parent, ssWidget):
		super(StylesheetEditor, self).__init__(parent)
		self.setWindowModality(Qt.ApplicationModal)
		self.setupUi(self)
		self.parent = parent #parent is the main UI, NOT the attributes editor.
		self.lastItem = None
		self.listWidget.itemDoubleClicked.connect(self.copyCommandToClipboard)
		self.settingsListWidget.itemDoubleClicked.connect(self.copyPropertyToClipboard)
		self.closeBtn.clicked.connect(self.close)
		self.applyBtn.clicked.connect(self.applyNew)
		self.source = ssWidget
		self.show()
		self.updateUi()

	def updateUi(self):
		# Sorted the way I want.
		userCommands = ["Linear gradient", "Radial gradient", "Conical gradient", "Color RGB", "Color RGBA", "Color HSV", "Color HSVA", "Color HEX", "URL/Path", "More..."]
		userProperties = ["Shorthand BG","BG color", "BG image", "BG clip", "BG attachment", "BG position", "BG origin", "BG repeat mode", "Border", "Top Border", \
		"Bottom Border", "Left Border", "Right Border","Border Color", "Border Radius", "Top Left border Radius", "Bottom Left border Radius", "Top Right border Radius",\
		"Bottom Right border Radius", "Border Style", "Margin", "Margin Left", "Margin Right", "Margin Top", "Margin Bottom", "Font", "More..."]
		for item in userCommands:
			self.listWidget.addItem(SLWI(item, USER_COMMANDS[item][0], USER_COMMANDS[item][1]))
		for item in userProperties:
			self.settingsListWidget.addItem(SLWI(item, USER_SETTINGS[item][0], USER_SETTINGS[item][1]))
		self.commandLayout.setText(self.source.text())

	def copyCommandToClipboard(self):
		item = self.listWidget.selectedItems()[0]
		code = item.getCommand()
		toClipBoard(code)
		print "Copied into Clip."

	def copyPropertyToClipboard(self):
		item = self.settingsListWidget.selectedItems()[0]
		code = item.getCommand()
		toClipBoard(code)
		print "Copied into Clip."

	def closeEvent(self, event):
		super(StylesheetEditor, self).closeEvent(event)

	def resizeEvent(self, event):
		defaultSize = (543, 313)
		defaultListWidgetSize = (131, 126)
		defaultSettingsListWidSize = (131,126)
		defaultLayoutSize = (391, 231)
		defaultButtonsPos = (380, 270)
		defaultInfoBoxPos = (150, 260)
		defaultSeparatorSize = (20, 311)
		currentSize = (self.width(), self.height())
		offset = (currentSize[0]-defaultSize[0],currentSize[1]-defaultSize[1])
		self.listWidget.resize(QSize(defaultListWidgetSize[0], defaultListWidgetSize[1]+offset[1]/2))
		self.avSettingsLabel.move(self.listWidget.geometry().bottomLeft())
		self.settingsListWidget.move(self.avSettingsLabel.geometry().bottomLeft())
		self.settingsListWidget.resize(QSize(defaultSettingsListWidSize[0], defaultSettingsListWidSize[1]+offset[1]/2))
		self.verticalSeparator.resize(QSize(defaultSeparatorSize[0], defaultSeparatorSize[1]+offset[1]))
		self.commandLayout.resize(QSize(defaultLayoutSize[0]+offset[0], defaultLayoutSize[1]+offset[1]))
		self.infoBox.move(QPoint(defaultInfoBoxPos[0], defaultInfoBoxPos[1]+offset[1]))
		self.horizontalLayoutWidget.move(QPoint(defaultButtonsPos[0]+offset[0], defaultButtonsPos[1]+offset[1]))

	def applyNew(self):
		self.source.setText(self.commandLayout.toPlainText())
		self.parent.attrsDialog.applyAttrs()
		print "Changes saved."