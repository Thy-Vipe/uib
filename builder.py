from PySide.QtCore import *
from PySide.QtGui import *
from utils import *
import utils as tools
import sys, os, shutil, json
import widgets as uit
from popupMenu import PopupMenu
from builderOpt import BuilderOptions
from itemOptionsWid import itemOptionsWidget
from itemAttrsUi import ItemAttrsDial
from commandEditor import CommandEditor
from ctypes import windll, Structure
# import maya.cmds as cmds
# import pymel.core as pm
cmds = None
pm = None
import consoleTool

CLASSES_ENUM = {
	"label":uit.Label,
	"command_button":uit.CommandButton,
	"selector":uit.Selector,
	"checkbox":uit.CheckBox,
	"line_edit":uit.LineEdit,
	"text_edit":uit.TextEdit,
	"slider":uit.Slider,
	"frame":uit.Frame,
	"float_field":uit.FloatField
}

DEFAULT_STARTUP_SCRIPT = """def atStartup():
	pass
	#Only the code inside atStartup() will be executed.
"""
class userValueHolder:
	def __init__(self):
		self.container = {}

	def set(self, name, value):
		self.container[name] = value

	def get(self, name):
		return self.container[name]

	def values(self):
		return self.container.values()

	def keys(self):
		return self.container.keys()

class textHandle(object):
	def __init__(self, text=None):
		self._text = ""
		if text: self._text = text
	def setText(self, text):
		self._text = text

	def text(self): return self._text
"""
This Class acts like any widget (functions are for the most part similar to widget's BaseControl, their Base class... But contains the other widgets, allowing them to
be translated, scaled, resized, strecthed, ripped...Oh wait.. That's going too far..Allowing to edit objects as a group, all at once.
They can -or not- be parented to the GUI. They're not "virtually" here (well, they are.. But...) Let's say that's the Group acts like a constrain on the other
widgets. If it moves, its content do so.
## Warning: As it is right now, it only works properly if widget's Basecontrol is used with the items put in the group. ##
"""
class Group(QObject):
	def __init__(self, content, geo=None, duplicate=False):
		super(Group, self).__init__()
		self.cid = -1 #identifier for temporary instance.
		self._content = content
		self.contentOffsets = [None for i in range(len(self._content))]
		self._groupOrigin = None
		self._lastOrigin = None
		self.__geometry = geo if geo else getHIB(self._content)
		self.duplicate = duplicate
		self._frame = None
		self._contourPoints = None
		self._contour = None
		self._parameters = []
		self.contour()
		for item in self._content:
			self._parameters.append(getParameters(item.geometry(), self.geometry(), 0,3))

	def move(self, pos):
		if self._groupOrigin is None: return
		for item, i in zip(self._content, range(len(self._content))):
			if self.contentOffsets[i] is None or self._lastOrigin != self._groupOrigin: self.contentOffsets[i] = pos - item.geometry().topLeft()
			newPos = pos - self.contentOffsets[i]
			item.move(newPos)
		self._lastOrigin = self._groupOrigin
		self.setGeometry(getHIB(self._content))

	def addItems(self, *items): 
		self._content.extend(items)
		self.__geometry = getHIB(self._content)
		self._parameters = []
		for item in self._content:
			self._parameters.append(getParameters(item.geometry(), self.geometry(), 0,3))

	def delete(self): #This function destroys the Group and its content.
		for item in self._content:
			item.delete()
		if self._frame: self._frame.deleteLater()
		self.deleteLater()
		self = None

	def getInstances(self, instanceType, not_=True):
		output = []
		for obj in self._content:
			if not not_:
				if isinstance(obj, instanceType):
					output.append(obj)
			elif not_:
				if not isinstance(obj, instanceType):
					output.append(obj)
		return output

	def split(self): #This function destroys the Group without deleting its content.
		for item in self._content:
			item.setup()
			item.highlight(k=True)
			
		if self._frame: self._frame.deleteLater()
		self.deleteLater()
		self = None

	def display(self, parent): #This function draws a rubberband showing the group's geometry. Requires a parent area (for instance, the parent of the objects, or a  similar layer.) 
		self._frame = uit.RubberBand(parent, color="frame", geo=self.__geometry)
		self._frame.show()

	def setOrigin(self, orig): self._groupOrigin = orig
	def origin(self): return self._groupOrigin 
	def geometry(self): return QRect(*self.__geometry.getRect())
	def setGeometry(self, geometry): 
		self.__geometry = geometry
		if self._frame: self._frame.setGeometry(geometry)
		self.contour()
		for item in self._content:
			self._parameters.append(getParameters(item.geometry(), self.geometry(), 0,3))		

	def content(self): return self._content

	def contour(self, size=(8,8)): # Generates a hitbox for each side and corner of the Group's QRect.
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
			side = uit.Identifier(ids[n], p1, lenght)
			self._contour.append(side)
			n += 1

	def adjust(self, *xywh):
		"""
		Parameters-based rescaling/adjusting function. The parameters are defined when the group is created or its content modified, using the function <getParameters> from utils. 
		The group content's relative coordinates are defined by float parameters used to place the objects inside the group, relative to the group's top left corner.
		This allows keeping the same relative position and scale for each object according to the group they're in. 
		"""
		groupGeoAdj = self.geometry()
		groupGeoAdj.adjust(*xywh)
		for item, params in zip(self._content, self._parameters):
			geo = QRect()
			x, y = params[0]
			w, h = params[1]
			geo.setX(groupGeoAdj.x()+groupGeoAdj.width()*x)
			geo.setY(groupGeoAdj.y()+groupGeoAdj.height()*y)
			geo.setWidth(groupGeoAdj.width()*(w-x)+1)
			geo.setHeight(groupGeoAdj.height()*(h-y)+1)
			item.setGeometry(geo)

		self.setGeometry(groupGeoAdj)

	def getContours(self): return (self._contour, ['U','V', 'U', 'V'])
	def getContoursPoints(self): return self._contourPoints


