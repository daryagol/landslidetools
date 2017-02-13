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
from Ui_ResampleModis import Ui_ResampleModis
from glob import glob
from os import *
import os, os.path
from osgeo import gdal, gdalnumeric, ogr, osr
#import processing
import shutil
#import Image
#import numpy
import io
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

try:
    from PyQt4.QtCore import QString
except ImportError:
    QString = str

# create the dialog for Zoomer
class ResampleModisDialog(QtGui.QDialog):
        
  #class variables:
  iface = None
  
  def __init__(self, interface): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_ResampleModis ()
    self.ui.setupUi(self)
    self.iface = interface
        

  #Event handling in case "OK" was pressed
  def accept(self):
    
    fileName1 = self.ui.getInputRasterField().text().replace("\\", "/")
    tempFolderName = self.ui.getTempFolderField().text().replace("\\", "/")
    vectorFileName = self.ui.getInputVectorField().text().replace("\\", "/")
    outputColumnName = self.ui.getOutputCombobox()
    
    
    mappingUnitsLayer = QgsVectorLayer(vectorFileName, "Single feature layer", "ogr")
    features = mappingUnitsLayer.getFeatures()
    mappingUnitsLayer.startEditing()
    for feature in features:
        areaRatio = self.calculateSnowPercentage(fileName1, tempFolderName, feature)
        
        fieldIndex = 0
        fields = mappingUnitsLayer.dataProvider().fields()
        for field in fields:
            if field.name() == outputColumnName: 
                break;
            fieldIndex = fieldIndex + 1   
        mappingUnitsLayer.changeAttributeValue(feature.id(), fieldIndex, areaRatio)
        mappingUnitsLayer.updateFields()


    mappingUnitsLayer.commitChanges()
    mappingUnitsLayer.updateExtents()
    
    #close the window if button pressed:
    super(ResampleModisDialog, self).accept()
    
  # Method to process a single feature
  def calculateSnowPercentage(self, inputRasterFileName, tempFolderName, referenceFeature):
    
    #get the projection:
    fileInfo = QFileInfo(inputRasterFileName)
    baseName = fileInfo.baseName()
    rlayer = QgsRasterLayer(inputRasterFileName, baseName)
    proj = str(rlayer.crs().authid())

    
    intermediateResultsFolderName = tempFolderName + "/temp/"

    iterate = True
    while iterate == True:
        if os.path.exists(intermediateResultsFolderName):
            try:
                shutil.rmtree(intermediateResultsFolderName)
            except:
                time.sleep(5)
            else:
                iterate = False
        else:
            iterate = False
            
    os.makedirs(intermediateResultsFolderName)
    singleFeatureVectorLayerFileName = intermediateResultsFolderName + "singlefeature.shp"
    polygonProjectionString = "Polygon?crs=" + proj
    singleFeatureVectorLayer = QgsVectorLayer(polygonProjectionString, "Single feature layer", "memory")
    fet = QgsFeature()
    fet.setGeometry(referenceFeature.geometry())
    singleFeatureVectorLayer.dataProvider().addFeatures([fet])
    QgsVectorFileWriter.writeAsVectorFormat(singleFeatureVectorLayer, singleFeatureVectorLayerFileName, "CP1250", None, "ESRI Shapefile")
    
    command = "gdalwarp -q -cutline " + singleFeatureVectorLayerFileName + " -crop_to_cutline -of GTiff " + inputRasterFileName + " " + intermediateResultsFolderName +"clippedRaster.tif"
    os.system(command)

    pathToClippedRaster = intermediateResultsFolderName + "clippedRaster.tif"
    maskedRaster = gdal.Open(pathToClippedRaster)
    
    inputBand = maskedRaster.GetRasterBand(1)
    
    srcband = inputBand
    outShapefile = intermediateResultsFolderName + "polygonized.shp"
    # Remove output shapefile if it already exists
    if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    
    # Create the output shapefile
   
    outDataSource = outDriver.CreateDataSource(outShapefile)
    outShapefileQstring = QString(outShapefile)
    outLayer = outDataSource.CreateLayer(outShapefileQstring, geom_type=ogr.wkbPolygon) 
    
    gdal.Polygonize( srcband, srcband, outLayer, 1)
    
    #close gdal datasets:
    outDataSource = None
    outDriver = None
    
    #mapping unit layer:
    referenceArea = referenceFeature.geometry().area()

    s = QSettings()
    oldValidation = s.value("/Projections/defaultBehaviour", "useGlobal")
    s.setValue("/Projections/defaultBehaviour", "useGlobal")
    
    #snow layer:
    snowLayer = QgsVectorLayer(outShapefile, "Snow layer", "ogr")
    features = snowLayer.getFeatures()
    snowArea = 0
    for feature in features:
       intersection = referenceFeature.geometry().intersection(feature.geometry())
       snowArea = snowArea + intersection.area()
    areaRatio = snowArea * 100.0 / referenceArea

    #remove the intermediate results folder and all files inside it:
    singleFeatureVectorLayerFileName = None
    singleFeatureVectorLayer = None    
    fet = None
    command = None
    pathToClippedRaster = None
    maskedRaster = None
    inputBand = None
    srcband = None
    outShapefile = None
    outLayer = None
    snowLayer = None
    
    return areaRatio

    

