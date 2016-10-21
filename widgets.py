from PySide.QtGui import *
from PySide.QtCore import *
import os
import utils
SoftwarePlugin = None

DEFAULT_COMMAND_BUTTON_CODE = """def clicked():
  pass
  # only the code inside clicked() will be executed
"""
DEFAULT_SLIDER_CODE = """def value_changed():
  pass
  # only the code inside value_changed() will be executed
"""

DEFAULT_CHECKBOX_CODE = """def on():
  pass

def off():
  pass
  
# only the code inside on() and off() will be executed
"""

RUBBERBAND_STYLE = {
	'blue': "background-color: rgba(33, 159, 222, 65); border: 2px solid #2B9AD6",
	'red': "background-color: rgba(242, 79, 46, 65); border: 2px solid #FF2A00",
	'green': "background-color: rgba(69, 199, 46, 65); border: 2px solid #169100",
	'frame': "background-color: rgba(0,0,0,0); border: 1px solid #A7A7A7",
	'blue-no_bg': "background-color: rgba(0,0,0,0); border: 2px solid #2B9AD6",
	'green-no_bg': "background-color: rgba(0,0,0,0); border: 2px solid #16C200", 
	'orange': "background-color: rgba(255, 127, 80, 100); border: 4px solid #FF4500"
}


"""
QRectangle subclass to add one more value for hitboxes. 
"""
class Identifier(QRect):
	def __init__(self, identity, *args):
		super(Identifier, self).__init__(*args)
		self._identity = identity

	def getIdentity(self): return self._identity
	def setIdentity(self, identity): self._identity = identity


"""
Allows drawing a selection rectangle on the viewport. Comes with a few "quick" colors whose stylesheet's visible in RUBBERBAND_STYLE.
"""
class RubberBand(QFrame):
	def __init__(self, parent, **kwargs):
		super(RubberBand, self).__init__(parent)
		color = kwargs.get("color", 'blue')
		self.setStyleSheet(RUBBERBAND_STYLE[color])
		self.__geometry = kwargs.get("geo", QRect(0,0,0,0))
		self.__pos = kwargs.get("pos", self.__geometry.topLeft())
		self.setGeometry(self.__geometry)

	def setGeometry(self, qrect):
		"""
		Set the RB's geometry. It is pretty much like the original function, as a matter of fact.
		"""
		if isinstance(qrect, QRect): pass
		elif isinstance(qrect, (tuple, list)): qrect = QRect(*qrect)
		else: raise TypeError("Input must be of type tuple, list or QRectangle.")
		geo = QRect(qrect.x()-2, qrect.y()-2, qrect.width()+4, qrect.height()+4)
		super(RubberBand, self).setGeometry(geo)
		self.__geometry = qrect
		self.__pos = QPoint(qrect.x(), qrect.y())

	def move(self, pos):
		geo = self.geometry()
		self.__pos = pos
		self.setGeometry(QRect(pos.x(), pos.y(), geo.width(), geo.height()))

	def geometry(self): return QRect(*self.__geometry.getRect())
	def pos(self): return self.__pos
	def recolor(self, color='blue', asValues=False):
		"""
		Recolors the RubberBand. Generally not used, but it makes this class "module-able" for any other project.
		"""
		if not asValues:
			self.setStyleSheet(RUBBERBAND_STYLE[color])
		else:
			if isinstance(color, dict):
				self.setStyleSheet("background-color: {bgcolor}; border: {thk}px solid {bcol}".format(**color))
			else:
				raise TypeError, "With this setting, color must be DICT containing \'bgcolor\', \'thk\' for border thickness, and \'bcol\' for border color. Excepted \'thk\' that is an integer, all values must be strings."

	def delete(self):
		self.hide()
		del self
		self = None
		
"""
Line widget to make alignments noticeable when existing. Red when not aligned, but close. Green when exactly aligned with any other instance on the Ui.
"""
class UVLine(QFrame):
    def __init__(self, parent, pos, w, h, **kwargs):
        super(UVLine, self).__init__(parent)
        self.state = None
        self.styleSheet = {
            "normal":"background-color: {bgColor}; border: 1px solid {borColor};".format(bgColor=kwargs.get('bgColor1', '#FF1111'), borColor=kwargs.get('borderColor1', '#DD1111')), 
            "highlighted":"background-color: {bgColor}; border: 1px solid {borColor};".format(bgColor=kwargs.get('bgColor2', '#1DC200'), borColor=kwargs.get('borderColor2', '#2BD90D'))
            }
        self.shiftStyleSheet("normal")
        self.setGeometry(QRect(pos.x(), pos.y(), w, h))
        self.show()

    def shiftStyleSheet(self, name):
        self.setStyleSheet(self.styleSheet[name])
        self.state = name
        self.update()

    def highlight(self):
    	if self.state == "highlighted": self.shiftStyleSheet("normal")
    	else: self.shiftStyleSheet("highlighted")