"""
The building Layout Class. Allows creating everything interactively for the Ui project. Only used for building/editing. The reader Class offers a few less functions, as its content
is set to readOnly.
"""
class Layout(QWidget):
	keyPressed = Signal(QEvent)
	attrsDialogCalled = Signal()
	def __init__(self, parent, lineLayer):
		super(Layout, self).__init__(parent)
		self.setFocusPolicy(Qt.StrongFocus)
		self.parent = parent
		self.UVLinesLayer = lineLayer
		self.setMouseTracking(True)
		self.selectionRect = None
		self.selectedItems = []
		self.dragOrigin = None
		self.sideIndex = [0, None]
		self.lmouseBtnClicked = False
		self.rmouseBtnClicked = False
		self.userEditingItem = False
		self.userEditing = False
		self.duplicateMode = False
		self.moveMode = False
		self.is_raised = False
		self.sideEdited = False
		self.debug = False # May be caused by latency. 
		self.objectsMenu = None
		self.optionsMenu = None
		self.itemOptionsWid = None
		self.ULine = [None, None]
		self.VLine = [None, None]
		self.objectsMen = (uit.Label, uit.CommandButton, uit.Selector, uit.CheckBox, uit.LineEdit, uit.TextEdit, uit.Slider, uit.Frame, uit.FloatField, self.killWidgs, self.applyItem)
		self.commands = [self.moveWidget, self.initEditorsAtItem, self.duplicateWidget, self.deleteWidget, self.duplicateWidgets, self.setOnTop, self.setOnBottom]
		self.currentItem = None
		self.currentCID = -1
		self.editedItemCID = -1
		self.clickOffset = None
		self.pointerPos = None
		self.pointerGlobalPos = None
		self.editedObjectLastAttrs = None

	def nextCid(self):
		self.currentCID += 1
		return self.currentCID

	def keyPressEvent(self, event):
		self.keyPressed.emit(event)

	def mousePressEvent(self, event):
		"""
		Gesture function for mouse press events. Draws a selection rectangle, or a layout for an item, depending of which button is clicked.
		left will create layout while right would create selection. They're defined by their colors anyways. Red for selection. Blue for Layout. 
		Everything is pretty straight forward, no need to explain each "if" in depth. 
		When the layout receives a click, it automatically receives Focus too. dragOrigin is defined by this click, and conserved for dragging until click release.
		"""
		self.setFocus()
		self.dragOrigin = event.pos()
		if not isinstance(self.currentItem, Group):
			if event.button() == Qt.LeftButton:
				self.lmouseBtnClicked = True
				self.rmouseBtnClicked = False
				self.pointerGlobalPos = event.globalPos()
				if not self.userEditing and not self.duplicateMode and not self.moveMode and not self.userEditingItem:
					self.initRubberBand(pos=event.pos())

			elif event.button() == Qt.RightButton:
				self.rmouseBtnClicked = True
				self.lmouseBtnClicked = False
				self.pointerGlobalPos = event.globalPos()
				if self.objectsMenu is None and not self.duplicateMode and not self.moveMode:
					self.killWidgs()
					self.initRubberBand(pos=event.pos(), target=self.parent, color="red")
		else:
			if event.button() == Qt.LeftButton:
				self.lmouseBtnClicked = True
				self.rmouseBtnClicked = False
				self.currentItem.setOrigin(event.pos())
			elif event.button() == Qt.RightButton:
				self.rmouseBtnClicked = True
				self.lmouseBtnClicked = False

	def mouseMoveEvent(self, event):
		"""
		Gesture function for mouse move events. Whenever the mouse Pointer is hovered on the surface of the Layout: the tracking is enabled. Allows updating the pointer and/or catch
		any object possibly laying under. 
		"""
		self.pointerPos = event.pos() 
		if not self.hasFocus(): self.setFocus()
		if self.userEditingItem and not self.rmouseBtnClicked:
			self.interactiveAdjustingManager()
			return

		if not isinstance(self.currentItem, Group):
			if not self.duplicateMode and not self.moveMode:
				self.interactiveCreationManager()
			elif self.duplicateMode or self.moveMode:
				geo = self.currentItem.geometry()
				if self.clickOffset is None: self.clickOffset = self.pointerPos - geo.topLeft()
				recPos = self.pointerPos - self.clickOffset
				self.currentItem.move(recPos)
				self.selectionRect.move(recPos)
				self.getUVLines()
		else:
			if isinstance(self.currentItem, Group):
				self.interactiveAdjustingManager()
			else:
				if self.optionsMenu:
					if not self.currentItem.geometry().contains(self.pointerPos):
						self.optionsMenu.deleteLater()
						self.optionsMenu = None

	def interactiveAdjustingManager(self):
		"""
		Management function for any interactive adjusting done on the Layout, while editing an object or a group of objects. 
		At first, it tries to catch if the mouse's pointer lays above the hitbox of an object (defined by its 4 sides). If it does, then the cursor is updated to the
		corresponding direction. i.e: user has the mouse on the top side of the widget, the function sets the cursor to a <vertical arrow> cursor.
		And if not, then the cursor's either on the widget's surface, or out of it. If it's on, show a "all directions arrow" as cursor, showing that the widget can be translated
		anywhere else. Otherwise, do nothing.

		The hitbox is defined by the four sides, and the widget's corners are not literally written in the code, they are calculated and defined by values obtained with a side to the
		power of its lateral and intersecting one. Each side as an integer value: 1 for top, 2 for left, 3 for bottom, 4 for right, so having the mouse cursor on the top-left corner
		would mean it's located at the intersection of 1 and 2, hence 2^1 = 2. Same applies for the other corners with their own values.
		2 > top left
		9 > bottom left
		64 > bottom right
		4 > top right

		The ~ref~ dic refers to the type of cursor to use for each corner, along with which index of a list containing [x,y,w,h] to modify with the mouse's offsets.
		The ~ids~ is a simple reference for every lateral side. ids[n] is lateral and intersecting ids[n+2], hence the six values.
		"""
		if not self.lmouseBtnClicked:
			self.sideIndex[0] = 0
			ids = ["topSide", "leftSide", "bottomSide", "rightSide", "topSide", "leftSide"]
			ref = {"2":[(0,1),Qt.SizeFDiagCursor],"9":[(0,3),Qt.SizeBDiagCursor],"4":[(2,1),Qt.SizeBDiagCursor],"64":[(2,3),Qt.SizeFDiagCursor]}
			sides, directions = self.currentItem.getContours()
			self.stop = False
			for side, direction in zip(sides, directions):
				if side.contains(self.pointerPos) and not self.stop:
					p = ids.index(side.getIdentity())
					elss = (p+2)%4
					lss = []
					for o, i in zip(sides, range(len(sides))):
						if i not in (elss, p): lss.append(o) # if ~side index~ isn't the "parent" side and isn't the opposite either, add the two others as lateral sides.
						else: pass
					for lateralSide in lss:
						# This part of the function tries to find the corners.
						# If not.. Then the cursor is on one of the sides, so the program shifts to the sides and do the same. 
						if lateralSide.contains(self.pointerPos):
							identity = ids.index(lateralSide.getIdentity())
							corner = str((identity+1)**(p+1))
							self.stop = True
							break
					else:		
						if direction == "U": QApplication.setOverrideCursor(Qt.SizeVerCursor)
						elif direction == "V": QApplication.setOverrideCursor(Qt.SizeHorCursor)
						self.sideIndex[1] = direction
						break

				elif self.stop:
					cornerId = ref[corner]
					self.sideIndex[0], self.sideIndex[1] = cornerId[0]
					QApplication.setOverrideCursor(cornerId[1])
				elif not self.stop and not self.lmouseBtnClicked:
					if self.currentItem.geometry().contains(self.pointerPos):
						QApplication.setOverrideCursor(Qt.SizeAllCursor)
						self.sideIndex[0] = 10 #identifier for movement.
						break
					else: 
						QApplication.restoreOverrideCursor()
						self.sideIndex[0] += 1

		elif self.lmouseBtnClicked and self.sideIndex[0] < 4:
			offset = QSize(self.pointerPos.x()-self.dragOrigin.x(), self.pointerPos.y()-self.dragOrigin.y())
			n = self.sideIndex[0]
			direction = self.sideIndex[1]
			currentGeometry = self.currentItem.geometry()
			xywh = [0,0,0,0]
			if self.clickOffset is None: self.clickOffset = QSize(0,0)
			if isinstance(direction, str):
				if direction == "U":
					if n == 0: xywh[1] = offset.height() - self.clickOffset.height()
					else: xywh[3] = offset.height() - self.clickOffset.height() 
				elif direction == "V":
					if n == 1: xywh[0] = offset.width() - self.clickOffset.width()
					else: xywh[2] = offset.width() - self.clickOffset.width() 
			else:
				xywh[n] = offset.width() - self.clickOffset.width()
				xywh[direction] = offset.height() - self.clickOffset.height()  
			
			if not isinstance(self.currentItem, Group):
				currentGeometry.adjust(*xywh)
				self.currentItem.setGeometry(currentGeometry)
				self.selectionRect.setGeometry(currentGeometry)
				self.itemOptionsWid.updateValues(geo=currentGeometry)
			else:
				self.currentItem.adjust(*xywh)

			self.clickOffset = offset
			self.sideEdited = True	
			self.stop = False	

		elif self.lmouseBtnClicked and self.sideIndex[0] == 10:
			geo = self.currentItem.geometry()
			if self.clickOffset is None: self.clickOffset = self.pointerPos - geo.topLeft()
			recPos = self.pointerPos - self.clickOffset
			self.currentItem.move(recPos)
			if self.selectionRect: self.selectionRect.move(recPos)
			self.getUVLines()
			self.sideEdited = False	
			self.stop = False		

	def interactiveCreationManager(self):
		"""
		Function manages objects creation and editing on the viewport. 
		Shows up a menu if a widget's right-clicked, to offer a few options to the user, as in editing, set to top, bottom, move, etc...
		This function also handles the drawing of the widget's layout when the user first clicks-drag on the viewport. 
		The selectionRect is the blue rectangle that appears after dragging. It's the Layout for any widget. 
		User editing is True when the user is editing the object (right clikc on widger-> edit...)
		itemOptionsWid are the settings for the given widget. 
		optionsMenu is the widget that appears to create any item in the defined layout.
		objectsMenu is the menu that pops up when right clicking on the widget. 
		"""
		if self.selectionRect and self.lmouseBtnClicked and not self.userEditing:
			geo = QRect(*calculateCorners(self.dragOrigin,self.pointerPos))
			self.selectionRect.setGeometry(geo)

		if self.selectionRect and self.rmouseBtnClicked and self.itemOptionsWid is None:
			geo = self.selectionRect.geometry()
			if self.objectsMenu:
				if geo.contains(self.pointerPos) and not self.objectsMenu.getAbstractRect().contains(self.pointerPos):
					if self.clickOffset is None: self.clickOffset = self.pointerPos - geo.topLeft()
					recPos = self.pointerPos - self.clickOffset
					self.selectionRect.move(recPos)
			else:
				geo = QRect(*calculateCorners(self.dragOrigin,self.pointerPos))
				self.selectionRect.setGeometry(geo)					

		if self.objectsMenu and self.rmouseBtnClicked:
			if self.objectsMenu.getAbstractRect().contains(self.pointerPos) or self.debug:
				self.debug = True
				if self.clickOffset is None: self.clickOffset = self.pointerPos - self.objectsMenu.getRect().topLeft()
				recPos = self.pointerPos - self.clickOffset
				self.objectsMenu.move(recPos)

		elif self.optionsMenu:
			item = self.parent.items[self.editedItemCID]
			if not item.hitbox().contains(self.pointerPos) and not self.optionsMenu.getAbstractRect().contains(self.pointerPos):
				self.optionsMenu.deleteLater()
				self.optionsMenu = None

	def mouseReleaseEvent(self, event):
		"""
		This function closes the possible active actions, when mouse is released.
		It also validates them most of the time. For instance after a "move" action, the defining of a new Layout/group. 
		"""
		self.clickOffset = None
		QApplication.restoreOverrideCursor()

		if self.currentItem:
			if self.sideEdited and not isinstance(self.currentItem, Group):
				if self.objectsMenu.geometry().intersects(self.currentItem.geometry()):
					self.objectsMenu.move(QPoint(self.currentItem.geometry().topRight().x()+35, self.pointerPos.y()-75))
				self.sideEdited = False
				self.lmouseBtnClicked = False
				self.rmouseBtnClicked = False
				return
			elif self.sideEdited and isinstance(self.currentItem, Group):
				self.sideEdited = False
				self.lmouseBtnClicked = False	
				return		

		if not isinstance(self.currentItem, Group):
			if not self.duplicateMode and not self.moveMode:
				if self.selectionRect and self.lmouseBtnClicked and not self.userEditing and not self.userEditingItem:
					area = self.selectionRect.geometry()
					self.lmouseBtnClicked = False
					surface = calculateSurface(area.width(), area.height())
					if surface >= 450:
						self.initObjectsMenu(area)

					else:
						self.selectionRect.delete()
						if surface >= 4 : print "Area too small."	
						return
					if not self.currentItem: self.userEditing = True
				elif self.rmouseBtnClicked:
					self.rmouseBtnClicked = False
					self.debug = False

					if self.selectionRect and not self.objectsMenu:
						area = self.selectionRect.geometry()
						if calculateSurface(area.width(), area.height()) <= 6: 
							if self.initOptionsMenu(event.pos()): 
								self.selectionRect.delete()
								return

						self.selectedItems = []
						for item in self.parent.items:
							if area.contains(item.geometry().topLeft()) and area.contains(item.geometry().bottomRight()):
								self.selectedItems.append(item)
								item.highlight(parent=self.UVLinesLayer, color="green-no_bg")
						if len(self.selectedItems) != 0:
							self.currentItem = Group(self.selectedItems, geo=getHIB(self.selectedItems))
							self.currentItem.display(self.UVLinesLayer)
						
						self.selectionRect.delete()

				elif self.lmouseBtnClicked and self.currentItem:
					self.sideEdited = True
					self.mouseReleaseEvent(event)

			elif self.duplicateMode and self.lmouseBtnClicked: 
				self.duplicateMode = False
				self.lmouseBtnClicked = False
				self.currentItem.cid = self.nextCid()
				self.currentItem.setup()
				self.parent.items.append(self.currentItem)
				self.currentItem = None
				self.selectionRect.delete()
				self.deleteLines()

			elif self.moveMode and self.lmouseBtnClicked:
				self.moveMode = False
				self.currentItem = None
				self.lmouseBtnClicked = False
				self.selectionRect.delete()
				self.deleteLines()

		else:
			if self.lmouseBtnClicked:
				self.lmouseBtnClicked = False
			elif self.rmouseBtnClicked:
				if self.currentItem.geometry().contains(self.pointerPos):
					self.initOptionsMenu(self.pointerPos)
				else:
					if self.currentItem.duplicate:
						objects = self.currentItem.getInstances(uit.RubberBand, not_=True)
						for obj in objects:
							obj.cid = self.nextCid()
							self.parent.items.append(obj)

					self.currentItem.split()
					self.currentItem = None
					self.rmouseBtnClicked = False

	def buildItem(self, index):
		"""
		This is what creates/replaces an item in a given Layout according to user's request. 
		"""
		if self.currentItem and not index == 10: #index = 10 means the user clicked the "accept" button. Deleting their work would be bad.
			oldItemCid = self.currentItem.cid 	 #This loop basically kills any instance that was NOT saved onto the main Ui. 
			self.currentItem.delete()
			self.currentItem = None
		else:
			oldItemCid = None

		self.initItemOptionsWid()

		self.currentItem = self.objectsMen[index](self.parent)
		if self.currentItem is not None:
			self.is_raised = False
			if isinstance(self.currentItem, self.objectsMen[2]): #If current instance is a Selector.
				self.itemOptionsWid.wLabel.setText('Radius:')
				self.itemOptionsWid.hLabel.hide()
				self.itemOptionsWid.hSB.hide()	


			self.currentItem.setGeometry(self.selectionRect.geometry())
			if isinstance(self.currentItem, self.objectsMen[6]): #If current instance is a Slider. 
				orient = Qt.Horizontal if guessOrient(self.selectionRect.width(), self.selectionRect.height()) else Qt.Vertical
				self.currentItem.widget.setOrientation(orient)
			self.currentItem.show()
			self.currentItem.setObjectName(randomObjName())
			self.itemOptionsWid.updateValues(geo=self.currentItem.geometry())

		if self.userEditingItem:
			self.deleteLines()
			self.currentItem.cid = oldItemCid
			self.parent.items[oldItemCid] = self.currentItem

	def applyItem(self, x=None):
		"""
		Saves the instance onto the Main Ui. Allowing self.currentItem to be cleared (this value is ONLY for temporary instances).
		"""
		if self.currentItem is None: 
			print "No item chosen!"
			return
		if not self.userEditingItem:	
			self.currentItem.cid = self.nextCid()
			self.currentItem.setup()
			self.parent.items.append(self.currentItem)
		else: self.userEditingItem = False

		self.currentItem = None
		self.userEditing = False
		self.killWidgs(False)
		self.raise_()
		self.is_raised = True
		self.deleteLines()

		return

	def killWidgs(self, x=None):
		"""
		Clears the building Layout of any active widgets that are temporary, for Ui clean-up.
		"""
		self.userEditing = False
		self.deleteLines()
		if self.selectionRect:
			self.selectionRect.delete()
		if self.itemOptionsWid:
			self.itemOptionsWid.deleteLater()
			self.itemOptionsWid = None
		if self.objectsMenu:
			self.objectsMenu.deleteLater()
			self.objectsMenu = None
		if self.currentItem and x != False and not self.userEditingItem:
			self.currentItem.delete()
			self.currentItem = None
		else: self.userEditingItem = False

		return

	def duplicateWidget(self):
		"""
		One likes to duplicate unique objects... Copies an instance's settings into an other one of the same type, with a new CID.
		"""
		target = self.parent.items[self.editedItemCID]
		targetAttributes = target.serialize()
		targetType = targetAttributes.keys()[0]
		attributes = targetAttributes[targetType]
		self.currentItem = CLASSES_ENUM[targetType](self.parent)
		self.raise_()
		self.currentItem.deserialize(attributes, duplicate=True)
		self.currentItem.setObjectName(randomObjName())
		self.initRubberBand(item=self.currentItem, withMouse=False, target=self.parent)
		clickOrig = self.pointerGlobalPos
		windll.user32.SetCursorPos(clickOrig.x(), clickOrig.y())
		self.duplicateMode = True
		

	def duplicateWidgets(self):
		"""
		But one may also like duplicating multiple objects... Works like the function above, but made to manage a Group. 
		"""
		targets = []
		for obj in self.currentItem.content():
			if isinstance(obj, uit.RubberBand): obj.hide()
			else: targets.append(obj)

		geo = self.currentItem.geometry()
		self.currentItem.split()
		self.selectedItems = []
		for target in targets:
			targetAttributes = target.serialize()
			targetType = targetAttributes.keys()[0]
			attributes = targetAttributes[targetType]
			newWidget = CLASSES_ENUM[targetType](self.parent)
			self.raise_()
			newWidget.deserialize(attributes, duplicate=True)
			newWidget.setObjectName(randomObjName())	
			newWidget.highlight(parent=self.parent)
			self.selectedItems.append(newWidget)

		newContent = self.selectedItems
		self.currentItem = Group(newContent, geo=geo, duplicate=True)
		self.currentItem.display(self.UVLinesLayer)

	def moveWidget(self):
		"""
		Allows transating a widget. The item's snapped onto the mouse's cursor until the user left-clicks.
		"""
		self.currentItem = self.parent.items[self.editedItemCID]
		self.initRubberBand(item=self.currentItem, withMouse=False, target=self.parent)
		clickOrig = self.pointerGlobalPos
		windll.user32.SetCursorPos(clickOrig.x(), clickOrig.y())
		self.moveMode = True

	def clearHighlights(self):
		"""
		Clears all active highlights from saved items, skipping the locked ones (locked highlights show errors, and must be fixed to be unlocked.)
		...Or through the Console.. But that's cheating! And I ain't gonna tell how to do it.. Even if it's easy... >.>
		"""
		for item in self.selectedItems:
			item.highlight(k=True)

	def deleteWidget(self):
		"""
		Deletes a given widget or a Group of widgets.
		"""
		if not isinstance(self.currentItem, Group):
			self.parent.items[self.editedItemCID].delete()
			self.parent.items.pop(self.editedItemCID)
			self.currentCID = rebuildCIDs(self.parent.items) #Check utils file.
		else:
			targets = self.currentItem.content()
			self.currentItem.delete()
			for target in targets:
				if not isinstance(target, uit.RubberBand):
					self.parent.items[target.cid].delete()
					self.parent.items.pop(target.cid)
					self.currentCID = rebuildCIDs(self.parent.items)
			self.currentItem = None

	def updateItem(self, **values):
		"""
		updates the item according to the GUI settings visible for the item being currently edited.
		"""
		geo = QRect(values['posX'],values['posY'],values['width'],values['height'])
		if self.selectionRect: self.selectionRect.setGeometry(geo)
		self.currentItem.setGeometry(geo)
		if not isinstance(self.currentItem, self.objectsMen[5:9]): self.currentItem.setText(values['name'])
		self.currentItem.setTags(values['tags'], asStr=True)

		self.getUVLines()

	def initRubberBand(self, **kwargs):
		"""
		Inits a click-n-drag rectangle. To show Widget Layouts (blue) and Group containers (red).
		"""
		query = kwargs.get("q", False)

		if self.selectionRect and not query:
			self.selectionRect.delete()

		withMouse = kwargs.get("withMouse", True)
		color = kwargs.get('color', 'blue')
		target = kwargs.get("target", self)	
		if withMouse:
			pos = kwargs["pos"]
			rec = uit.RubberBand(target, color=color) 
			self.dragOrigin = pos
			rec.setGeometry(QRect(self.dragOrigin, QSize()))
			rec.show()
		else:
			item = kwargs.get("item", None)
			if item: geo = item.geometry() 
			else: raise TypeError("Missing arg: item")
			rec = uit.RubberBand(target, color=color)
			rec.setGeometry(geo)
			rec.show()		
			rec.lower()

		if query: return rec
		else: self.selectionRect = rec

	def initObjectsMenu(self, area):
		"""
		Inits a popup menu allowing to create any new widget in the current Widget Layout.
		PopupMenu class is available in popupMenu.py .
		"""
		if self.objectsMenu:
			self.objectsMenu.deleteLater()
			self.objectsMenu = None

		pos = area.topRight()
		pos.setX(pos.x()+35)
		self.objectsMenu = PopupMenu(self, pos, abstractOffset=(20,20))
		self.objectsMenu.initButtons(['Label', 'Button', 'Selector', 'Checkbox', 'Line Edit', 'Text Field', 'Slider', 'Frame', 'Float Field', 'Cancel', 'Accept'], btnDim=(75,20))
		self.objectsMenu.btnClicked.connect(self.buildItem)		

	def initItemOptionsWid(self):
		"""
		Inits and parents the option widget to the item's objectsMenu instance. itemOptionsWidget class is available in itemOptionsWid.py .
		"""
		if self.itemOptionsWid:
			self.objectsMenu.killChildren()
			self.itemOptionsWidget = None

		self.itemOptionsWid = itemOptionsWidget(self, self.objectsMenu.getRect().topRight())
		self.objectsMenu.setChildren(self.itemOptionsWid)
		self.itemOptionsWid.output.connect(self.unpackArgs)
		self.itemOptionsWid.attrsEditBtn.clicked.connect(self.initAttrsDialogMsg)

	def initAttrsDialogMsg(self): self.attrsDialogCalled.emit()

	def initOptionsMenu(self, pos):
		"""
		Inits the option menu to move, edit, duplicate, and modify an existing instance.
		It appears when the cursor's hovering a widget as the user right-clicks, and disapears if it gets out of the widget's & menu area.
		Also killed after being clicked on one of its buttons. 
		"""
		self.editedItemCID = -1
		if self.optionsMenu:
			self.optionsMenu.deleteLater()
			self.optionsMenu = None

		if not isinstance(self.currentItem, Group):
			objects = list(tuple(self.parent.items))
			objects.reverse()
			for item in objects:
				if item.hitbox().contains(pos):
					print item.cid, item 
					self.editedItemCID = item.cid
					self.optionsMenu = PopupMenu(self, pos, abstractOffset=(15,15))
					self.optionsMenu.initButtons(['Move', 'Edit...', 'Duplicate', 'To top', 'To bottom', 'Delete'], btnDim=(75,23), ids=[0,1,2,5,6,3])
					self.optionsMenu.btnReleased.connect(self.optionsMenuCommands)
					break

		else:
			self.optionsMenu = PopupMenu(self, pos, abstractOffset=(15,15))
			self.optionsMenu.initButtons(['Duplicate', 'Delete'], ids=[4,3], btnDim=(75,23))
			self.optionsMenu.btnReleased.connect(self.optionsMenuCommands)

		if self.optionsMenu is None: return False # Indicates if menu was created.
		else: return True

	def optionsMenuCommands(self, index):
		"""
		Link function to the optionsMenu's Buttons. Each buttons has an index that refers to a function hold in self.commands
		"""
		self.commands[index]()
		self.optionsMenu.deleteLater()
		self.optionsMenu = None

	def setOnTop(self): 
		"""
		Places a widget on top of the others.
		"""
		self.parent.items[self.editedItemCID].raise_()
		x = self.parent.items.pop(self.editedItemCID)
		self.parent.items.append(x)
		self.currentCID = rebuildCIDs(self.parent.items)
		self.raise_()
	def setOnBottom(self): 
		"""
		Places a widget under the others.
		"""
		self.parent.items[self.editedItemCID].lower()
		x = self.parent.items.pop(self.editedItemCID)
		self.parent.items.insert(0, x)
		self.currentCID = rebuildCIDs(self.parent.items)
		self.raise_()

	def initEditorsAtItem(self):
		"""
		This function is called when the user wants to edit an existing object. 
		"""
		self.userEditingItem = True
		item = self.parent.items[self.editedItemCID]
		self.initObjectsMenu(item.hitbox())
		self.initItemOptionsWid()
		self.currentItem = item
		self.itemOptionsWid.updateValues(**self.currentItem.serialize()[self.currentItem.objectType])
		self.initRubberBand(item=item, withMouse=False, target=self.UVLinesLayer, color="blue-no_bg")
		self.setFocus()

	def getUVLines(self):
		"""
		Draws U&V lines on the layout, to show alignments with other objects.
		"""
		if isinstance(self.currentItem, Group): skip = tuple(self.currentItem.getInstances(uit.RubberBand)) #Query group's content without its Rubberbands.
		else: skip = None 
		UVLinesParams = getAlign(tuple(self.parent.items), self.currentItem, skipped=skip)
		if UVLinesParams is not None:
			if UVLinesParams[0][0]: self.drawULine(UVLinesParams[0][1], UVLinesParams[4][0], 0)
			else: self.deleteLines(0)
			if UVLinesParams[2][0]: self.drawULine(UVLinesParams[2][1], UVLinesParams[4][1], 1)
			else: self.deleteLines(1)
			if UVLinesParams[1][0]: self.drawVLine(UVLinesParams[1][1], UVLinesParams[4][2], 0)
			else: self.deleteLines(2)
			if UVLinesParams[3][0]: self.drawVLine(UVLinesParams[3][1], UVLinesParams[4][3], 1)
			else: self.deleteLines(3)

	def drawULine(self, l, e, n):
		"""
		Creates a Line axed on X (U)
		"""
		if self.ULine[n]: 
			self.ULine[n].deleteLater()
			self.ULine[n] = None

		self.ULine[n] = uit.UVLine(self.UVLinesLayer, QPoint(0, l), self.parent.width()*2, 3)
		if e: self.ULine[n].highlight()
		self.ULine[n].lower()
			
	def drawVLine(self, l, e, n):
		"""
		Creates a Line axed on Y (V)
		"""
		if self.VLine[n]:
			self.VLine[n].deleteLater()
			self.VLine[n] = None

		self.VLine[n] = uit.UVLine(self.UVLinesLayer, QPoint(l, 0), 3, self.parent.height()*2)
		if e: self.VLine[n].highlight()
		self.VLine[n].lower()

	def deleteLines(self, l=4):
		"""
		Destroys all/specific alignments lines.
		"""
		if self.ULine[0] and (l == 4 or l == 0):
			self.ULine[0].deleteLater()
			self.ULine[0] = None	
		if self.ULine[1] and (l == 4 or l == 1):
			self.ULine[1].deleteLater()
			self.ULine[1] = None	

		if self.VLine[0] and (l == 4 or l == 2): 
			self.VLine[0].deleteLater()
			self.VLine[0] = None
		if self.VLine[1] and (l == 4 or l == 3): 
			self.VLine[1].deleteLater()
			self.VLine[1] = None

	def unpackArgs(self, args): self.updateItem(**args)

	def raise_(self):
		"""
		Puts the building area on top of the rest for everything above this function to work properly.
		"""
		self.UVLinesLayer.raise_()
		super(Layout, self).raise_()
		self.is_raised = True

	def lower(self):
		"""
		Puts the building area behind the rest to allow access to created widgets (they're basically covered by an 
		invisible layer -This Class, Layout- allowing all editings).
		"""
		super(Layout, self).lower()
		self.UVLinesLayer.lower()
		self.is_raised = False


