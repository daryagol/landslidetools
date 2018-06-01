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
from Ui_HighestPercent import Ui_HighestPercent
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
class HighestPercentDialog(QtGui.QDialog):
  
  #class variables:
  iface = None
  pathToTempFolder = None
  
  def __init__(self, interface, path): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_HighestPercent ()
    self.ui.setupUi(self)
    self.iface = interface
    self.pathToTempFolder = path


  #Event handling in case "OK" was pressed
  def accept(self):   

    landslides = self.ui.getSelectedLandslideLayer()
    demPath = self.ui.getSelectedDemLayer()
    dem = gdal.Open(demPath)
    if landslides is None or dem is None:
      return

    demBand = dem.GetRasterBand(1)
    demTransform = dem.GetGeoTransform()
    demOriginX = demTransform[0]
    demOriginY = demTransform[3]
    demPixelWidth = demTransform[1] # W-E pixel resolution
    demPixelHeight = demTransform[5] # N-S pixel resolution

    # Prepare to resample the DEM to a resolution of 4-5 m. 5m is the maximum allowed resolution and we divide by 4 to increase the number of parts: 
    numberOfPartsWidth = abs(demPixelWidth) // 4
    newResolutionWidth = demPixelWidth / numberOfPartsWidth
    numberOfPartsHeight = abs(demPixelHeight) // 4
    newResolutionHeight = demPixelHeight / numberOfPartsHeight  

    highestPercent = QgsVectorLayer("Polygon?crs=" + landslides.crs().toWkt(), "Highest N percent", "memory")
    highestPercent.startEditing()
    highestPercent.dataProvider().addAttributes([QgsField(self.ui.getSelectedIdField(), QVariant.String)])
    highestPercent.updateFields()
    
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
        
        # Write a single feature to a shapefile in the temp folder (for debugging):
        singleFeatureVectorLayerFileName = intermediateResultsFolderName + "singlefeature.shp"
        singleFeatureVectorLayer = QgsVectorLayer("Polygon?crs=" +  landslides.crs().toWkt(), "Single feature layer", "memory")
        fet = QgsFeature()
        fet.setGeometry(landslide.geometry())
        singleFeatureVectorLayer.dataProvider().addFeatures([fet])
        QgsVectorFileWriter.writeAsVectorFormat(singleFeatureVectorLayer, singleFeatureVectorLayerFileName, "CP1250", None, "ESRI Shapefile")

        # get the boundaries to correctly crop the dem layer without shifts:
        # code from: https://gis.stackexchange.com/questions/186491/gdalwarp-causing-shift-in-pixels?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        singleFeatureLayerOgr = ogr.Open(singleFeatureVectorLayerFileName)
        layerOgr = singleFeatureLayerOgr.GetLayer(0)
        layerOgr.ResetReading()
        singleFeatureOgr = layerOgr.GetNextFeature()
        geometryOgr = singleFeatureOgr.GetGeometryRef()
        minx, maxx, miny, maxy = geometryOgr.GetEnvelope()
        # compute the pixel-aligned bounding box (larger than the feature's bbox)
        left = minx - (minx - demOriginX) % demPixelWidth
        right = maxx + (demPixelWidth - ((maxx - demOriginX) % demPixelWidth))
        bottom = miny + (demPixelHeight - ((miny - demOriginY) % demPixelHeight))
        top = maxy - (maxy - demOriginY) % demPixelHeight
    
        command = 'gdalwarp -overwrite -q -cutline ' + singleFeatureVectorLayerFileName + ' -tr ' + str(newResolutionWidth) + ' ' + str(newResolutionHeight) + ' -of GTiff ' + demPath + ' ' + intermediateResultsFolderName + 'rasterized.tif -wo CUTLINE_ALL_TOUCHED=TRUE -te ' + str(left) + ' ' + str(bottom) + ' ' + str(right) + ' ' + str(top)#-crop_to_cutline' 
        #rasterized.tif is optional, just to see how the original DEM pixels compare with the down-sampled ones
        os.system(command)
        command = 'gdalwarp -overwrite -q -cutline ' + singleFeatureVectorLayerFileName + ' -tr ' + str(newResolutionWidth) + ' ' + str(newResolutionHeight) + ' -of GTiff ' + intermediateResultsFolderName + 'rasterized.tif ' + intermediateResultsFolderName + 'rasterized2.tif' 
        os.system(command)
        pathToClippedRaster = intermediateResultsFolderName + "rasterized2.tif"
        maskedRaster = gdal.Open(pathToClippedRaster)


        try:

            inputBand = maskedRaster.GetRasterBand(1)
            cols = maskedRaster.RasterXSize
            rows = maskedRaster.RasterYSize       
            data = inputBand.ReadAsArray(0, 0, cols, rows)

            #Sort all non-nodata pixels and determine the cut-off value:
            pixelList = []

            for col in range (0, cols):
                for row in range (0, rows):
                    if data[row, col] != inputBand.GetNoDataValue():
                        pixelList.append(data[row, col])

            pixelList.sort()
            cutOffValue = pixelList[-len(pixelList)//int(self.ui.getPortionField())] 

            
            for col in range(0, cols):
                for row in range (0, rows):
                    if data[row, col] <= cutOffValue and cutOffValue != pixelList[0]:
                        data[row, col] = inputBand.GetNoDataValue()
                    else: #remove 'else' to keep original raster values
                        data[row, col] = 1

            # Write the raster with N% highest pixels:
            driver = gdal.GetDriverByName("GTiff")
            dataset = driver.Create(intermediateResultsFolderName + 'polygonized.tif', cols, rows, 1, gdal.GDT_Float32, )
            dataset.SetProjection(maskedRaster.GetProjectionRef())
            dataset.SetGeoTransform(maskedRaster.GetGeoTransform())
            dataset.GetRasterBand(1).SetNoDataValue(inputBand.GetNoDataValue())
            dataset.GetRasterBand(1).WriteArray(data)
            dataset.FlushCache()

            # Convert the raster to polygons:
            dst_layername = "polygonized"
            drv = ogr.GetDriverByName("ESRI Shapefile")
            dst_ds = drv.CreateDataSource( intermediateResultsFolderName + "polygonized.shp" )
            proj = osr.SpatialReference()
            proj.ImportFromWkt(landslides.crs().toWkt())
            dst_layer = dst_ds.CreateLayer(dst_layername, srs =  proj )
            gdal.Polygonize( dataset.GetRasterBand(1), dataset.GetRasterBand(1), dst_layer, -1, [], callback=None )  
            #first argument is the input raster, second argument is the mask layer
            dst_ds.Destroy()
            dataset = None
            maskedRaster = None

            # Merge the polygons into a multi-part polygon:
            polygonized = QgsVectorLayer(intermediateResultsFolderName + "polygonized.shp", "polygonized", "ogr")
            multipartFeature = QgsFeature()
            multipartGeometry = QgsGeometry.fromWkt('GEOMETRYCOLLECTION()')
            listOfGeometries = []
            for singleFeature in polygonized.getFeatures():
                 multipartGeometry.addPartGeometry(singleFeature.geometry())

                 singleFeature = None
            multipartFeature.initAttributes(1)
            multipartFeature.setAttribute(0, landslide[self.ui.getSelectedIdField()])
            multipartFeature.setGeometry(QgsGeometry(multipartGeometry))   
            highestPercent.dataProvider().addFeatures([multipartFeature])
            highestPercent.updateExtents()
            highestPercent.updateFields()
    
        except:
            count = 1

        
    highestPercent.commitChanges()
    highestPercent.updateExtents()
    QgsVectorFileWriter.writeAsVectorFormat(highestPercent, self.ui.getOutputField(), "CP1250", None, "ESRI Shapefile")

    #close the window if button pressed:
    super(HighestPercentDialog, self).accept()

  def getOpenMapLayers(self):
      layers = QgsMapLayerRegistry.instance().mapLayers()
      return layers
    
