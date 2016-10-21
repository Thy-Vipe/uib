import functools
import math
import ctypes
import os
import random as ran
from PySide.QtCore import *
from PySide.QtGui import *

with open("%s\\objNames.uibsrc"%os.path.dirname(os.path.realpath(__file__)), "r") as dictionnaryFile:
  WORDS_DIC = dictionnaryFile.readlines()
'''
This block of code is responsible for maintainting
consistent UNDO-REDO stack for Maya

Chunk is an atomic sequence of commands
Undoing a chunk rolls back any commands inside
'''

# CHUNK_OPEN = False # global chunk state

# def undoable_open(): # opens the global chunk to store an atomic command sequence
#   global CHUNK_OPEN
#   if not CHUNK_OPEN:
#     pm.undoInfo(ock=1)
#     CHUNK_OPEN = True

# def undoable_close(): # closes the global chunk
#   global CHUNK_OPEN
#   if CHUNK_OPEN:
#     pm.undoInfo(cck=1)
#     CHUNK_OPEN = False

# undoable_b = functools.partial(pm.undoInfo, ock=1) # opens local chunk
# undoable_e = functools.partial(pm.undoInfo, cck=1) # closes local chunk
def distance(QPoint1, QPoint2):
  dist = math.sqrt((QPoint2.x() - QPoint1.x())**2 + (QPoint2.y() - QPoint1.y())**2)
  return dist 

'''
Calculates parameters for a given object's geometry according to a reference QRectangle.
'''
def getParameters(itemGeo, refGeo, *paramsIndexes, **kw):
  corners = [itemGeo.topLeft(), itemGeo.topRight(), itemGeo.bottomLeft(), itemGeo.bottomRight()]
  itemPoints = [corners[i] for i in paramsIndexes] if len(paramsIndexes) > 0 else corners
  rangeX = float(refGeo.width())
  rangeY = float(refGeo.height())
  parameters = []
  pre = kw.get("pre", -1) # A Value of -1 for the precision means "as precise as possible"
  for ip in itemPoints:
    relativePos = (ip.x() - refGeo.x(), ip.y() - refGeo.y())
    param = (round(relativePos[0]/rangeX, pre), round(relativePos[1]/rangeY, pre)) if pre >= 0 else (relativePos[0]/rangeX, relativePos[1]/rangeY)
    parameters.append(param)

  return tuple(parameters)


'''
Calculates a hitbox for a given content. (highest object -> lowest object on X and Y)
Keep in mind that highest is technically UNDER lower. 
'''
def getHIB(items):
  currentTop = None
  currentBottom = None
  for item in items:
    geo = item.geometry()
    topleft = geo.topLeft()
    bottomright = geo.bottomRight()
    if currentTop is None or currentTop.x() > topleft.x():
      if currentTop is None: currentTop = QPoint(999999,999999)
      currentTop.setX(topleft.x())
    if currentTop is None or currentTop.y() > topleft.y():
      currentTop.setY(topleft.y())

    if currentBottom is None or currentBottom.x() < bottomright.x():
      if currentBottom is None: currentBottom = QPoint(0,0)
      currentBottom.setX(bottomright.x())
    if currentBottom.y() < bottomright.y():
      currentBottom.setY(bottomright.y())

    top, bottom = currentTop, QSize(currentBottom.x() - currentTop.x(), currentBottom.y() - currentTop.y())

  return QRect(top, bottom)
