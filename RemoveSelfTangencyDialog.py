"""
/***************************************************************************
Name		         : LandslideTools plugin
Description          : Spatial funtionality for landslide studies
copyright            : GNU General Public License
author		         : Darya Golovko
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
from Ui_RemoveSelfTangency import Ui_RemoveSelfTangency
from glob import glob
from os import path
import numpy
import os
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import shutil
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


# create the dialog for inventory queries
class RemoveSelfTangencyDialog(QtGui.QDialog):
  
  def __init__(self): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_RemoveSelfTangency ()
    self.ui.setupUi(self)

  #Event handling in case "OK" was pressed
  def accept(self):
    
    landslides = self.ui.getSelectedPolygonLayer()
    if landslides == None or landslides.geometryType() != 2: # stands for PolygonGeometry
       return
    
    resultLayer = QgsVectorLayer("Polygon?crs=" + landslides.crs().toWkt(), "Result layer", "memory")
    resultLayer.startEditing()
    resultLayer.dataProvider().addAttributes(landslides.dataProvider().fields())
    resultLayer.updateFields()

    #find self-tangent polygons:
    for landslide in landslides.getFeatures():
       isMultipart = False
       geom = landslide.geometry()
       if geom.isMultipart():
          parts = geom.asMultiPolygon()
          isMultipart = True
       else:
          parts = [ geom.asPolygon() ]
       for part in parts:
          for ring in part:
             coordinatePairs = [] # list with all coordinate pairs of a ring
             for i in range (0, len(ring)-1): #-1 because the first and last vertex are the same
                vertex = ring[i]
                found = False
                for coordPair in coordinatePairs:
                   if vertex[0] == coordPair[0] and vertex[1] == coordPair[1]:
                      QgsMessageLog.logMessage("found", 'Landslide Tools')
                      found = True
                      indexPrev = (i + len(ring)-1 - 1) % (len(ring)-1) #index of the previous vertex
                      indexNext = (i + len(ring)-1 + 1) % (len(ring)-1) #index of the next vertex
                      vertexPrev = ring[indexPrev]
                      vertexNext = ring[indexNext]
                      QgsMessageLog.logMessage('this: ' + str(vertex[0]) + " " + str(vertex[1])+ ';   prev: ' + str(vertexPrev[0]) + " " + str(vertexPrev[1]) + ';   next: ' + str(vertexNext[0]) + " " + str(vertexNext[1]), 'Landslide Tools')
                      if vertexPrev[0] + vertexNext[0] - 2 * vertex[0] > 0:
                         vertex.setX(vertex[0] + 0.1)
                      else:
                         vertex.setX(vertex[0] - 0.1)
                      if vertexPrev[1] + vertexNext[1] - 2 * vertex[1] > 0:
                         vertex.setY(vertex[1] + 0.1)
                      else: 
                         vertex.setY(vertex[1] - 0.1)
                      QgsMessageLog.logMessage('this: ' + str(part[0][i][0]) + " " + str(part[0][i][1])+ ';   prev: ' + str(vertexPrev[0]) + " " + str(vertexPrev[1]) + ';   next: ' + str(vertexNext[0]) + " " + str(vertexNext[1]), 'Landslide Tools')


                      
                if found == False:
                   coordinatePairs.append(vertex)


       if isMultipart:
          newGeometry = QgsGeometry.fromMultiPolygon(parts)
       else:
          newGeometry = QgsGeometry.fromPolygon(parts[0])
       newFeature = QgsFeature()
       newFeature.setAttributes(landslide.attributes())
       newFeature.setGeometry(newGeometry)
       resultLayer.dataProvider().addFeatures([newFeature])



#https://gis.stackexchange.com/questions/182121/counting-number-of-vertices-of-object-on-vector-layer-pyqgis?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    
    resultLayer.commitChanges()
    resultLayer.updateExtents()
    
    QgsMapLayerRegistry.instance().addMapLayer(resultLayer)
    
    #close the window if button pressed:
    super(RemoveSelfTangencyDialog, self).accept()

    
  def getOpenMapLayers(self):
      layers = QgsMapLayerRegistry.instance().mapLayers()
      return layers
    
  #def getVertices()
