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
from Ui_HighestPoints import Ui_HighestPoints
from glob import glob
from os import path
import numpy
import os
from osgeo import gdal
from osgeo import ogr
import osr
import shutil
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# create the dialog for inventory queries
class HighestPointsDialog(QtGui.QDialog):
  
  #class variables:
  iface = None
  pathToTempFolder = None
  
  def __init__(self, interface, path): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_HighestPoints ()
    self.ui.setupUi(self)
    self.iface = interface
    self.pathToTempFolder = path

  #Event handling in case "OK" was pressed
  def accept(self):   

    landslides = self.ui.getSelectedLandslideLayer()
    demPath = self.ui.getSelectedDemLayer()
    if demPath == None: 
       return
    dem = gdal.Open(demPath)
    if landslides is None or dem is None:
      return
    demBand = dem.GetRasterBand(1)
    demTransform = dem.GetGeoTransform()
    demOriginX = demTransform[0]
    demOriginY = demTransform[3]
    demPixelWidth = demTransform[1] # W-E pixel resolution
    demPixelHeight = demTransform[5] # N-S pixel resolution
    
    highestPoints = QgsVectorLayer("Point?crs=" + landslides.crs().toWkt(), "Highest points", "memory")
    highestPoints.startEditing()
    highestPoints.dataProvider().addAttributes([QgsField(self.ui.getSelectedIdField(), QVariant.String)])
    highestPoints.updateFields()
    
    for landslide in landslides.getFeatures():

        #create temporary folder:
        intermediateResultsFolderName = self.pathToTempFolder + "/QgisLandslideToolsTemp/"

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
        singleFeatureVectorLayer = QgsVectorLayer("Polygon?crs=" +  landslides.crs().toWkt(), "Single feature layer", "memory")
        fet = QgsFeature()
        fet.setGeometry(landslide.geometry())
        singleFeatureVectorLayer.dataProvider().addFeatures([fet])
        QgsVectorFileWriter.writeAsVectorFormat(singleFeatureVectorLayer, singleFeatureVectorLayerFileName, "CP1250", None, "ESRI Shapefile")
    
	outside = ' '
	if self.ui.getOutsideCheckbox().isChecked():
	  outside = ' -at '

        #command = 'gdal_rasterize' + outside + '-burn 1 -tr ' + str(demPixelWidth) + ' ' + str(demPixelHeight) + ' ' + singleFeatureVectorLayerFileName + ' ' + intermediateResultsFolderName + 'rasterized.tif'
	command = 'gdalwarp -q -cutline ' + singleFeatureVectorLayerFileName + ' -crop_to_cutline -tr ' +  str(demPixelWidth) + ' ' + str(demPixelHeight) + ' -of GTiff ' + demPath + ' ' + intermediateResultsFolderName + 'rasterized.tif'
	os.system(command)

        pathToClippedRaster = intermediateResultsFolderName + "rasterized.tif"
        maskedRaster = gdal.Open(pathToClippedRaster)

        try:

            inputBand = maskedRaster.GetRasterBand(1)
            
            cols = maskedRaster.RasterXSize
            rows = maskedRaster.RasterYSize       
            data = inputBand.ReadAsArray(0, 0, cols, rows)
            transform = maskedRaster.GetGeoTransform()
            originX = transform[0]
            originY = transform[3]
            pixelWidth = transform[1]
            pixelHeight = transform[5]
        
            maxHeight = -1
            maxHeightIndices = [0.000000, 0.000000] 

            for col in range(0, cols):
                for row in range(0, rows):
                    if data[row, col] != 0:
                        pixelCenterX = originX + col * pixelWidth + 0.5 * pixelWidth
                        pixelCenterY = originY + row * pixelHeight - 0.5 * pixelWidth
                        demXOffset = int((pixelCenterX - demOriginX) / demPixelWidth)
                        demYOffset = int((pixelCenterY - demOriginY) / demPixelHeight)
                        heightValue = demBand.ReadAsArray(demXOffset, demYOffset, 1, 1)
                        
                        if heightValue > maxHeight:
                            maxHeight = heightValue
                            maxHeightIndices = [pixelCenterX, pixelCenterY]
        
            if maxHeight != -1:
                highestPoint = QgsFeature()
                point = QgsPoint(maxHeightIndices[0], maxHeightIndices[1])
                highestPointGeom = QgsGeometry.fromPoint(point)
                highestPoint.setGeometry(highestPointGeom)
                highestPoint.initAttributes(1)
                highestPoint.setAttribute(0, landslide[self.ui.getSelectedIdField()])
                highestPoints.dataProvider().addFeatures([highestPoint])
        
        except:
            count = 1
        
        singleFeatureVectorLayer = None
        singleFeatureVectorLayerFileName = None
        fet = None
        command = None
        pathToClippedRaster = None
        maskedRaster = None
        inputBand = None
        data = None
        
    highestPoints.commitChanges()
    highestPoints.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(highestPoints)
    
    #close the window if button pressed:
    super(HighestPointsDialog, self).accept()

    
  def getOpenMapLayers(self):
      layers = QgsMapLayerRegistry.instance().mapLayers()
      return layers
    
