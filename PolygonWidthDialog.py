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
from Ui_PolygonWidth import Ui_PolygonWidth
from glob import glob
from os import path
import os
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import shutil
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# create the dialog for inventory queries
class PolygonWidthDialog(QtGui.QDialog):
  
  #class variables:
  iface = None
  
  def __init__(self, interface): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_PolygonWidth ()
    self.ui.setupUi(self)
    self.iface = interface

  #Event handling in case "OK" was pressed
  def accept(self):    

    landslides = self.ui.getSelectedLandslideLayer()
    lengthLines = self.ui.getSelectedLineLayer()
    
    widthLines = QgsVectorLayer("LineString?crs=" + landslides.crs().toWkt(), "Width lines", "memory")
    widthLines.startEditing()
    widthLines.dataProvider().addAttributes([QgsField(self.ui.getSelectedLandslideIdField(), QVariant.String), QgsField("length", QVariant.Double)])
    widthLines.updateFields()
    
    widthStatistics = QgsVectorLayer("LineString?crs=" + landslides.crs().toWkt(), "Width statistics", "memory")
    widthStatistics.startEditing()
    widthStatistics.dataProvider().addAttributes([QgsField(self.ui.getSelectedLandslideIdField(), QVariant.String), QgsField("length", QVariant.Double), QgsField("WidthMedian", QVariant.Double), QgsField("WidthMean", QVariant.Double), QgsField("WidthStdev", QVariant.Double), QgsField("WidthMax", QVariant.Double), QgsField("WidthMin", QVariant.Double), QgsField("WidthCount", QVariant.Double)])
    widthStatistics.updateFields()
        
    for lengthLine in lengthLines.getFeatures():
        
        #find the corresponding landslide polygon:
        currentLandslide = None
        for feature in landslides.dataProvider().getFeatures():
            if feature[self.ui.getSelectedLandslideIdField()] == lengthLine[self.ui.getSelectedLineIdField()]:
                currentLandslide = feature
                break
        
        listOfWidthLines = []
        
        lengthLineGeom = lengthLine.geometry()
        for i in range(len(lengthLineGeom.asPolyline())-1):
            perpendicularBisectorGeom = self.getPerpendicularBisector(lengthLineGeom.asPolyline()[i], lengthLineGeom.asPolyline()[i+1])
            intersection = perpendicularBisectorGeom.intersection(currentLandslide.geometry())       
            listOfWidthLines.append(intersection)
            widthLinesFeature = QgsFeature()            
            widthLinesFeature.setGeometry(intersection)
            widthLinesFeature.initAttributes(2)
            widthLinesFeature.setAttribute(0, currentLandslide[self.ui.getSelectedLandslideIdField()])
            widthLinesFeature.setAttribute(1, lengthLineGeom.length())
            widthLines.dataProvider().addFeatures([widthLinesFeature])
        
        listOfWidthValues = []
        for i in range(len(listOfWidthLines)):
            listOfWidthValues.append(listOfWidthLines[i].length())
        
        widthStatisticsFeature = QgsFeature()
        widthStatisticsFeature.initAttributes(8)
        widthStatisticsFeature.setAttribute(0, currentLandslide[self.ui.getSelectedLandslideIdField()])
        widthStatisticsFeature.setAttribute(1, lengthLine[self.ui.getSelectedLineIdField()])   
        widthMedian = np.median(listOfWidthValues)
        widthStatisticsFeature.setAttribute(2, float(widthMedian))
        widthMean = np.mean(listOfWidthValues)
        widthStatisticsFeature.setAttribute(3, float(widthMean))
        widthStdev = np.std(listOfWidthValues)
        widthStatisticsFeature.setAttribute(4, float(widthStdev))
        widthMax = np.amax(listOfWidthValues)
        widthStatisticsFeature.setAttribute(5, float(widthMax))
        widthMin = np.amin(listOfWidthValues)
        widthStatisticsFeature.setAttribute(6, float(widthMin))
        widthCount = len(listOfWidthLines)
        widthStatisticsFeature.setAttribute(7, widthCount)
            
        widthStatisticsFeature.setGeometry(lengthLineGeom)
        widthStatistics.dataProvider().addFeatures([widthStatisticsFeature])
        

    widthLines.commitChanges()
    widthLines.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(widthLines)
    
    widthStatistics.commitChanges()
    widthStatistics.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(widthStatistics)
    #close the window if button pressed:
    super(PolygonWidthDialog, self).accept()
             
                      
  def getPerpendicularBisector(self, startPoint, endPoint):
      # 1) find the middle of the segment, which also lies on the perpendicular bisector:
      xMid = (startPoint.x() + endPoint.x()) / 2
      yMid = (startPoint.y() + endPoint.y()) / 2
      
      # 2) calculate the slope of initial line and handle special cases:
      if startPoint.x()==endPoint.x():
          return QgsGeometry.fromPolyline([QgsPoint(0.0, yMid), QgsPoint(600000.0, yMid)])
      if startPoint.y()==endPoint.y():
          return QgsGeometry.fromPolyline([QgsPoint(xMid, 0.0), QgsPoint(xMid, 6000000.0)])     
      initialSlope = (endPoint.y() - startPoint.y()) / (endPoint.x() - startPoint.x())    
      # 3) calculate the slope of the perpendicular bisector:
      perpendicularSlope = (-1.0) / initialSlope    
      # 4) find two points on the perpendicular bisector and make a line:
      xMin = 0.0
      yMin = yMid - perpendicularSlope*xMid
      xMax = 600000.0
      yMax = yMid - perpendicularSlope*xMid + perpendicularSlope*xMax       
      # 5) construct the perpendicular bisector:
      perpendicularBisector = QgsGeometry.fromPolyline([QgsPoint(xMin, yMin), QgsPoint(xMax, yMax)])
      return perpendicularBisector
  
    
  def getOpenMapLayers(self):
      layers = QgsMapLayerRegistry.instance().mapLayers()
      return layers
    