"""
Similar to the Layout class, but does NOT allow editing the objects. 
"""
class ViewLayout(QWidget):
	def __init__(self, parent):
		super(ViewLayout, self).__init__()
		self.setFocusPolicy(Qt.StrongFocus)
		self.filePath = None
		self.setMouseTracking(True)
		self.parent = parent
		self.dragOrigin = None
		self.clickOffset = None
		self.pointerPos = None
		self.selectionRect = None
		self.selectedItems = []
		self.rmouseBtnClicked = False
		self.lmouseBtnClicked = False
		self.background = None
		self.niceName = ""
		self.startupScript = textHandle(DEFAULT_STARTUP_SCRIPT)
		self.startupCommand = None
		self.content = []
		self.symbols = {
			"uib": self,
			"cmds": cmds,
			"pm": pm,
			"os": os,
			"sys": sys,
			"uit": uit,
			"tools": tools
		}
		self.w = 0
		self.h = 0

	def resize(self, *args):
		super(ViewLayout, self).resize(*args)
		self.w = self.geometry().width()
		self.h = self.geometry().height()

	def mousePressEvent(self, event):
		self.dragOrigin = event.pos()
		if event.button() == Qt.RightButton:
			self.rmouseBtnClicked = True
			self.lmouseBtnClicked = False
		elif event.button() == Qt.LeftButton:
			self.selectionRect = uit.RubberBand(self)
			self.selectionRect.show()
			self.rmouseBtnClicked = False
			self.lmouseBtnClicked = True

	def mouseMoveEvent(self, event):
		self.pointerPos = event.pos()
		if self.lmouseBtnClicked:
			geo = QRect(*calculateCorners(self.dragOrigin,self.pointerPos))
			self.selectionRect.setGeometry(geo)		

	def mouseReleaseEvent(self, event):
		if self.lmouseBtnClicked:
			area = self.selectionRect.geometry()
			self.selectedItems = []
			for item in self.content:
				if area.contains(item.geometry()) and item.isSelectable:
					item.highlight(color="blue-no_bg")
					self.selectedItems.append(item)

			self.selectionRect.delete()

		self.rmouseBtnClicked = False
		self.lmouseBtnClicked = False

	def clearHighlights(self):
		for item in self.content:
			item.highlight(k=True)

	def updateBackground(self):
		if self.background is None: # abort if has not BG
			return
		# set the BG using a stylesheet
		self.setStyleSheet("CUILayoutWidget {background-image: url(%s); background-repeat: none;}" % self.background)

	def addItem(self, item):
		self.content.append(item)

	def activate(self):
		# try:
		self.startupCommand = compileFunctions(self.startupScript.text(), ["atStartup"], self.symbols)[0]
		self.startupCommand()
		# except:
			# raise RuntimeError("Couldn't init startup script, please check code and try again.")
