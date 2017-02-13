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

class Ui_CountLandslides(object):

    #class variables:
    highestPointsCombobox = None
    mappingUnitsCombobox = None
    dialog = None
    
    def setupUi(self, CountLandslidesDialog):
        CountLandslidesDialog.setObjectName(_fromUtf8("Count landslide events"))
        CountLandslidesDialog.resize(400, 300)
        
        mainLayout = QtGui.QVBoxLayout()
        CountLandslidesDialog.setLayout(mainLayout)
        
        self.dialog = CountLandslidesDialog
        
        horizontalLayoutUpper = QtGui.QHBoxLayout()
        horizontalLayoutMiddle = QtGui.QHBoxLayout()
        horizontalLayoutLower = QtGui.QHBoxLayout()

        highestPointsLabel = QtGui.QLabel("Select the layer with landslide highest points:", CountLandslidesDialog)
        self.highestPointsCombobox = QtGui.QComboBox()
        self.highestPointsCombobox.setMaximumWidth(210)
        mappingUnitsLabel = QtGui.QLabel("Select the layer with mapping units:", CountLandslidesDialog)
        self.mappingUnitsCombobox = QtGui.QComboBox();
        self.mappingUnitsCombobox.setMaximumWidth(210)
        openLayers = CountLandslidesDialog.getOpenMapLayers()
        for layer in openLayers.values():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.highestPointsCombobox.addItem(str(layer.name()))
                self.mappingUnitsCombobox.addItem(str(layer.name()))
        horizontalLayoutUpper.addWidget(highestPointsLabel)
        horizontalLayoutUpper.addWidget(self.highestPointsCombobox)
        horizontalLayoutMiddle.addWidget(mappingUnitsLabel)
        horizontalLayoutMiddle.addWidget(self.mappingUnitsCombobox)
        selectButton1 = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButton1.setMaximumWidth(60)
        selectButton1.clicked.connect(self.showDialogHighestPoints)
        horizontalLayoutUpper.addWidget(selectButton1)
        selectButton2 = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButton2.setMaximumWidth(60)
        selectButton2.clicked.connect(self.showDialogMappingUnits)
        horizontalLayoutMiddle.addWidget(selectButton2)

        
        mainLayout.addLayout(horizontalLayoutUpper)   
        mainLayout.addLayout(horizontalLayoutMiddle)
        mainLayout.addLayout(horizontalLayoutLower)
        
        warningLabel = QtGui.QLabel("A column with the landslide count will be added to the mapping units layer.", CountLandslidesDialog)
        mainLayout.addWidget(warningLabel)
          
        dummyLabel = QtGui.QLabel("", CountLandslidesDialog)
        mainLayout.addWidget(dummyLabel)
        
        self.buttonBox = QtGui.QDialogButtonBox(CountLandslidesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(CountLandslidesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CountLandslidesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CountLandslidesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CountLandslidesDialog)

    def retranslateUi(self, CountLandslidesDialog):
        CountLandslidesDialog.setWindowTitle(_translate("Count landslide events", "Count landslide events", None))
    
    def showDialogHighestPoints(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileName:
	    self.highestPointsCombobox.addItem(fileName)
            count = self.highestPointsCombobox.count()
            self.highestPointsCombobox.setCurrentIndex(count - 1)
    
    def showDialogMappingUnits(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileName:
	    self.mappingUnitsCombobox.addItem(fileName)
            count = self.mappingUnitsCombobox.count()
            self.mappingUnitsCombobox.setCurrentIndex(count - 1)
    
    def getSelectedHighestPointsLayer(self):
        text = self.highestPointsCombobox.currentText()
        highestPoints = None
        if text.endswith(".shp"):
            highestPoints = QgsVectorLayer(text, "Highest points", "ogr")
        else:
            openLayers = self.dialog.getOpenMapLayers()
            for layer in openLayers.values():
                if (layer.name() == text):
                    highestPoints = layer
        return highestPoints
      
    def getSelectedMappingUnitsLayer(self):
        text = self.mappingUnitsCombobox.currentText()
        mappingUnits = None
        if text.endswith(".shp"):
	    textWithoutExtention = text.split(".")[0]
	    textWithoutExtention.replace("\\", "/")
	    layerName = textWithoutExtention.split('/')[-1]
            mappingUnits = QgsVectorLayer(text, layerName, "ogr")
        else:
            openLayers = self.dialog.getOpenMapLayers()
            for layer in openLayers.values():
                if (layer.name() == text):
                    mappingUnits = layer
        return mappingUnits