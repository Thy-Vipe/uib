from PySide.QtCore import QRect
# from PySide.QtGui import *
from utils import getParameters, getHIB
import os

CORRESPONDING_CLASSES = {
	"label":"QLabel",
	"command_button":"QPushButton",
	"selector":None, #Won't be supported for now. Let's get the basic thing to work first..
	"checkbox":"QCheckBox",
	"line_edit":"QLineEdit",
	"text_edit":"QTextEdit",
	"slider":"QSlider",
	"frame":"QFrame",
	"float_field":"QDoubleSpinBox"
}

baseInit = \
"""
        self.object{v} = {classObj}(self)
        self.object{v}.setGeometry(QRect(*{rec}))
        self.content.append(self.object{v})"""

baseSetup = \
"""
        self.object{v}.setStyleSheet('{ss}')"""

baseToolTip = \
"""
        self.object{v}.setToolTip('{tt}')"""

baseParams = \
"""
        self.parameters = {paramsList}"""

baseFont = \
"""
        font = QFont()
        {fpt}
        {fam}
        self.object{v}.setFont(font)"""

def createBaseStructure(content, precision):
	geo = getHIB(content)
	contentGeo = []
	for item in content:
		currentGeo = item.geometry()
		newgeo = QRect()
		newgeo.setX(currentGeo.x()-geo.x())
		newgeo.setY(currentGeo.y()-geo.y())
		newgeo.setWidth(currentGeo.width())
		newgeo.setHeight(currentGeo.height())
		contentGeo.append(newgeo.getRect())
	ngeo = QRect(0,0, geo.width(), geo.height())
	positionParameters = []
	for item in content:
		positionParameters.append(getParameters(item.geometry(), geo, 0,3, pre=precision))

	return ngeo, contentGeo, positionParameters


def buildAttributes(content):
	stylesheets = [obj.widget.styleSheet() for obj in content]
	names = [obj.objectName() for obj in content]
	return stylesheets, names

def getClassName(content):
	classes = []
	newContent = []
	for item in content:
		newClass = CORRESPONDING_CLASSES[item.objectType]
		if newClass:
			classes.append(newClass)
			newContent.append(item)
		else:
			Warning("Unsupported object: {}, skipped.".format(item.objectType))

	return classes, newContent


def encodeWidget(className, content, parametersPrecision=4):
	classNames, content = getClassName(content)
	widGeometry, contentGeometry, widParameters = createBaseStructure(content, parametersPrecision)
	stylesheets, names = buildAttributes(content)
	#First, build the base.
	contentInit_block = "self.content = []\n"
	qstyleSheets_block = ""
	qtooltips_block = ""
	params = baseParams.format(paramsList=str(widParameters))
	for item, classType, objName, n, cg, qss in zip(content, classNames, names, range(len(content)), contentGeometry, stylesheets):
		contentInit_block += baseInit.format(classObj=classType, v=n, rec=cg, name=objName)
		if classType == "QSlider" and item.orient == "U": contentInit_block += "\n        self.object{v}.setOrientation(Qt.Horizontal)".format(v=n)
		if item.text() != "": 
			contentInit_block += "\n        self.object{v}.setText('{string}')".format(v=n, string=item.text())
			try:
				contentInit_block += baseFont.format(v=n, fpt="font.setPointSize({})".format(item.fontSize(q=1)), fam="")
			except: pass
		if qss != "NoStyleSheet": qstyleSheets_block += baseSetup.format(v=n, ss=qss.replace("\n", ""))
		if item.tooltip != '': qtooltips_block += baseToolTip.format(v=n, tt=item.tooltip)

	path = os.path.dirname(os.path.realpath(__file__))
	with open("%s\\encoderStructure.uibref"%path, "r") as baseCodeFile:
		struc = baseCodeFile.read()
		code = struc.format(CLASSNAME=className, CONTENT_INIT=contentInit_block,\
			CONTAINED_ITEMS_QSTYLE_ATTRS=qstyleSheets_block, CONTAINED_ITEMS_TOOLTIPS=qtooltips_block, ITEMS_PARAMS=params, OBJ_DEFAULTGEO=widGeometry.getRect())

	with open("%s\\%s_CLASS.py"%(path, className), "w") as outputFile:
		outputFile.write(code)