"""
User interface to build, edit, test and save Ui 'designs' and functions.
"""
class UIBWindow(QMainWindow):
	def __init__(self, parent=None, mode=0, loadFile=None):
		super(UIBWindow, self).__init__(parent)
		self.parent = parent
		self.setObjectName("UIBMainWindow")
		self.items = []
		self.currentMode = mode #Defines if the window is in viewing mode, or in building mode.
		self.attrsDialog = None
		self.funcDialog = None
		self.background = None
		self.fileNiceName = None
		self.startupScript = textHandle(DEFAULT_STARTUP_SCRIPT)
		self.startupCommand = None
		self.startupCmdEditor = None
		self.lineLayer = None
		self.currentFileData = None
		self.currentFilePath = None
		self.modified = False
		self.userValues = userValueHolder()
		if mode == 0:
			self.lineLayer = QWidget(self)
			self.lineLayer.setGeometry(QRect(0,0,1024,760))
			self.__viewport = Layout(self, self.lineLayer)
			self.__viewport.keyPressed.connect(self.keyPressEvent)
			self.__viewport.attrsDialogCalled.connect(self.initAttrsDialog)
		elif mode == 1:
			self.__viewport = QTabWidget(self)
			self.__viewport.setDocumentMode(True)
			self.__viewport.currentChanged.connect(self.updateUiFromContentGeometry)

		self.__viewport.setGeometry(QRect(0,0,1024,760))
		if mode == 0:
			self.__selfOptions = BuilderOptions(self)
		elif mode == 1:
			self.__selfOptions = None
		self.resize(1024,760)
		self.show()
		self.timer = self.startTimer(250)
		self.symbols = {
			"uib": self,
			"cmds": cmds,
			"pm": pm,
			"os": os,
			"sys": sys,
			"uit": uit,
			"tools": tools
		}

		self.console = consoleTool.ConsoleDialog(self, self.symbols)

		if mode == 1 and not loadFile:
			self.loadUi()
		elif loadFile:
			self.loadUi(load=loadFile)

	def timerEvent(self, event):
		if not self.__viewport.hasFocus():
			if not QApplication.overrideCursor() == None: QApplication.restoreOverrideCursor()

	def keyPressEvent(self, event):
		if self.currentMode == 0:
			if event.key() == Qt.Key_E:
				if self.__viewport.is_raised:
					self.__viewport.lower()
					print "You can now access the objects."
				elif not self.__viewport.is_raised:
					self.__viewport.raise_()
					print "Editor is now set on top. Access to objects is blocked."

			elif event.key() == Qt.Key_X:
				print self.items

	def resizeEvent(self, event):
		self.updateContentGeometry()

	def updateContentGeometry(self):
		self.__viewport.setGeometry(QRect(0,0,self.width(), self.height()))
		if self.lineLayer: 
			self.lineLayer.setGeometry(QRect(0,0,self.width(), self.height()))
		if self.__selfOptions:
			self.__selfOptions.setMaximumSize(self.__selfOptions.width(), self.height())

	def updateUiFromContentGeometry(self):
		if self.__viewport.currentWidget():
			w = self.__viewport.currentWidget().w + 10
			h = self.__viewport.currentWidget().h + 20
			self.setFixedSize(w, h)		

	def moveEvent(self, event):
		if self.__selfOptions:
			if self.__selfOptions.isSnaped():
				pos = self.pos()
				pos.setX(pos.x() - self.__selfOptions.width() - 15)
				self.__selfOptions.move(pos)

	def initAttrsDialog(self):
		if self.attrsDialog:
			self.attrsDialog.deleteLater()
			self.attrsDialog = None

		self.attrsDialog = ItemAttrsDial(self, self.__viewport.currentItem)

	def initStartupCmdDialog(self):
		self.startupCmdEditor = CommandEditor(self, self.startupScript)

	def content(self): return self.items
	def viewport(self): return self.__viewport
	def windowMenu(self): return self.__selfOptions

	def getByTags(self, tags):
		if self.currentMode == 0: items = self.items
		elif self.currentMode == 1: items = self.__viewport.currentWidget().content
		if isinstance(tags, (str,unicode)): tags = convert_to_list(tags)
		matches = []

		for item in items:
			itemTags = item.getTags()
			y = False
			for tag in tags:
				if tag in itemTags:
					y = True
				else:
					y = False
					break
			if y: matches.append(item)
		return matches

	def getByName(self, name):
		if self.currentMode == 0: items = self.items
		elif self.currentMode == 1: items = self.__viewport.currentWidget().content
		output = []
		for item in items:
			if item.objectName() == name:
				output.append(item)

		return output

	def setUiBackground(self):
		result = QFileDialog.getOpenFileName(self, "Open", os.path.dirname(os.path.realpath(__file__)), "Image files (*.png *.jpg)")
		if not result[1]: return

		sourcePath = result[0]
		# localPath = utils.charactersDir()+fileName # format the path to store the BG image

		# try:
		# 	shutil.copyfile(sourcePath, localPath) # copy the BG image to /characters folder of the project
		# except Exception as e:
		# 	pass # if already exists

		self.background = sourcePath # set the BG fileName
		self.updateBackground() # redraw the BG		

	def updateBackground(self):
		if self.background is None:
			self.setStyleSheet("#UIBMainWindow {}")
			return

		imagePath = self.background # get path
		# set the stylesheet
		self.setStyleSheet("#UIBMainWindow {background-image: url(%s); background-repeat: none;}" % imagePath)    

	def saveUi(self):
		if self.fileNiceName is None:
			userInput = QInputDialog.getText(self, "File nice name", "Enter File nice name:")
			if userInput[1]:
				self.fileNiceName = userInput[0]
			else:
				print "You must specify a file name before saving. i.e: This ui is for a 3D character, you can put its name."
				return
		# request fileName to save the layout
		result = QFileDialog.getSaveFileName(self, "Save", os.path.dirname(os.path.realpath(__file__)), "UIB files (*.uib)")
		if result[1]:
			fileName = result[0]
		else:
			return # abort if no file selected

		data = self.getJsonData()

		with open(fileName, "w") as outputFile:
		 	json.dump(data, outputFile)
		self.modified = False
		self.currentFileData = None

	def loadUi(self, load=None):
		# First check if the Ui was modified or the user did put some content already.
		if self.currentMode == 0 and self.currentFileData:
			self.hasSomethingChanged()
			if not self.failSafe(): return
		elif self.currentMode == 0 and len(self.items) > 0 and not self.fileNiceName:
			self.modified = True
			if not self.failSafe(): return

		# If the test is passed, open up the openfilename dialog and do the rest. 
		if load is None:
			result = QFileDialog.getOpenFileName(self, "Open", os.path.dirname(os.path.realpath(__file__)), "UIB files (*.uib)")
			if result[1]:
				fileName = result[0]
			else:
				return # abort if no file specified
		elif load:
			fileName = load

		with open(fileName, "r") as inputFile:
			jsonData = json.load(inputFile) # parse JSON data	
		UiData = jsonData["UI"] # Query all Ui related data
		wh = (UiData["w"], UiData["h"])
		if self.currentMode == 0: 
			self.resetUi()
			self.resize(*wh)
			self.background = UiData["background"]
			self.__viewport.currentCID = UiData["latestCID"]	
			self.fileNiceName = UiData["fileNiceName"]
			self.startupScript.setText(UiData["startup_script"])
			self.updateBackground()
			self.currentFileData = jsonData
			self.currentFilePath = fileName

		elif self.currentMode == 1:
			newTab = ViewLayout(self)
			newTab.resize(*wh)
			newTab.background = UiData["background"]
			newTab.niceName = UiData["fileNiceName"]
			newTab.startupScript.setText(UiData["startup_script"])
			newTab.filePath = fileName
			newTab.updateBackground()

		objectsData = jsonData["content"] # Query all content related data (the objects created). Each <data> is a dictionnary containing the object type as a key, and their attributes.
		for data in objectsData:
			objectType = data.keys()[0]
			serializedData = data[objectType]
			if self.currentMode == 0:
				new = CLASSES_ENUM[objectType](self)
				new.deserialize(serializedData)
				self.items.append(new)
			elif self.currentMode == 1:
				new = CLASSES_ENUM[objectType](newTab)
				new.deserialize(serializedData, client=True)
				newTab.addItem(new)

		if self.currentMode == 1:
			self.__viewport.addTab(newTab, newTab.niceName)
			newTab.activate()
		elif self.currentMode == 0:
			self.__viewport.raise_()
			self.modified = False
			self.activate()

	def resetUi(self):
		for obj in self.items:
			obj.delete()
		self.items = []
		self.background = None
		self.updateBackground()
		self.fileNiceName = None
		self.resize(1024,760)

	def failSafe(self):
		if self.modified:
			answer = QMessageBox.question(None,
			"Unsaved changes",
			"Something has been modified on the window.\nProceed without saving?",
			QMessageBox.Yes,
			QMessageBox.No)
			if answer == QMessageBox.Yes:
				return True
			else:
				return False
		else:
			return True

	def getJsonData(self):
		data = {
			"UI":{},
			"content": []
		}
		for obj in self.items:
			objectSerial = obj.serialize()
			objectSerial[obj.objectType]["geo"] = objectSerial[obj.objectType]["geo"].getRect() # convert QRectangle into a list containing its values, 
			data["content"].append(objectSerial)														# for json to be able to dump them.

		ui_values = ["w","h", "latestCID","background", "fileNiceName", "startup_script"]
		for valuetype, value in zip(ui_values, [self.width(), self.height(), len(self.items)-1, self.background, self.fileNiceName, self.startupScript.text()]):
			data["UI"][valuetype] = value

		return data

	def hasSomethingChanged(self):
		"""
		This function checks if the current viewport and its content is exactly the same has the one stored in the file. If it appears to be different,
		self.modified is set to True, allowing a popup to warn the user that they modified something, and that it is unsaved.
		"""
		oldData = self.currentFileData
		newData = self.getJsonData()
		for k in oldData["UI"].keys(): #Check if the window is the same. If yes, check if its content is the same.
			if unicode(oldData["UI"][k]) != unicode(newData["UI"][k]):
				self.modified = True
				break
		else:
			if len(oldData["content"]) != len(newData["content"]): self.modified = True #Check if the amount of objects is the same. If yes, check that all their values are the same.
			else:
				for i in range(len(oldData["content"])): #The 'heavy' loop, used if the previous researches are insufficient.
					k = oldData["content"][i]
					values = k[k.keys()[0]]
					for v in values.keys():
						if isinstance(values[v], (tuple, list)):
							for singleValue, otherSingleValue in zip(values[v], newData["content"][i][k.keys()[0]][v]):
								if singleValue != otherSingleValue:
									self.modified = True
									break

						elif unicode(values[v]) != unicode(newData["content"][i][k.keys()[0]][v]):
							self.modified = True

						if self.modified:
							break

	def closeEvent(self, event):
		if self.currentFileData:
			self.hasSomethingChanged()
		elif len(self.items) > 0 and not self.fileNiceName:
			self.modified = True

		response = self.failSafe()
		if response: event.accept()
		else: 
			event.ignore() 
			self.saveUi()

	def restartInViewMode(self, withCurrentFile=False):
		if self.__selfOptions: self.__selfOptions.close()
		if self.console: self.console.close()
		self.close()
		if withCurrentFile: self = UIBWindow(mode=1, parent=self.parent, loadFile=self.currentFilePath)
		else: self = UIBWindow(mode=1, parent=self.parent)

	def restartInBuildMode(self, withCurrentFile=False): 
		if self.console: self.console.close()
		self.close()
		if withCurrentFile: self = UIBWindow(mode=0, parent=self.parent, loadFile=self.__viewport.currentWidget().filePath)
		else: self = UIBWindow(mode=0, parent=self.parent)

	def activate(self):
		try:
			self.startupCommand = compileFunctions(self.startupScript.text(), ["atStartup"], self.symbols)[0]
			self.startupCommand()
		except:
			raise RuntimeError("Couldn't init startup script, please check code and try again.")

class UIB(QDialog):
	def __init__(self, parent=None):
		super(UIB, self).__init__(parent)
		self.parent = parent
		self.buildingMode = QPushButton(self)
		self.buildingMode.setGeometry(QRect(60,45,85,35))
		self.buildingMode.setText("I wanna build!")
		self.viewingMode = QPushButton(self)
		self.viewingMode.setGeometry(QRect(190,45,85,35))
		self.viewingMode.setText("I wanna use!")
		self.buildingMode.clicked.connect(self.initAsBuildingMode)
		self.viewingMode.clicked.connect(self.initAsViewingMode)
		self.setWindowTitle("UIB input")
		self.show()
		self.setFixedSize(350,125)

	def initAsBuildingMode(self):
		self.close()
		self = UIBWindow(mode=0, parent=self.parent)

	def initAsViewingMode(self):
		self.close()
		self = UIBWindow(mode=1, parent=self.parent)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	win = UIB()
	sys.exit(app.exec_())