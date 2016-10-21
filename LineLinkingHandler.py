from PySide.QtCore import *
from PySide.QtGui import *
import NodeHandleWidget as nhw
import sys, cornersCalculator

class LineLink(QWidget):
	def __init__(self, p, p1, color):
		super(LineLink, self).__init__(p)
		self.p1 = p1
		self.p2 = p1
		self.color = color
		self.crvPts = []
		self.setGeometry(0, 0, p.width(), p.height())
		self.setMouseTracking(True)
		# self.setStyleSheet("background-color:#AAA")
		self.show()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHints(QPainter.Antialiasing)
		painter.setPen(QPen(self.color,2))
		# painter.drawLine(self.p1,self.p2)
		self.getPoints()
		self.drawCrv(painter)
		painter.end()		

	def update(self, p2):
		self.p2 = p2
		super(LineLink, self).update()

	def getQPntsF(self):
		return map(lambda p: QPointF(*p), self.crvPts)

	# def getPoly(self):
	# 	return QRectF(map(lambda p: QPointF(*p), self.crvPts))

	def getPoints(self):
		p3 = [self.p2.x(), self.p2.y()]
		offset = [self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y()] 
		# print offset
		p1 = [self.p1.x()+offset[0]/2, self.p1.y()]
		p2 = [self.p1.x()+offset[0]/2, self.p1.y()+offset[1]]
		self.crvPts = [p1,p2,p3]

	def drawCrv(self, painter):
		# for x, y in self.crvPts:
		# 	painter.drawEllipse(x-4,y-4,8,8)
		path = QPainterPath()
		path.moveTo(self.p1)
		path.cubicTo(*self.getQPntsF())
		painter.drawPath(path)

	def mouseMoveEvent(self, event): event.ignore()
	def mousePressEvent(self, event): event.ignore()
	def mouseReleaseEvent(self, event): event.ignore()

class mainWid(QWidget):
	def __init__(self, p=None, nodesReceivers=[]):
		super(mainWid, self).__init__(p)
		self.parent = p
		# self.resize(p.parent.width(),p.parent.height())
		self.resize(800,800)
		# self.setMouseTracking(True)
		self.line = None
		self.crvPos = None
		self.crvs = []
		self.sockets = nodesReceivers
		self.emiter = None
		self.receiver = None
		self.show()

	def initSockets(self):
		widgets = QApplication.allWidgets()
		self.sockets = []
		for widget in widgets:
			if isinstance(widget, nhw.NodeSocket):
				pos = widget.mapToGlobal(QPoint(0,0))
				geo = widget.geometry()
				widget.globalRec = QRect(pos, QSize(geo.width(), geo.height()))
				self.sockets.append(widget)

	def mousePressEvent(self, event):
		if self.line:
			self.line.deleteLater()
			self.line = None

		for socket in self.sockets:
			if socket.globalRec.contains(event.globalPos()):
				self.line = LineLink(self, event.pos(), socket.crvColor)
				self.emiter = socket
				break		

	def mouseMoveEvent(self, event):
		if self.line:
			self.line.update(event.pos())

	def mouseReleaseEvent(self, event):
		if self.line:
			for socket in self.sockets:
				if socket.globalRec.contains(event.globalPos()) and socket.parent.objectName() != self.emiter.parent.objectName():
					self.bakeToWidget(socket)
					break

			else:
				self.line.deleteLater()
				self.line = None

	def bakeToWidget(self, socket):
		if (socket.isInput and not self.emiter.isInput) or (not socket.isInput and self.emiter.isInput):
			instance = self.line
			self.crvPos = instance.p1

			#Set curve points
			p1, p2 = self.crvPos, instance.p2

			#Set normalized QWidget geo rec
			self.crvPos = QPoint(instance.p1.x(), instance.p1.y())
			wp1, wp2 = cornersCalculator.get(self.crvPos, instance.p2, offs=1)
			x2, y2, x1, y1 = wp2.x(), wp2.y(), wp1.x(), wp1.y()
			wh = QSize(x2-x1, y2-y1)
			xy = QPoint(x1, y1)
			rec = QRect(xy, wh)
			instance.setGeometry(rec)

			#Create new normalized curve
			crvParams = cornersCalculator.getCurveParameters([p1, p2], rec, n=False)
			p2 = QPoint(wh.width()*crvParams[1][0], wh.height()*crvParams[1][1])
			instance.p1 = QPoint(wh.width()*crvParams[0][0], wh.height()*crvParams[0][1])
			instance.update(p2)

			self.crvs.append(instance)
			self.line = None
		else:
			self.line.deleteLater()
			self.line = None




class mainUi(QMainWindow):
	def __init__(self):
		super(mainUi, self).__init__()
		self.resize(800,800)
		self.wid = mainWid(self)

		self.mainTest = QWidget(self)
		self.mainTest.setGeometry(20,20,200,200)
		self.test = nhw.NodeHandle(self.mainTest, "base")
		self.test2 = nhw.NodeHandle(self.mainTest, "sec")
		self.test2.move(0,40)
		self.mainTest.lower()
		self.show()
		self.wid.initSockets()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = mainUi()
	sys.exit(app.exec_())

