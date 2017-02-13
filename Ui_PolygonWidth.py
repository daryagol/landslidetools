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

class Ui_PolygonWidth(object):

    #class variables:
    landslideCombobox = None
    landslideIdCombobox = None
    lineCombobox = None
    lineIdCombobox = None
    dialog = None
    
    def setupUi(self, PolygonWidthDialog):
        PolygonWidthDialog.setObjectName(_fromUtf8("Polygon width"))
        PolygonWidthDialog.resize(400, 300)
        
        mainLayout = QtGui.QVBoxLayout()
        PolygonWidthDialog.setLayout(mainLayout)
        
        self.dialog = PolygonWidthDialog
        
        # for selecting the landslide layer:
        horizontalLayoutUpper = QtGui.QHBoxLayout()
        landslideLabel = QtGui.QLabel("Select landslide layer:", PolygonWidthDialog)
        horizontalLayoutUpper.addWidget(landslideLabel)
        self.landslideCombobox = QtGui.QComboBox()
        self.landslideCombobox.setMaximumWidth(210)
        openLayers = PolygonWidthDialog.getOpenMapLayers()
        for layer in openLayers.values():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.landslideCombobox.addItem(str(layer.name()))
        horizontalLayoutUpper.addWidget(self.landslideCombobox)
        selectButton = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButton.setMaximumWidth(60)
        selectButton.clicked.connect(self.showDialogLandslide)
        horizontalLayoutUpper.addWidget(selectButton)
        mainLayout.addLayout(horizontalLayoutUpper)   
        
        # for selecting the join field of the landslide layer:
        horizontalLayoutLandslideId = QtGui.QHBoxLayout()
        landslideIdLabel = QtGui.QLabel("Select the join field of the landslide layer:", PolygonWidthDialog)
        horizontalLayoutLandslideId.addWidget(landslideIdLabel)
        self.landslideIdCombobox = QtGui.QComboBox()
        self.landslideIdCombobox.setMaximumWidth(210)
        self.updateLandslideIdCombobox()
        horizontalLayoutLandslideId.addWidget(self.landslideIdCombobox)
        mainLayout.addLayout(horizontalLayoutLandslideId)
        self.landslideCombobox.currentIndexChanged.connect(self.updateLandslideIdCombobox)
        
        # for selecting the layer with the length lines:
        horizontalLayoutLower = QtGui.QHBoxLayout()
        lineLabel = QtGui.QLabel("Select layer that contains length lines:", PolygonWidthDialog)
        horizontalLayoutLower.addWidget(lineLabel)
        self.lineCombobox = QtGui.QComboBox()
        self.lineCombobox.setMaximumWidth(210)
        openLayers2 = PolygonWidthDialog.getOpenMapLayers()
        for layer in openLayers2.values():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.lineCombobox.addItem(str(layer.name()))
        horizontalLayoutLower.addWidget(self.lineCombobox)
        selectButton2 = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButton2.setMaximumWidth(60)
        selectButton2.clicked.connect(self.showDialogLine)
        horizontalLayoutLower.addWidget(selectButton2)
        mainLayout.addLayout(horizontalLayoutLower)
        
        # for selecting the join field of the landslide layer:
        horizontalLayoutLineId = QtGui.QHBoxLayout()
        lineIdLabel = QtGui.QLabel("Select the join field of the lenth lines layer:", PolygonWidthDialog)
        horizontalLayoutLineId.addWidget(lineIdLabel)
        self.lineIdCombobox = QtGui.QComboBox()
        self.lineIdCombobox.setMaximumWidth(210)
        self.updateLineIdCombobox()
        horizontalLayoutLineId.addWidget(self.lineIdCombobox)
        mainLayout.addLayout(horizontalLayoutLineId)
        self.lineCombobox.currentIndexChanged.connect(self.updateLineIdCombobox)
          
        dummyLabel = QtGui.QLabel("", PolygonWidthDialog)
        mainLayout.addWidget(dummyLabel)
        
        self.buttonBox = QtGui.QDialogButtonBox(PolygonWidthDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(PolygonWidthDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PolygonWidthDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PolygonWidthDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PolygonWidthDialog)

    def retranslateUi(self, PolygonWidthDialog):
        PolygonWidthDialog.setWindowTitle(_translate("Polygon width", "Polygon width", None))
    
    def showDialogLandslide(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileName:
            self.selectedFileName = fileName
            self.landslideCombobox.addItem(fileName)
            count = self.landslideCombobox.count()
            self.landslideCombobox.setCurrentIndex(count - 1)
            self.updateLandslideIdCombobox()
            
    def showDialogLine(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileName:
            self.selectedFileName = fileName
            self.lineCombobox.addItem(fileName)
            count = self.lineCombobox.count()
            self.lineCombobox.setCurrentIndex(count - 1)
            self.updateLineIdCombobox()
        
    # this method is called after the user has selected the landslide layer:
    def updateLandslideIdCombobox(self):
	self.landslideIdCombobox.clear()
        landslideLayer = self.getSelectedLandslideLayer()
        if landslideLayer:
	  for i in range (0, landslideLayer.fields().size()):
	    self.landslideIdCombobox.addItem(landslideLayer.fields().at(i).name())
	   
    # this method is called after the user has selected the length line layer:
    def updateLineIdCombobox(self):
	self.lineIdCombobox.clear()
        lineLayer = self.getSelectedLineLayer()
        if lineLayer:
	  for i in range (0, lineLayer.fields().size()):
	    self.lineIdCombobox.addItem(lineLayer.fields().at(i).name())
    
    
    def getSelectedLandslideLayer(self):
        text = self.landslideCombobox.currentText()
        landslides = None
        if text.endswith(".shp"):
            landslides = QgsVectorLayer(text, "Landslides", "ogr")
        else:
            openLayers = self.dialog.getOpenMapLayers()
            for layer in openLayers.values():
                if (layer.name() == text):
                    landslides = layer
        return landslides
    
    def getSelectedLineLayer(self):
        text = self.lineCombobox.currentText()
        lines = None
        if text.endswith(".shp"):
            lines = QgsVectorLayer(text, "Length lines", "ogr")
        else:
            openLayers = self.dialog.getOpenMapLayers()
            for layer in openLayers.values():
                if (layer.name() == text):
                    lines = layer
        return lines
      
    def getSelectedLandslideIdField(self):
      return self.landslideIdCombobox.currentText()
    
    def getSelectedLineIdField(self):
      return self.lineIdCombobox.currentText()