'''
catches if two objects have the same align (x;y)
'''
def getAlign(items, current, skipped=None):
  if not isinstance(items, tuple): raise TypeError("First arg must be a Tuple object.")
  if not isinstance(current, (tuple)): current = tuple([current])[0]
  else: current = current[0]
  if skipped and not isinstance(skipped, tuple): raise TypeError("Skipped param must be Tuple object.")
  items = list(items)
  itemsQuantity = len(items)

  if skipped:
    sortedList = []
    skippedValues = [i.cid for i in skipped]
    for idref in items:
      if idref.cid not in skippedValues:
        sortedList.append(idref)
    items = sortedList
    itemsQuantity = len(items)
    
  if (itemsQuantity == 0 or items[itemsQuantity-1].cid == items[0].cid) and not current.cid == -1 : return # If there's only one object created/edited
  if itemsQuantity >= 2 and current.cid != -1 : items.pop(current.cid)
  itemPosX = [current.geometry().topLeft(), current.geometry().bottomLeft()]
  itemPosY = [current.geometry().topLeft(), current.geometry().topRight()]
  outputX1 = [False, None]
  outputX2 = [False, None]
  outputY1 = [False, None]
  outputY2 = [False, None]
  exactMatch = [False, False, False, False]

  XIsTrue = False
  for item in items:
    if itemPosX[0].y()-4 <= item.geometry().topLeft().y() <= itemPosX[0].y()+4:
      outputX1 = [True, itemPosX[0].y()-3]
      XIsTrue = True
    if itemPosX[0].y() == item.geometry().topLeft().y(): exactMatch[0] = True

    if itemPosX[1].y()-4 <= item.geometry().bottomLeft().y() <= itemPosX[1].y()+4:
      outputX2 = [True, itemPosX[1].y()+2]
      XIsTrue = True
    if itemPosX[1].y() == item.geometry().bottomLeft().y(): exactMatch[1] = True

    if XIsTrue: break

  YisTrue = False
  for item in items:
    if itemPosY[0].x()-4 <= item.geometry().topLeft().x() <= itemPosY[0].x()+4:
      outputY1 = [True, itemPosY[0].x()-3]
      YisTrue = True
    if itemPosY[0].x() == item.geometry().topLeft().x(): exactMatch[2] = True

    if itemPosY[1].x()-4 <= item.geometry().topRight().x() <= itemPosY[1].x()+4:
      outputY2 = [True, itemPosY[1].x()+2]
      YisTrue = True
    if itemPosY[1].x() == item.geometry().topRight().x(): exactMatch[3] = True

    if YisTrue: break

  return tuple(outputX1), tuple(outputY1), tuple(outputX2), tuple(outputY2), exactMatch
'''
Convert list to string
'''
def convert_to_str(l):
  output = ""
  for string in l:
    output += '%s;'%string

  output = output[:len(output)-1]
  return output

'''
Convert string to list
'''
def convert_to_list(s, arg=';'):
  s = s.replace(" ", "") #remove all spaces
  output = s.split(arg)
  return output

'''
calculates an area.
'''
def calculateSurface(w, h): return w*h

'''
To find slider's orientation according to user choices.
'''
def guessOrient(w, h):
  if w <= h: return False
  else: return True

'''
rebuilds the CIDs
'''
def rebuildCIDs(items):
  for item, cid in zip(items, range(len(items))):
    item.cid = cid

  return len(items)-1 # Return the new current CID
'''
Calculates the upper left and lower right corners
of drag area specified by drag ~start~ and ~end~ positions
'''
def calculateCorners(start, end):
  offset = end - start
  if offset.x() >= 0 and offset.y() >= 0: # direction: right-down
    upper_left = start
    lower_right = end

  elif offset.x() >= 0 and offset.y() <= 0: # direction: right-up
    upper_left = QPoint(start.x(), end.y())
    lower_right = QPoint(end.x(), start.y())

  elif offset.x() <= 0 and offset.y() >= 0: # direction: left-down
    upper_left = QPoint(end.x(), start.y())
    lower_right = QPoint(start.x(), end.y())

  elif offset.x() <= 0 and offset.y() <= 0: # direction: left-up
    upper_left = end
    lower_right = start

  return (upper_left, lower_right)


'''
Wrapper for getting current project's /characters directory
'''
# def charactersDir():
#   rootDir = pm.workspace(q=1, rd=1)
#   charDir = rootDir+"characters/"
#   pm.workspace.mkdir(charDir)
#   return charDir


'''
Compiles the functions inside ~string~ inside scope defined by ~symbols~
Returns only functions specified in ~names~ argument
'''
def compileFunctions(string, names, symbols):
  exec string in symbols # compile the code in given scope
  return [symbols[name] for name in names] # extract necessary functions and return them

'''
Calculates next node of the grid of ~size~ x ~size~ dimensions
In the direction of ~offset~
'''
def nextGridNode(point, offset, size):
  x = point.x()
  y = point.y()

  if offset.x() >= 0: # direction: left
    grid_x = x + (size - x % size) # clamp to nearest node on the left
  else:
    grid_x = x - x % size # clamp to nearest node on the right

  if offset.y() >= 0:
    grid_y = y + (size - y % size) # clamp to nearest node downwards
  else:
    grid_y = y - y % size # clamp to nearest node upwards

  return QPoint(grid_x, grid_y)

