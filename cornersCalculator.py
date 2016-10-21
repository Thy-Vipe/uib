from PySide.QtCore import QPoint



def get(start, end, offs=0):
  offset = end - start
  offs = QPoint(offs, offs)
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

  return (upper_left-offs, lower_right+offs)


def getCurveParameters(curvePoints, refGeo, n=False):
  parameters = []
  x,y,w,h = refGeo.getRect()
  for pnt in curvePoints:
    paramX = float(pnt.x()-x) / w
    paramY =  float(pnt.y()-y) / h
    if n:
    	paramX = int(round(paramX))
    	paramY = int(round(paramY))
    parameters.append((paramX, paramY))

  return parameters