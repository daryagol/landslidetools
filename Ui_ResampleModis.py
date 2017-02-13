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

from PyQt4 import *
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

class Ui_ResampleModis(object):
    
    #constants:

    #class variables:
    inputVectorField = None
    inputRasterField = None
    outputCombobox = None
    tempFolderField = None
    
    def setupUi(self, ResampleModisDialog):
        ResampleModisDialog.setObjectName(_fromUtf8("ResampleModisDialog"))
        ResampleModisDialog.resize(400, 300)
        
        mainLayout = QtGui.QVBoxLayout()
        ResampleModisDialog.setLayout(mainLayout)
        
        horizontalLayout1 = QtGui.QHBoxLayout()
        inputVectorLabel = QtGui.QLabel("Select vector file: ", ResampleModisDialog)
        horizontalLayout1.addWidget(inputVectorLabel)
        self.inputVectorField = QtGui.QLineEdit(ResampleModisDialog)
        horizontalLayout1.addWidget(self.inputVectorField)
        inputVectorButton = QtGui.QPushButton(_fromUtf8("select"), None)
        inputVectorButton.setMaximumWidth(60)
        inputVectorButton.clicked.connect(self.inputVectorButtonClicked)
        horizontalLayout1.addWidget(inputVectorButton)
        
        horizontalLayout2 = QtGui.QHBoxLayout()
        outputLabel = QtGui.QLabel("Select column to update: ", ResampleModisDialog)
        horizontalLayout2.addWidget(outputLabel)
        self.outputCombobox = QtGui.QComboBox()
        horizontalLayout2.addWidget(self.outputCombobox)
        
        horizontalLayout3 = QtGui.QHBoxLayout()
        inputRasterLabel = QtGui.QLabel("Select raster file (e.g. Landsat): ", ResampleModisDialog)
        horizontalLayout3.addWidget(inputRasterLabel)
        self.inputRasterField = QtGui.QLineEdit(ResampleModisDialog)
        horizontalLayout3.addWidget(self.inputRasterField)
        inputRasterButton = QtGui.QPushButton(_fromUtf8("select"), None)
        inputRasterButton.setMaximumWidth(60)
        inputRasterButton.clicked.connect(self.inputRasterButtonClicked)
        horizontalLayout3.addWidget(inputRasterButton)
        
        horizontalLayout4 = QtGui.QHBoxLayout()
        tempFolderLabel = QtGui.QLabel("Select folder to store intermediate results: ", ResampleModisDialog)
        horizontalLayout4.addWidget(tempFolderLabel)
        self.tempFolderField = QtGui.QLineEdit(ResampleModisDialog)
        horizontalLayout4.addWidget(self.tempFolderField)
        tempFolderButton = QtGui.QPushButton(_fromUtf8("select"), None)
        tempFolderButton.setMaximumWidth(60)
        tempFolderButton.clicked.connect(self.tempFolderButtonClicked)
        horizontalLayout4.addWidget(tempFolderButton)
        
        mainLayout.addLayout(horizontalLayout1) 
        mainLayout.addLayout(horizontalLayout2)       
        mainLayout.addLayout(horizontalLayout3)
        mainLayout.addLayout(horizontalLayout4)
          
        dummyLabel = QtGui.QLabel("", ResampleModisDialog)
        mainLayout.addWidget(dummyLabel)
        
        self.buttonBox = QtGui.QDialogButtonBox(ResampleModisDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(ResampleModisDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ResampleModisDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ResampleModisDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ResampleModisDialog)

    def retranslateUi(self, ResampleModisDialog):
        ResampleModisDialog.setWindowTitle(_translate("Areal zonal statistics for MODIS data", "Areal zonal statistics for MODIS data", None))
    
    def getInputVectorField(self):
        return self.inputVectorField
    
    def getInputRasterField(self):
        return self.inputRasterField
    
    def getOutputCombobox(self):
        return self.outputCombobox.currentText()
    
    def getTempFolderField(self):
        return self.tempFolderField
        
    def inputRasterButtonClicked(self):
        path = None
        inputRasterFileName = QtGui.QFileDialog.getOpenFileName(None, "Open raster file (*.tif)", path, filter = "*.tif")
        self.inputRasterField.setText(inputRasterFileName)
        
    def inputVectorButtonClicked(self):
        path = None
        inputVectorFileName = QtGui.QFileDialog.getOpenFileName(None, "Open vector file (*.shp)", path, filter="*.shp")
        self.inputVectorField.setText(inputVectorFileName)

        if inputVectorFileName:
            self.outputCombobox.clear()
            vl = QgsVectorLayer(inputVectorFileName, "Polygons", "ogr")
            columns = vl.dataProvider().fields()
            for column in columns:
                self.outputCombobox.addItem(column.name())
        else:
            self.outputCombobox.clear()
    
    def tempFolderButtonClicked(self):
        path = None
        fileDialog = QtGui.QFileDialog()
        tempFolderName = fileDialog.getExistingDirectory(None, "Select folder where intermediate results will be stored", path, options=QtGui.QFileDialog.ShowDirsOnly)
        self.tempFolderField.setText(tempFolderName)