'''
Calculates the hex form (#XXXXXX) of the override color for ~obj~
If ~obj~ has no override color, the method traverses the hierarchy up
until one of the parents has override color in transform node.
If nothing found, None is returned
'''
# def getOverrideColor(obj):
#   colorId = getOverrideColorId(obj) # search for colorIndex of the obj or its parents

#   if colorId:
#     floatColor = pm.colorIndex(colorId, q=1) # get float RGB values from Maya for given id
#     intVal = [int(math.ceil(v*255)) for v in floatColor] # convert float values to integers
#     return hexColor(intVal) # convert to hex and return
#   else:
#     return None

'''
Recursive method to traverse hierarchy upwards looking for an override color
'''
def getOverrideColorId(obj, first_lvl=True):
  xformColor = obj.getAttr("overrideColor") # OC of the transform node
  shapeColor = obj.getShape().getAttr("overrideColor") # OC of the shape node
    
  if xformColor: # if has OC in transform
    return xformColor
  else:
    if first_lvl and shapeColor: # if we haven't yet dived into recursion and the object has OC in shape node
      return shapeColor # return it
    else:
      parentNode = obj.getParent() # get parent node
      if parentNode:
        return getOverrideColorId(parentNode, False) # start recursive traverse up the hierarchy
      else:
        return 0 # if has no parent and not own OC

'''
Returns hex form of color for given list of integer RGB values
'''
def hexColor(rgbVal):
  return "#{:02x}{:02x}{:02x}".format(*rgbVal) # using python str.format to convert RGB integers for hex

'''
Multiplies given ~color~ in hex form by ~coef~
'''
def multiplyColor(color, coef):
  r = int(coef * int(color[1]+color[2], 16))
  g = int(coef * int(color[3]+color[4], 16))
  b = int(coef * int(color[5]+color[6], 16))
    
  r = r if r<255 else 255
  g = g if g<255 else 255
  b = b if b<255 else 255
    
  return hexColor([r,g,b])

def randomObjName():
  name = "{n}_{v}"
  w = ran.choice(WORDS_DIC)
  w = w.replace("\n", "")
  num = ran.randint(0,999)
  name = name.format(n=w, v=num)
  return name

'''
Wrapper for multiplyColor to get a darker tone (0.7 coefficient)
'''
darker = lambda x: multiplyColor(x, 0.7)

'''
Wrapper for multiplyColor to get a brighter tone (1.3 coefficient)
'''
brighter = lambda x: multiplyColor(x, 1.3)


OpenClipboard = ctypes.windll.user32.OpenClipboard
EmptyClipboard = ctypes.windll.user32.EmptyClipboard
GetClipboardData = ctypes.windll.user32.GetClipboardData
SetClipboardData = ctypes.windll.user32.SetClipboardData
CloseClipboard = ctypes.windll.user32.CloseClipboard
CF_UNICODETEXT = 13

GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
GlobalSize = ctypes.windll.kernel32.GlobalSize
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

unicode_type = type(u'')

def queryClipBoard():
    text = None
    OpenClipboard(None)
    handle = GetClipboardData(CF_UNICODETEXT)
    pcontents = GlobalLock(handle)
    size = GlobalSize(handle)
    if pcontents and size:
        raw_data = ctypes.create_string_buffer(size)
        ctypes.memmove(raw_data, pcontents, size)
        text = raw_data.raw.decode('utf-16le').rstrip(u'\0')
    GlobalUnlock(handle)
    CloseClipboard()
    return text

def toClipBoard(s):
    if not isinstance(s, unicode_type):
        s = s.decode('mbcs')
    data = s.encode('utf-16le')
    OpenClipboard(None)
    EmptyClipboard()
    handle = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data) + 2)
    pcontents = GlobalLock(handle)
    ctypes.memmove(pcontents, data, len(data))
    GlobalUnlock(handle)
    SetClipboardData(CF_UNICODETEXT, handle)
    CloseClipboard()
