"""
/***************************************************************************
Name		     : LandslideTools plugin
Description          : Spatial funtionality for landslide studies
copyright            : GNU General Public License
author		     : Darya Golovko
email                : dgolovko at gfz-potsdam.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

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

class Ui_AiArea(object):

    #class variables:
    catalogCombobox = None
    magnitudeCombobox = None
    mIndexField = None
    addentField = None
    outputField = None
    dialog = None
    
    def setupUi(self, AiAreaDialog):
        AiAreaDialog.setObjectName(_fromUtf8("Calculate Arias intensity for study area"))
        AiAreaDialog.resize(400, 300)
        
        mainLayout = QtGui.QVBoxLayout()
        AiAreaDialog.setLayout(mainLayout)
        
        self.dialog = AiAreaDialog
        
        horizontalLayoutCatalog = QtGui.QHBoxLayout()
        catalogLabel = QtGui.QLabel("Select earthquake catalog:", AiAreaDialog)
        horizontalLayoutCatalog.addWidget(catalogLabel)
        self.catalogCombobox = QtGui.QComboBox()
        self.catalogCombobox.setMaximumWidth(210)
        openLayers = AiAreaDialog.getOpenMapLayers()
        countOpenLayers = 0
        for layer in openLayers.values():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.catalogCombobox.addItem(str(layer.name()))
                countOpenLayers = countOpenLayers + 1
        horizontalLayoutCatalog.addWidget(self.catalogCombobox)
        selectButton = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButton.setMaximumWidth(60)
        selectButton.clicked.connect(self.showDialog)
        horizontalLayoutCatalog.addWidget(selectButton)
        mainLayout.addLayout(horizontalLayoutCatalog)
        
        horizontalLayoutMagnitude = QtGui.QHBoxLayout()
        magnitudeLabel = QtGui.QLabel("Select the magnitude field:", AiAreaDialog)
        horizontalLayoutMagnitude.addWidget(magnitudeLabel)
        self.magnitudeCombobox = QtGui.QComboBox()
        self.magnitudeCombobox.setMaximumWidth(210)
        self.updateMagnitudeCombobox()
        horizontalLayoutMagnitude.addWidget(self.magnitudeCombobox)
        mainLayout.addLayout(horizontalLayoutMagnitude)
        self.catalogCombobox.currentIndexChanged.connect(self.updateMagnitudeCombobox)
        
        horizontalLayoutFormula = QtGui.QHBoxLayout()
        formulaLabel = QtGui.QLabel("Use formula:                                     log R = ", AiAreaDialog)
        horizontalLayoutFormula.addWidget(formulaLabel)
        self.mIndexField = QtGui.QLineEdit(AiAreaDialog)
        self.mIndexField.setText("0.54")
        horizontalLayoutFormula.addWidget(self.mIndexField)
        mLabel = QtGui.QLabel("* M  +  ", AiAreaDialog)
        horizontalLayoutFormula.addWidget(mLabel)
        self.addentField = QtGui.QLineEdit(AiAreaDialog)
        self.addentField.setText("-1.8")
        horizontalLayoutFormula.addWidget(self.addentField)
        mainLayout.addLayout(horizontalLayoutFormula)     
          
        horizontalLayoutOutput = QtGui.QHBoxLayout()
        outputLabel = QtGui.QLabel("Output raster file (*.tif): ", AiAreaDialog)
        horizontalLayoutOutput.addWidget(outputLabel)
        self.outputField = QtGui.QLineEdit()
        self.outputField.setText("")
        horizontalLayoutOutput.addWidget(self.outputField)
        outputButton = QtGui.QPushButton(_fromUtf8("select"), None)
        outputButton.setMaximumWidth(60)
        outputButton.clicked.connect(self.writeToFile)
        horizontalLayoutOutput.addWidget(outputButton)
        mainLayout.addLayout(horizontalLayoutOutput)
          
        dummyLabel = QtGui.QLabel("", AiAreaDialog)
        mainLayout.addWidget(dummyLabel)
        
        self.buttonBox = QtGui.QDialogButtonBox(AiAreaDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(AiAreaDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), AiAreaDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AiAreaDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AiAreaDialog)

    def retranslateUi(self, AiAreaDialog):
        AiAreaDialog.setWindowTitle(_translate("Calculate Arias intensity for study area", "Calculate Arias intensity for study area", None))
    
    def showDialog(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileName:
            self.selectedFileName = fileName
            self.catalogCombobox.addItem(fileName)
            count = self.catalogCombobox.count()
            self.catalogCombobox.setCurrentIndex(count - 1)
            self.updateMagnitudeCombobox()
            
    # this method is called after the user has selected the earthquake catalog layer:
    def updateMagnitudeCombobox(self):
	self.magnitudeCombobox.clear()
        catalogLayer = self.getSelectedCatalogLayer()
        if catalogLayer:
	  for i in range (0, catalogLayer.fields().size()):
	    self.magnitudeCombobox.addItem(catalogLayer.fields().at(i).name())
    
    def writeToFile(self):
        path = None
        outputFileName = QtGui.QFileDialog.getSaveFileName(None, "Save as", path, filter = "*.tif")
        self.outputField.setText(outputFileName)

    def getMIndexField(self):
        return self.mIndexField
    
    def getAddentField(self):
        return self.addentField
    
    def getOutputField(self):
        return self.outputField
    
    def getSelectedCatalogLayer(self):
        text = self.catalogCombobox.currentText()
        epicenters = None
        if text.endswith(".shp"):
            epicenters = QgsVectorLayer(text, "Epicenters", "ogr")
        else:
            openLayers = self.dialog.getOpenMapLayers()
            for layer in openLayers.values():
                if (layer.name() == text):
                    epicenters = layer
        return epicenters
      
    def getSelectedMagnitudeField(self):
      return self.magnitudeCombobox.currentText()