"""
Base Class for every instance used in the programm. Allows a proper control of them.
"""
class BaseControl(QObject):
	def __init__(self, **kwargs):
		super(BaseControl, self).__init__()
		self._tags = kwargs.get('tags', [])
		self._geometry = kwargs.get('geo', None)
		self._hoffset = kwargs.get('offset', (0,0))
		self._hitbox = kwargs.get('hgeo', None)
		self._pos = QPoint(0,0)
		self._text = ""
		self._highlighting = None
		self._contour = None
		self._contourPoints = None
		self.stylesheet = "NoStyleSheet"
		self.objectHL_locked = False
		self.isSelectable = False
		self.tooltip = ""
		self._fontSize = 8

	def move(self, pos):
		self._pos = pos
		self.widget.move(pos)
		geo = self.widget.geometry()
		self._geometry = geo
		self._hitbox = QRect(geo.x()-self._hoffset[0], geo.y()-self._hoffset[1], geo.width()+self._hoffset[0]*2, geo.height()+self._hoffset[1]*2)
		self.contour()
		self.highlight(e=True)

	def setText(self, text):
		self._text = text
		self.widget.setText(text)

	def setStyleSheet(self, stylesheet):
		self.widget.setStyleSheet(stylesheet)
		self.stylesheet = stylesheet

	def styleSheet(self): return self.widget.styleSheet()

	def setGeometry(self, geo, client=False):
		if isinstance(geo, QRect): pass
		elif isinstance(geo, (tuple, list)): geo = QRect(*geo)
		else: raise TypeError("Input must be of type tuple, list or QRectangle.")
		self._geometry = geo
		self._pos = QPoint(geo.x(), geo.y())
		self._hitbox = QRect(geo.x()-self._hoffset[0], geo.y()-self._hoffset[1], geo.width()+self._hoffset[0]*2, geo.height()+self._hoffset[1]*2)
		if not client: self.contour()
		self.widget.setGeometry(geo)
		self.highlight(e=True)

	def show(self):
		if self._highlighting: self._highlighting.show()
		self.widget.show()

	def hide(self):
		if self._highlighting: self._highlighting.hide()
		self.widget.hide()

	# safely delete the control
	def delete(self):
		if self._highlighting: self._highlighting.deleteLater()
		self.widget.hide()
		self.widget.deleteLater()
		self.deleteLater()

	def geometry(self): return QRect(*self._geometry.getRect())
	def setHOffset(self, offset): 
		self._hoffset = offset
		geo = self.geometry()
		self._hitbox = QRect(geo.x()-self._hoffset[0], geo.y()-self._hoffset[1], geo.width()+self._hoffset[0]*2, geo.height()+self._hoffset[1]*2)
	def getHOffset(self): return self._hoffset
	def hitbox(self): return self._hitbox
	def setTags(self, tags, asStr=False): 
		if not asStr: 
			if isinstance(tags, list): self._tags = tags
			else: raise TypeError("Invalid input: ~tags~ must be list. Use asStr=True and send a str value if not using a list.")
		else:
			self._tags = utils.convert_to_list(str(tags))

	def getTags(self): return self._tags
	def text(self): return self._text
	def raise_(self): self.widget.raise_()
	def lower(self): self.widget.lower()
	def pos(self): return self._pos
	def setup(self): pass
	def highlight(self, c=False, parent=None, color="green", k=False, e=False, lock=False, unlock=None):
		"""
		This function draws a highlight rectangle around the object's geometry. For showing "selected" for instance, or an error.
		c=True creates a HR with default parent (item's parent).
		parent=<wid> to define an other parent
		color is... Straight forward.
		k=True to kill if HL isn't locked
		e=True to edit geometry automatically to object's (w/o other args)
		lock=True to lock the HL
		unlock=True to unlock it. 
		"""
		if unlock:
			self.objectHL_locked = False

		if k and not self.objectHL_locked:
			self.objectHL_locked = lock
			if self._highlighting:
				self._highlighting.deleteLater()
				self._highlighting = None

		if parent:
			if self._highlighting: 
				if not self.objectHL_locked: self._highlighting.deleteLater()
				else: return
			self._highlighting = RubberBand(parent, color=color, geo=self.geometry())
			self._highlighting.lower()
			self._highlighting.show()
			self.objectHL_locked = lock
		elif c:
			if self._highlighting: 
				if not self.objectHL_locked: self._highlighting.deleteLater()
				else: return
			self._highlighting = RubberBand(self.parent, color=color, geo=self.geometry())
			if not lock: self._highlighting.lower()
			self._highlighting.show()
			self.objectHL_locked = lock		

		if e:
			if self._highlighting:
				self._highlighting.setGeometry(self.geometry())

	def contour(self, size=(8,8)): # Generates a hitbox for each side and corner of the Widget's QRect.
		rect = self.geometry()
		self._contourPoints = [(rect.topLeft(), rect.topRight()),\
				(rect.topLeft(), rect.bottomLeft()),\
				(rect.bottomLeft(), rect.bottomRight()),\
				(rect.topRight(), rect.bottomRight())]
		rect = QRect(rect.x()-size[0]/2, rect.y()-size[1]/2, rect.width()+size[0]/2-3, rect.height()+size[1]/2-3)
		self._contour = []
		contourPoints = [(rect.topLeft(), rect.topRight()),\
				(rect.topLeft(), rect.bottomLeft()),\
				(rect.bottomLeft(), rect.bottomRight()),\
				(rect.topRight(), rect.bottomRight())]
		direction = [(1,0),(0,1),(1,0), (0,1)]
		ids = ["topSide", "leftSide", "bottomSide", "rightSide"]
		n = 0
		for p1p2 in contourPoints:
			p1, p2 = p1p2[0], p1p2[1]
			lenght = QSize((p2.x()-p1.x())*direction[n][0]+size[0], (p2.y()-p1.y())*direction[n][1]+size[1])
			side = Identifier(ids[n], p1, lenght)
			self._contour.append(side)
			n += 1

	def getContours(self): return (self._contour, ['U','V', 'U', 'V'])
	def getContoursPoints(self): return self._contourPoints


