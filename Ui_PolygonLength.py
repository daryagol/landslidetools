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
from osgeo import gdal

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

class Ui_PolygonLength(object):

    #class variables:
    landslideCombobox = None
    idCombobox = None
    demCombobox = None
    dialog = None
    
    def setupUi(self, PolygonLengthDialog):
        PolygonLengthDialog.setObjectName(_fromUtf8("Polygon length"))
        PolygonLengthDialog.resize(400, 300)
        
        mainLayout = QtGui.QVBoxLayout()
        PolygonLengthDialog.setLayout(mainLayout)
        
        self.dialog = PolygonLengthDialog
        
        # for selecting the landslide layer:
        horizontalLayoutLandslide = QtGui.QHBoxLayout()
        landslideLabel = QtGui.QLabel("Select landslide layer:", PolygonLengthDialog)
        horizontalLayoutLandslide.addWidget(landslideLabel)
        self.landslideCombobox = QtGui.QComboBox()
        self.landslideCombobox.setMaximumWidth(210)
        openLayers = PolygonLengthDialog.getOpenMapLayers()
        for layer in openLayers.values():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.landslideCombobox.addItem(str(layer.name()))
        self.landslideCombobox.activated.connect(self.updateIdCombobox)
        horizontalLayoutLandslide.addWidget(self.landslideCombobox)
        selectButtonLandslide = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButtonLandslide.setMaximumWidth(60)
        selectButtonLandslide.clicked.connect(self.showDialogLandslide)
        horizontalLayoutLandslide.addWidget(selectButtonLandslide)
        mainLayout.addLayout(horizontalLayoutLandslide)   
        
        # for selecting the id field of the landslide layer:
        horizontalLayoutId = QtGui.QHBoxLayout()
        idLabel = QtGui.QLabel("Select the to be used as ID:", PolygonLengthDialog)
        horizontalLayoutId.addWidget(idLabel)
        self.idCombobox = QtGui.QComboBox()
        self.idCombobox.setMaximumWidth(210)
        self.updateIdCombobox()
        horizontalLayoutId.addWidget(self.idCombobox)
        mainLayout.addLayout(horizontalLayoutId)
        
        # for selecting the DEM layer:
        horizontalLayoutDem = QtGui.QHBoxLayout()
        demLabel = QtGui.QLabel("Select DEM layer:", PolygonLengthDialog)
        horizontalLayoutDem.addWidget(demLabel)
        self.demCombobox = QtGui.QComboBox()
        self.demCombobox.setMaximumWidth(210)
        for layer in openLayers.values():
            if layer.type() == QgsMapLayer.RasterLayer:
                self.demCombobox.addItem(str(layer.name()))
        horizontalLayoutDem.addWidget(self.demCombobox)
        selectButtonDem = QtGui.QPushButton(_fromUtf8("select"), None)
        selectButtonDem.setMaximumWidth(60)
        selectButtonDem.clicked.connect(self.showDialogDem)
        horizontalLayoutDem.addWidget(selectButtonDem)
        mainLayout.addLayout(horizontalLayoutDem)  
        
        
	# add a dummy label for a better styling:          
        dummyLabel = QtGui.QLabel("", PolygonLengthDialog)
        mainLayout.addWidget(dummyLabel)
        
        self.buttonBox = QtGui.QDialogButtonBox(PolygonLengthDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(PolygonLengthDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PolygonLengthDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PolygonLengthDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PolygonLengthDialog)

    def retranslateUi(self, PolygonLengthDialog):
      PolygonLengthDialog.setWindowTitle(_translate("Polygon length", "Polygon length", None))
    
    def showDialogLandslide(self):
        fileNameLandslide = QtGui.QFileDialog.getOpenFileName(None, "Open file", None, "Shapefiles (*.shp)")
        if fileNameLandslide:
            self.landslideCombobox.addItem(fileNameLandslide)
            count = self.landslideCombobox.count()
            self.landslideCombobox.setCurrentIndex(count - 1)
            self.updateIdCombobox()

    def showDialogDem(self):
      inputRasterFileName = QtGui.QFileDialog.getOpenFileName(None, "Open raster file", None, filter = "*.tif *.tiff *.img *.gif *.bmp")
      if inputRasterFileName:
	  self.demCombobox.addItem(inputRasterFileName)
	  count = self.demCombobox.count()
	  self.demCombobox.setCurrentIndex(count - 1)
	 
    # this method is called after the user has selected the landslide layer:
    def updateIdCombobox(self):
	self.idCombobox.clear()
        landslideLayer = self.getSelectedLandslideLayer()
        if landslideLayer:
	  for i in range (0, landslideLayer.fields().size()):
	    self.idCombobox.addItem(landslideLayer.fields().at(i).name())
    
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
	 

    def getSelectedIdField(self):
      return self.idCombobox.currentText()
	 
    def getSelectedDemLayer(self):
      path = None
      text = self.demCombobox.currentText()
      if text.endswith(".tif") or text.endswith(".tiff") or text.endswith(".img") or text.endswith(".gif") or text.endswith(".bmp"):
         path = text
      else:
	     openLayers = self.dialog.getOpenMapLayers()
	     for layer in openLayers.values():
	        if (layer.name() == text):
	           path = layer.dataProvider().dataSourceUri()
      return path
      
