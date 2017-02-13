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
from Ui_AiArea import Ui_AiArea
from glob import glob
from os import path
import numpy
import os
from osgeo import gdal
import osr

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
#from ctypes import size

# create the dialog for inventory queries
class AiAreaDialog(QtGui.QDialog):

  #class variables:
  iface = None

  def __init__(self, interface): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_AiArea ()
    self.ui.setupUi(self)
    self.iface = interface

  #Event handling in case "OK" was pressed
  def accept(self):
    
    #get the shapefile with points:
    epicenters = self.ui.getSelectedCatalogLayer()
    #get the AI formula parameters:
    mIndexText = self.ui.getMIndexField().text()
    if mIndexText == "":
      mIndexText = "1"
    mIndex = float(mIndexText)
    addentText = self.ui.getAddentField().text()
    if addentText == "":
      addentText = "0"
    addent = float(addentText)
    #get the output file:
    outputFileName = self.ui.getOutputField().text()
    
    #determine the extent of the area / of the output file:
    outputRaster = gdal.Open(outputFileName)
    sizeX = outputRaster.RasterXSize
    sizeY = outputRaster.RasterYSize
    originX = outputRaster.GetGeoTransform()[0]
    originY = outputRaster.GetGeoTransform()[3]
    cellSizeX = outputRaster.GetGeoTransform()[1]
    cellSizeY = outputRaster.GetGeoTransform()[5]
    
    matrix = [[0 for x in xrange(sizeY)] for x in xrange(sizeX)]

    
    #iterate over all earthquakes:
    for epicenter in epicenters.getFeatures():
        magnitude = epicenter[self.ui.getSelectedMagnitudeField()]
        pointX = epicenter.geometry().asPoint().x()
        pointY = epicenter.geometry().asPoint().y()

        logR = mIndex * magnitude + addent
        radius = 10 ** logR # in kilometers
        
        pointIndexX = int(self.getCellIndexX(pointX, originX, cellSizeX))
        pointIndexY = int(self.getCellIndexY(pointY, originY, cellSizeY))
        
        limitWest = pointIndexX
        limitEast = pointIndexX
        limitSouth = pointIndexY
        limitNorth = pointIndexY
        
        # iterate to the west:
        xWest = pointIndexX - 1
        yWest = pointIndexY
        iterateWest = True
        while xWest >= 0 and xWest < sizeX and iterateWest == True:
            cellCenterX = self.getCellCenterX(xWest, originX, cellSizeX)
            cellCenterY = self.getCellCenterY(yWest, originY, cellSizeY)
            sqd = (pointX - cellCenterX)**2 + (pointY - cellCenterY)**2
            distance = sqd**0.5
            if distance <= radius * 1000:
                limitWest = xWest
                xWest = xWest - 1
            else:
                iterateWest = False
        
        #iterate to the east:
        xEast = pointIndexX + 1
        yEast = pointIndexY
        iterateEast = True
        while xEast >=0 and xEast < sizeX and iterateEast  == True:
            cellCenterX = self.getCellCenterX(xEast, originX, cellSizeX)
            cellCenterY = self.getCellCenterY(yEast, originY, cellSizeY)
            sqd = (pointX - cellCenterX)**2 + (pointY - cellCenterY)**2
            distance = sqd ** 0.5
            if distance <= radius * 1000:
                limitEast = xEast
                xEast = xEast + 1
            else:
                iterateEast = False
                
        #iterate to the south:
        xSouth = pointIndexX
        ySouth = pointIndexY - 1
        iterateSouth = True
        while ySouth >= 0 and ySouth < sizeY and iterateSouth == True:
            cellCenterX = self.getCellCenterX(xSouth, originX, cellSizeX)
            cellCenterY = self.getCellCenterY(ySouth, originY, cellSizeY)
            sqd = (pointX - cellCenterX)**2 + (pointY - cellCenterY)**2
            distance = sqd ** 0.5
            if distance <= radius * 1000:
                limitSouth = ySouth
                ySouth = ySouth - 1
            else:
                iterateSouth = False
        
        #iterate to the north:
        xNorth = pointIndexX
        yNorth = pointIndexY + 1
        iterateNorth = True
        while yNorth >= 0 and yNorth < sizeY and iterateNorth == True:
            cellCenterX = self.getCellCenterX(xNorth, originX, cellSizeX)
            cellCenterY = self.getCellCenterY(yNorth, originY, cellSizeY)
            sqd = (pointX - cellCenterX)**2 + (pointY - cellCenterY)**2
            distance = sqd ** 0.5
            if distance <= radius * 1000:
                limitNorth = yNorth
                yNorth = yNorth + 1
            else:
                iterateNorth = False
        
        #iterate diagonally:
        for i in range(limitWest, limitEast):
            for j in range(limitSouth, limitNorth):
                    #if j != pointIndexY:
	      cellCenterX = self.getCellCenterX(i, originX, cellSizeX)
              cellCenterY = self.getCellCenterY(j, originY, cellSizeY)
              sqd = (pointX - cellCenterX)**2 + (pointY - cellCenterY)**2
              distance = sqd ** 0.5
              if distance <= radius * 1000:
		matrix[i][j] = matrix[i][j] + 1
           
    #write array to a tif file:
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(outputFileName, sizeX, sizeY, 1, gdal.GDT_Float32, )
    dataset.SetGeoTransform((originX, cellSizeX, 0, originY, 0, cellSizeY))
    dataset.SetProjection(outputRaster.GetProjectionRef())
        
    transposed = zip(*matrix)
    array = numpy.array(transposed)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.FlushCache()

    #close the window if button pressed:
    super(AiAreaDialog, self).accept()
    
    
  def getCellIndexX(self, xCoord, originX, cellSizeX):
    pointIndexX = (xCoord - originX) // cellSizeX
    return pointIndexX

  def getCellIndexY(self, yCoord, originY, cellSizeY):
    pointIndexY = (yCoord - originY) // cellSizeY
    return pointIndexY

  def getCellCenterX(self, indexX, originX, cellSizeX):
    x = indexX * cellSizeX + originX + (cellSizeX / 2)
    return x

  def getCellCenterY(self, indexY, originY, cellSizeY):
    y = indexY * cellSizeY + originY + (cellSizeY / 2)
    return y
    
  def getOpenMapLayers(self):
      layers = QgsMapLayerRegistry.instance().mapLayers()
      return layers
    