class Label(BaseControl):
	def __init__(self, parent, **kwargs):
		super(Label, self).__init__()
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QLabel(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setText(kwargs.get("label", ""))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'label'
		self.fontSize(s=kwargs.get("font_size", 8))
		self.show()

	def fontSize(self, s=8, q=False):
		if not q:
			self._fontSize = s
			font = QFont()
			font.setPointSize(s)
			self.widget.setFont(font)
		else: return self._fontSize

	def serialize(self):
		return {
			'label':{
				"cid": self.cid,
				"geo": self.geometry(),
				"label": self.text(),
				"tags": self.getTags(),
				"font_size":self.fontSize(q=True),
				"stylesheet":self.stylesheet,
				"name":self.objectName()
			}
		}

	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json['cid']
			
		self.fontSize(s=json['font_size'])
		self.setText(json['label'])
		self.setGeometry(json['geo'], client=client)
		self.setTags(json['tags'])
		self.setObjectName(json.get("name", ""))
		self.stylesheet = json.get("stylesheet", "noStyleSheet")
		self.setup()

	def setup(self):
		if self.stylesheet.upper() == "NOSTYLESHEET":
			pass
		else:
			self.setStyleSheet(self.stylesheet)


class Frame(BaseControl):
	def __init__(self, parent, **kwargs):
		super(Frame, self).__init__()
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QFrame(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'frame'
		self.backgroundColor = "rgba(100,100,100,255)"
		self.borderColor = "#C1C1C1"
		self.borderThickness = 2
		self.borderRadius = 0
		self.widget.setStyleSheet("background-color: {bgc}; border-radius: {brad}px; border: {thk}px solid {borc};".format(bgc=self.backgroundColor, borc=self.borderColor, thk=self.borderThickness, brad=self.borderRadius))
		self.show()		

	def serialize(self):
		return {
			'frame':{
				"cid": self.cid,
				"geo": self.geometry(),
				"tags": self.getTags(),
				"bg_color": self.backgroundColor,
				"border_thickness": self.borderThickness,
				"border_color": self.borderColor,
				"border_radius": self.borderRadius, 
				"stylesheet": self.stylesheet,
				"name": self.objectName()
			}
		}

	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json['cid']
			
		self.setGeometry(json["geo"], client=client)
		self.setTags(json["tags"])
		self.borderColor = json["border_color"]
		self.borderThickness = json["border_thickness"]
		self.backgroundColor = json["bg_color"]
		self.borderRadius = json["border_radius"]
		self.stylesheet = json["stylesheet"]
		self.setObjectName(json.get("name", ""))
		self.setup()

	def setup(self):
		if self.stylesheet.upper() == "NOSTYLESHEET":
			self.widget.setStyleSheet("background-color: {bgc}; border-radius: {brad}px; border: {thk}px solid {borc};".format(bgc=self.backgroundColor, borc=self.borderColor, thk=self.borderThickness, brad=self.borderRadius))
		else:
			self.setStyleSheet(self.stylesheet)


class LineEdit(BaseControl):
	def __init__(self, parent, **kwargs):
		super(LineEdit, self).__init__()
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QLineEdit(parent)	
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'line_edit'		
		self._fontSize = kwargs.get("fontSize", 8)
		font = QFont()
		font.setPointSize(self._fontSize)
		self.widget.setFont(font)
		self.stylesheet = "NoStyleSheet"
		self.show()

	def fontSize(self, s=8, q=False):
		if not q:
			self._fontSize = s
			font = QFont()
			font.setPointSize(s)
			self.widget.setFont(font)
		else: return self._fontSize

	def serialize(self):
		return {
			'line_edit':{
				"cid": self.cid,
				"geo": self.geometry(),
				"label": self.text(),
				"tags": self.getTags(),
				"font_size":self.fontSize(q=True),
				"stylesheet":self.stylesheet,
				"name":self.objectName()
			}
		}

	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json['cid']

		self.setGeometry(json['geo'], client=client)
		self.setTags(json['tags'])
		self.fontSize(s=json['font_size'])
		self.setText(json['label'])
		self.stylesheet = json['stylesheet']
		self.setObjectName(json.get("name", ""))
		self.setup()

	def setup(self):
		if self.stylesheet.upper() == "NOSTYLESHEET":
			pass
		else:
			self.setStyleSheet(self.stylesheet)


class TextEdit(BaseControl):
	def __init__(self, parent, **kwargs):
		super(TextEdit, self).__init__()
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QTextEdit(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'text_edit'	
		self._fontSize = kwargs.get("fontSize", 8)
		font = QFont()
		font.setPointSize(self._fontSize)
		self.widget.setFont(font)
		self.show()

	def fontSize(self, s=8, q=False):
		if not q:
			self._fontSize = s
			font = QFont()
			font.setPointSize(s)
			self.widget.setFont(font)
		else: return self._fontSize

	def serialize(self):
		return {
			'text_edit':{
				"cid": self.cid,
				"geo": self.geometry(),
				"label": self.text(),
				"tags": self.getTags(),
				"font_size":self.fontSize(q=True),
				"stylesheet":self.stylesheet,
				"name":self.objectName()
			}
		}

	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json['cid']

		self.fontSize(s=json['font_size'])
		self.setText(json['label'])
		self.setGeometry(json['geo'], client=client)
		self.setTags(json['tags'])
		self.stylesheet = json['stylesheet']
		self.setObjectName(json.get("name", ""))
		self.setup()

	def setup(self):
		if self.stylesheet.upper() == "NOSTYLESHEET":
			pass
		else:
			self.setStyleSheet(self.stylesheet)


class Selector(BaseControl):
	clicked = Signal()

	def __init__(self, parent, **kwargs):
		super(Selector, self).__init__()
		# define default parameters
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QPushButton(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.color = "#777777" # default color: grey
		self.objectType = 'selector'
		self.override_color = False
		self.target_objs = []
		self.tooltip = ""
		self.radius = 10
		self.is_selected = False
		self.widget.setText("") # clear the label
		self.isSelectable = True

		# load the stylesheet for the selector
		with open(os.path.abspath(os.path.dirname(__file__)) + '\\selector.qss', 'r') as qss_file:
			self.stylesheet = qss_file.read()

		self.setup() # apply settings
		self.show() 
		
		self.widget.clicked.connect(self.onWidgetTriggered)
	
	'''
	Base class override.
	'''
	def setGeometry(self, geo, client=False):
		if isinstance(geo, QRect): pass
		elif isinstance(geo, (tuple, list)): geo = QRect(*geo)
		else: raise TypeError("Input must be of type tuple, list or QRectangle.")
		self.move(QPoint(geo.x(), geo.y()))
		self.radius = geo.width()
		self._geometry = geo
		self._hitbox = QRect(geo.x()-self._hoffset[0], geo.y()-self._hoffset[1], geo.width()+self._hoffset[0]*2, geo.height()+self._hoffset[1]*2)
		if not client: self.contour()

	def colorCode(self):
		if self.override_color:
			try:
				top_obj = SoftwarePlugin.PyNode(self.target_objs[0]) # get the first of the target objects
			except: # if target object does not exist display the warning
				SoftwarePlugin.warning("Object {} not found. Make sure the correct scene is loaded.".format(self.target_objs[0]))
				return
			color = utils.getOverrideColor(top_obj) # set the override color (see utils.py)
			if color:
				self.color = color

	'''
	Implements the main functionality of the selector - selecting assigned objects
	'''
	def action(self, drag=False):
		appendSelection = drag or QApplication.keyboardModifiers() == Qt.ShiftModifier # selecting by dragging or shift selecting
		targetSet = set(self.target_objs) # convert to python set for convenience
		selectionSet = set(map(str, SoftwarePlugin.ls(sl=1))) # get the object names for selected nodes and convert to set for convenience

		# if target objects are selected and appending is on
		if targetSet <= selectionSet and appendSelection: 
			SoftwarePlugin.select(list(selectionSet - targetSet)) # remove target objects from selection leaving everything else selected
		else:
			if appendSelection: # add target objects to selection
				SoftwarePlugin.select(self.target_objs, add=1)
			else:
				SoftwarePlugin.select(self.target_objs) # replace current selection with target objects

	def onWidgetTriggered(self):
		self.clicked.emit()

	def redraw(self):
		radius = self.radius - 1.3 if self.is_selected else self.radius # taking the border into account
		args = {
			"color": self.color,
			"brighter": utils.brighter(self.color),
			"darker": utils.darker(self.color),
			"radius": radius,
			"double_radius": radius * 2,
			"border": 2 if self.is_selected else 0 # show 2 pixel border if the selector is activated
		}
		self.widget.setStyleSheet(self.stylesheet.format(**args)) # redraw the widget

	'''
	Returns JSON representation of the control
	'''
	def serialize(self):
		return {
		"selector" : {
				"cid": self.cid,
				"target_objs": self.target_objs,
				"color": self.color,
				"tags": self.getTags(),
				"override_color": self.override_color,
				"tooltip": self.tooltip,
				"radius": self.radius,
				"geo": self.geometry(),
				"name":self.objectName()
			}
		}

	'''
	Loads the control from JSON representation
	'''
	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json["cid"]

		self.target_objs = json["target_objs"]
		self.color = json["color"]
		self.setTags(json["tags"])
		self.override_color = json["override_color"]
		self.tooltip = json["tooltip"]
		self.radius = json.get("radius", 10)
		self.setGeometry(json.get("geo"), client=client)
		self.setObjectName(json.get("name", ""))

	'''
	Apply the settings to control
	'''
	def setup(self, client=False):
		if client: # if loaded by CUI Viewer
			self.widget.setToolTip(self.tooltip)
			self.colorCode()
			self.clicked.connect(self.action)
		else:
			self.widget.setToolTip("Control ID: {}".format(self.cid)) # show cid in tooltip
		self.redraw() # redraw


class CommandButton(BaseControl):
	clicked = Signal()

	def __init__(self, parent, **kwargs):
		super(CommandButton, self).__init__()
		# define default parameters
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QPushButton(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'command_button'
		self.cmd = DEFAULT_COMMAND_BUTTON_CODE
		self.tooltip = ""
		self.function = None
		self.functionEdited = True
		self.parent = parent
		
		self.setup()
		self.show()
		
		self.widget.clicked.connect(self.onWidgetTriggered)
		self.clicked.connect(self.action)

	def onWidgetTriggered(self):
		self.clicked.emit()

	'''
	Returns JSON representation of the control
	'''
	def serialize(self):
		return {
		"command_button": {
				"cid": self.cid,
				"cmd": self.cmd,
				"label": self.text(),
				"tags": self.getTags(),
				"tooltip": self.tooltip,
				"geo": self.geometry(),
				"stylesheet":self.stylesheet,
				"name":self.objectName()
			}
		}

	'''
	Loads the control from JSON representation
	'''
	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json["cid"]

		self.cmd = json["cmd"]
		self.functionEdited = True
		self.setText(json["label"])
		self.setTags(json["tags"])
		self.setGeometry(json["geo"], client=client)
		self.tooltip = json["tooltip"]
		self.stylesheet = json['stylesheet']
		self.setObjectName(json.get("name", ""))
		self.action()
		self.setup(client=client)

	'''
	Apply the settings to control
	'''
	def setup(self, client=False):
		self.setStyleSheet(self.stylesheet)
		if client: # if loaded by CUI Viewer
			self.widget.setToolTip(self.tooltip)
		else:
			self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

	def action(self):
		if self.function is None or self.functionEdited: # if activating first time we need to compile the assigned code
			try:
				self.function = utils.compileFunctions(self.cmd, ["clicked"], self.parent.symbols)[0]
				self.highlight(k=True, unlock=True)
				self.functionEdited = False
			except Exception: # if something went wrong display the warning
				self.highlight(c=True, color="orange", lock=True)
				raise TypeError("Could not compile the functions for the control {name} with ID {id}. Please, check the code.".format(name=self.objectType, id=self.cid))
				return

		self.function() # run the assigned code


class Slider(BaseControl):
	valueChanged = Signal()
	released = Signal()

	def __init__(self, parent, **kwargs):
		super(Slider, self).__init__()
		# setting up default settings
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QSlider(parent)
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'slider'
		self.target_attr = ""
		self.is_dir_ctrl = False
		self.min_attr_val = 0.0
		self.max_attr_val = 1.0
		self.clamp_to_int = False
		self.orient = kwargs.get('orient', 'U') 
		self.default_val = 0.0
		self.tooltip = ""
		self.valueChangedCmd = DEFAULT_SLIDER_CODE
		self.VCfunction = None
		self.VCfunctionEdited = True
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setup() # apply the settings
		self.show()
		
		self.widget.valueChanged.connect(self.onValueChanged)
		self.widget.sliderReleased.connect(self.onReleased)

	def onValueChanged(self):
		if not self.is_dir_ctrl: self.valueChangedCommand()
		else: self.valueChanged.emit()

	def onReleased(self):
		if self.is_dir_ctrl: self.released.emit()

	def value(self):
		currentPos = self.widget.value()+0.5
		range_ = float(self.max_attr_val - self.min_attr_val)
		value = range_ * (currentPos/float(self.widget.maximum()))

		if not self.clamp_to_int: return value
		else: return int(value)

	def setValue(self, value):
		range_ = float(self.max_attr_val - self.min_attr_val)
		newPos = int((value/range_)*float(self.widget.maximum())) #Value between 0 and *X*
		self.widget.setValue(newPos)

	def setGeometry(self, geo, client=False):
		if isinstance(geo, QRect): pass
		elif isinstance(geo, (tuple, list)): geo = QRect(*geo)
		else: raise TypeError("Input must be of type tuple, list or QRectangle.")
		super(Slider, self).setGeometry(geo)
		if self.orient == 'U': lenght = self.widget.geometry().width()
		elif self.orient == 'V': lenght = self.widget.geometry().height()
		self.widget.setMaximum(lenght)
		if not client: self.contour()

	'''
	Returns JSON representation of the control
	'''
	def serialize(self):
		return {
			"slider": {
				"cid": self.cid,
				"orient": self.orient,
				"target_attr": self.target_attr,
				"min_attr_val": self.min_attr_val,
				"max_attr_val": self.max_attr_val,
				"clamp_to_int": self.clamp_to_int,
				"tags": self.getTags(),
				"default_val": self.default_val,
				"tooltip": self.tooltip,
				"geo": self.geometry(),
				"stylesheet": self.stylesheet,
				"name": self.objectName(),
				"valueChanged_cmd": self.valueChangedCmd,
				"is_dir_ctrl": self.is_dir_ctrl
				}
		}

	'''
	Loads the control from JSON representation
	'''
	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json["cid"]

		self.orient = json["orient"]
		orient = Qt.Horizontal if self.orient == 'U' else Qt.Vertical
		self.widget.setOrientation(orient)
		self.target_attr = json["target_attr"]
		self.min_attr_val = json["min_attr_val"]
		self.max_attr_val = json["max_attr_val"]
		self.clamp_to_int = json["clamp_to_int"]
		self.setTags(json["tags"])
		self.default_val = json["default_val"]
		self.setValue(self.default_val)
		self.tooltip = json["tooltip"]
		self.setGeometry(json["geo"], client=client)
		self.stylesheet = json["stylesheet"]
		self.setObjectName(json.get("name", ""))
		self.valueChangedCmd = json.get("valueChanged_cmd", DEFAULT_SLIDER_CODE)
		self.is_dir_ctrl = json.get("is_dir_ctrl", True)
		self.VCfunctionEdited = True
		self.valueChangedCommand()
		self.setup(client)
	'''
	Apply current settings
	'''
	def setup(self, client=False):
		self.setStyleSheet(self.stylesheet)
		self.setValue(self.default_val)
		if client: # if loaded in ReadOnly Mode. (mode 1; see builder.py)
			self.widget.setToolTip(self.tooltip)
			self.valueChanged.connect(self.valueChangedAction)
			self.released.connect(self.releasedAction)
		else:
			self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

	'''
	Process the slider move event by updating the assigned attribute
	'''
	def valueChangedAction(self):
		if self.target_attr == "": # if nothing assigned
			self.highlight(c=True, lock=True, color="orange")
			raise RuntimeError("No attribute assigned to this controler.")
			return

		range_ = self.max_attr_val - self.min_attr_val # offset between max and min
		step = range_/100 # a value per percent
		val = self.min_attr_val + self.value() * step # min + percent value * step

		if self.clamp_to_int:
			val = round(val) # round to nearest integer
		
		utils.undoable_open() # open Maya undo chunk
		SoftwarePlugin.setAttr(self.target_attr, val) # update the attribute

	def releasedAction(self):
		utils.undoable_close() # when slider is released - free the undo chunk

	'''
	Update the control to match current attribute value
	'''
	def updateControl(self):
		range_ = self.max_attr_val - self.min_attr_val # offset between max and min
		try:
			attrVal = SoftwarePlugin.getAttr(self.target_attr) # get the current value
		except Exception: # if attribute is not accessible or does not exist
			return

		val = (attrVal - self.min_attr_val)/(range_/100) # calculate the percent value for slider
		self.widget.blockSignals(True) # block signals to avoid the unwanted attribute update
		self.widget.setValue(round(val)) # set slider value rounding it to nearest integer
		self.widget.blockSignals(False) # unblock the signals

	def valueChangedCommand(self):
		if self.VCfunction is None or self.VCfunctionEdited: # if activating first time we need to compile the assigned code
			try:
				self.VCfunction = utils.compileFunctions(self.valueChangedCmd, ["value_changed"], self.parent.symbols)[0]
				self.highlight(k=True, unlock=True)
				self.VCfunctionEdited = False
			except Exception: # if something went wrong display the warning
				self.highlight(c=True, color="orange", lock=True)
				raise TypeError("Could not compile the functions for the control {name} with ID {id}. Please, check the code.".format(name=self.objectType, id=self.cid))
				return

		self.VCfunction() # run the assigned code

class CheckBox(BaseControl):
	stateChanged = Signal()

	def __init__(self, parent, **kwargs):
		super(CheckBox, self).__init__()
		# set up the default settings
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = QCheckBox(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'checkbox'
		self.cmd = DEFAULT_CHECKBOX_CODE
		self.is_dir_ctrl = True
		self.target_attr = ""
		self.default_state = False
		self.label = "Checkbox"
		self.tooltip = ""
		self.on_cmd = None
		self.off_cmd = None
		self.functionEdited = True
		 # init the underlying Qt widget
		self.setup() # apply the settings
		self.show()
		
		self.widget.stateChanged.connect(self.onStateChanged)
		self.stateChanged.connect(self.toggledAction)

	def isChecked(self):
		return self.widget.isChecked()
		
	def onStateChanged(self):
		self.stateChanged.emit()

	'''
	Apply current settings
	'''
	def setup(self, client=False):	
		self.setStyleSheet(self.stylesheet)
		if client: # if loaded by CUI Viewer
			self.widget.setToolTip(self.tooltip)
			self.widget.setChecked(self.default_state)
		else:
			self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

	'''
	Process the checked/unchecked state update
	'''
	def toggledAction(self):
		if self.is_dir_ctrl: # if controling an attribute directly
			if not self.target_attr: # if no attribute assigned
				self.highlight(c=True, color="orange", lock=True)
				raise RuntimeError("No attribute assigned to the control {name} with ID {id}.".format(name=self.objectType, id=self.cid))
				return
			else:
				self.highlight(k=True, unlock=True)
				try:
					SoftwarePlugin.setAttr(self.target_attr, self.isChecked()) # set the boolean value for the attribute
				except:
					ImportError("Program isn't coupled with a software module.")

		else: # is a command checkbox
			if not (self.on_cmd and self.off_cmd) or self.functionEdited: # if commands not compiled
				try:
					funcs = utils.compileFunctions(self.cmd, ["on", "off"], self.parent.symbols)
					self.on_cmd = funcs[0] # get the on() function
					self.off_cmd = funcs[1] # get the off() function
					self.highlight(k=True, unlock=True)
					self.functionEdited = False
				except Exception as ie: # error occured while compiling
					self.highlight(c=True, color="orange", lock=True)
					raise TypeError("Could not compile the functions for the control {name} with ID {id}. Please, check the code.".format(name=self.objectType, id=self.cid))
					return

			if self.isChecked():
				self.on_cmd() # checked => run on()
			else:
				self.off_cmd() # unchecked => run off()

	'''
	Returns the JSON representation of the control
	'''
	def serialize(self):
		return {
			"checkbox": {
				"cid": self.cid,
				"cmd": self.cmd,
				"is_dir_ctrl": self.is_dir_ctrl,
				"target_attr": self.target_attr,
				"default_state": self.default_state,
				"label": self.text(),
				"tags": self.getTags(),
				"tooltip": self.tooltip,
				"geo": self.geometry(),
				"stylesheet": self.stylesheet,
				"name": self.objectName()
			}
		}

	'''
	Loads the control from JSON representation
	'''
	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json["cid"]
		
		self.setGeometry(json["geo"], client=client)
		self.cmd = json["cmd"]
		self.functionEdited = True
		self.is_dir_ctrl = json["is_dir_ctrl"]
		self.target_attr = json["target_attr"]
		self.default_state = json["default_state"]
		self.setText(json["label"])
		self.setTags(json["tags"])
		self.tooltip = json["tooltip"]
		self.stylesheet = json["stylesheet"]
		self.setObjectName(json.get("name", ""))
		self.toggledAction()
		self.setup()
	'''
	Update the state from Maya attribute
	'''
	def updateControl(self):
		if self.is_dir_ctrl: # if controling an attribute directly
			if not self.target_attr: # if no attribute assigned
				self.highlight(c=True, color="orange", lock=True)
				raise RuntimeError("No attribute assigned to the control {name} with ID {id}.".format(name=self.objectType, id=self.cid))
				return
			else:
				self.highlight(k=True, unlock=True)
				try:
					attrVal = SoftwarePlugin.getAttr(self.target_attr)
					self.widget.setChecked(attrVal)
				except:
					ImportError("Program isn't coupled with a software module.")


'''
Have to subclass, because QDoubleSpinBox does not 
have any signals to be used as trigger notification
'''
class FloatFieldBase(QDoubleSpinBox):
	focused = Signal()

	def __init__(self, p):
		super(FloatFieldBase, self).__init__(p)
		self.setButtonSymbols(QSpinBox.NoButtons)
		self.setFocusPolicy(Qt.ClickFocus)
		self.setMinimum(-10000)
		self.setMaximum(10000)
		self.setSingleStep(0.1)

	def focusInEvent(self, event):
		if event.reason() == Qt.MouseFocusReason:
			self.focused.emit()
		else:
			event.ignore()


class FloatField(BaseControl):
	focused = Signal()

	def __init__(self, parent, **kwargs):
		super(FloatField, self).__init__()
		# set up the default settings
		self.parent = parent
		self.cid = kwargs.get("cid", -1)
		self.widget = FloatFieldBase(parent)
		self.setGeometry(kwargs.get("geo", QRect(0,0,10,10)))
		self.setTags(kwargs.get("tags", []))
		self.objectType = 'float_field'
		self.target_attr = ""
		self.tooltip = ""

 # create the underlying Qt widget
		self.setup() # apply the settings
		self.show()
		self.widget.focused.connect(self.onFocused)

	def onFocused(self):
		self.focused.emit()

	def serialize(self):
		return {
			"float_field": {
				"cid": self.cid,
				"target_attr": self.target_attr,
				"tags": self.getTags(),
				"tooltip": self.tooltip,
				"geo": self.geometry(),
				"stylesheet": self.stylesheet,
				"name": self.objectName()
			}
		}

	def deserialize(self, json, duplicate=False, client=False):
		if not duplicate:
			self.cid = json["cid"]

		self.setGeometry(json["geo"], client=client)
		self.target_attr = json["target_attr"]
		self.setTags(json["tags"])
		self.tooltip = json["tooltip"]
		self.stylesheet = json["stylesheet"]
		self.setObjectName(json.get("name", ""))
		self.setup()

	def setup(self, client=False):
		self.setStyleSheet(self.stylesheet)
		if client: # if loaded by CUI Viewer
			self.widget.setToolTip(self.tooltip) # display the tooltip
			self.widget.valueChanged.connect(self.valueChangedAction)
		else:
			self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

	def valueChangedAction(self):
		val = self.widget.value() # convert value to float
		SoftwarePlugin.setAttr(self.target_attr, val) # set new value to attribute

	def updateControl(self):
		try:
			val = SoftwarePlugin.getAttr(self.target_attr) # get the attribute value
		except Exception: # abort if attribute unreachable
			return

		self.widget.setValue(val) # display new value
