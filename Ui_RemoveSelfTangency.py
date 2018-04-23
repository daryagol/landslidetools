from PyQt4 import QtCore, QtGui
from qgis.core import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_RemoveSelfTangency(object):

    #class variables:
    polygonsCombobox = None
    dialog = None
    
    def setupUi(self, RemoveSelfTangencyDialog):
        RemoveSelfTangencyDialog.setObjectName(_fromUtf8("Remove self-tangency"))
        RemoveSelfTangencyDialog.resize(400, 300)
        
        mainLayout = QtGui.QVBoxLayout()
        RemoveSelfTangencyDialog.setLayout(mainLayout)
        
        self.dialog = RemoveSelfTangencyDialog
        
        horizontalLayoutUpper = QtGui.QHBoxLayout()

        polygonsLabel = QtGui.QLabel("Select the layer with landslide polygons:", RemoveSelfTangencyDialog)
        self.polygonsCombobox = QtGui.QComboBox()
        self.polygonsCombobox.setMaximumWidth(210)
        openLayers = RemoveSelfTangencyDialog.getOpenMapLayers()
        for layer in openLayers.values():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.polygonsCombobox.addItem(str(layer.name()))
        horizontalLayoutUpper.addWidget(polygonsLabel)
        horizontalLayoutUpper.addWidget(self.polygonsCombobox)
        selectButton = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButton.setMaximumWidth(60)
        selectButton.clicked.connect(self.showDialog)
        horizontalLayoutUpper.addWidget(selectButton)
        
        mainLayout.addLayout(horizontalLayoutUpper)   
          
        dummyLabel = QtGui.QLabel("", RemoveSelfTangencyDialog)
        mainLayout.addWidget(dummyLabel)
        
        self.buttonBox = QtGui.QDialogButtonBox(RemoveSelfTangencyDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(RemoveSelfTangencyDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RemoveSelfTangencyDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RemoveSelfTangencyDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(RemoveSelfTangencyDialog)

    def retranslateUi(self, RemoveSelfTangencyDialog):
        RemoveSelfTangencyDialog.setWindowTitle(_translate("Count landslide events", "Count landslide events", None))
    
    def showDialog(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileName:
	    self.polygonsCombobox.addItem(fileName)
            count = self.polygonsCombobox.count()
            self.polygonsCombobox.setCurrentIndex(count - 1)
    
    def getSelectedPolygonLayer(self):
        text = self.polygonsCombobox.currentText()
        polygons = None
        if text.endswith(".shp"):
            polygons = QgsVectorLayer(text, "Polygons", "ogr")
        else:
            openLayers = self.dialog.getOpenMapLayers()
            for layer in openLayers.values():
                if (layer.name() == text):
                    polygons = layer
        return polygons
      
