from PySide.QtCore import *
from PySide.QtGui import *
"""
WARNING: AUTOMATICALLY GENERATED FILE. ALL CHANGES MAY BE LOST. 
Source: UIB. 
Developer: Leo Coulombier (contact @ leo.coulombier@gmail.com), aka Vipe. 
"""

class NodeSocket(QFrame):
    def __init__(self, parent, isInput=False):
        super(NodeSocket, self).__init__(parent)
        self.parent = parent
        self.crvColor = None
        self.globalRec = None
        self.isInput = isInput

    def formatStyle(self, style):
        color = style["NODE_COLOR"]
        if "#" in color:
            r,g,b = hex_to_rgb_2(color)
        elif isInstance(color, (list, tuple)):
            r,g,b = color
        self.crvColor = QColor(r,g,b)
        qss = 'background-color: qradialgradient(cx:0.5, cy:0.5, radius:1, fx:0.5, fy:0.5, stop:0 {NODE_COLOR}, stop:1 #000);border: 2px solid {BRD_COLOR};border-radius: 6px;'
        qss = qss.format(**style)
        self.setStyleSheet(qss)

    def mouseMoveEvent(self, event): event.ignore()
    def mousePressEvent(self, event): event.ignore()
    def mouseReleaseEvent(self, event): event.ignore()

class NodeHandle(QWidget):
    def __init__(self, parent, name):
        super(NodeHandle, self).__init__(parent)
        self.parent = parent
        self.content = []

        self.setObjectName(name)
        self.inputNode = NodeSocket(self, isInput=True)
        self.inputNode.setGeometry(QRect(*(0, 4, 14, 14)))
        self.content.append(self.inputNode)
        self.outputNode = NodeSocket(self, isInput=False)
        self.outputNode.setGeometry(QRect(*(164, 4, 14, 14)))
        self.content.append(self.outputNode)
        self.nodeLabel = QLabel(self)
        self.nodeLabel.setGeometry(QRect(*(16, 0, 145, 22)))
        self.content.append(self.nodeLabel)
        self.nodeLabel.setText('OBJECT_INPUT')
        font = QFont()
        font.setPointSize(8)
        
        self.nodeLabel.setFont(font)
        self.inputNode.formatStyle({'NODE_COLOR':'#0A0', 'BRD_COLOR':'#F00'})
        self.outputNode.formatStyle({'NODE_COLOR':'#0A0', 'BRD_COLOR':'#F00'})
        self.nodeLabel.setStyleSheet('background-color: {BG_COLOR};'.format(BG_COLOR='#BBB'))
        
        
        self.parameters = [((0.0, 0.1905), (0.0734, 0.8095)), ((0.9266, 0.1905), (1.0, 0.8095)), ((0.0904, 0.0), (0.904, 1.0))]
        self.setGeometry(QRect(*(0, 0, 177, 21)))
        self.show()

    def setGeometry(self, geo):
        super(NodeHandle, self).setGeometry(geo)
        for item, params in zip(self.content, self.parameters):
            ngeo = QRect()
            x, y = params[0]
            w, h = params[1]
            ngeo.setX(int(geo.width()*x))
            ngeo.setY(int(geo.height()*y))
            ngeo.setWidth(int(geo.width()*(w-x))+1)
            ngeo.setHeight(int(geo.height()*(h-y))+1)
            item.setGeometry(ngeo)

    def setInputNodeType(self, type):
        pass

    def setOutputNodeType(self, type):
        pass


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def hex_to_rgb_2(value):
    value = value.lstrip('#')
    lv = len(value)
    if lv == 1:
        v = int(value, 16)*17
        return v, v, v
    if lv == 3:
        return tuple(int(value[i:i+1], 16)*17 for i in range(0, 3))
    return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))