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

    #1. Find self-tangent polygons:
    for landslide in landslides.getFeatures():
       isMultipart = False
       geom = landslide.geometry()
       if geom.isMultipart():
          parts = geom.asMultiPolygon()
          isMultipart = True
       else:
          parts = [ geom.asPolygon() ]
       allRings = [] #will be used in step 2
       for part in parts:
          for ring in part:
             allRings.append(ring) #will be used in step 2
             coordinatePairs = [] # list with all coordinate pairs of a ring
             for i in range (0, len(ring)-1): #-1 because the first and last vertex are the same
                vertex = ring[i]
                found = False
                for coordPair in coordinatePairs:
                   if vertex[0] == coordPair[0] and vertex[1] == coordPair[1]:
                      found = True
                      indexPrev = (i + len(ring)-1 - 1) % (len(ring)-1) #index of the previous vertex
                      indexNext = (i + len(ring)-1 + 1) % (len(ring)-1) #index of the next vertex
                      vertexPrev = ring[indexPrev]
                      vertexNext = ring[indexNext]
                      if vertexPrev[0] + vertexNext[0] - 2 * vertex[0] > 0:
                         vertex.setX(vertex[0] + 0.1)
                      else:
                         vertex.setX(vertex[0] - 0.1)
                      if vertexPrev[1] + vertexNext[1] - 2 * vertex[1] > 0:
                         vertex.setY(vertex[1] + 0.1)
                      else: 
                         vertex.setY(vertex[1] - 0.1)                      
                      
                if found == False:
                   coordinatePairs.append(vertex)


       #2. Correct interior rings that touch exterior rings:
       for ring1 in allRings:
          for ring2 in allRings:
             if ring1 is not ring2:
                found = False 
                #records if a common point has already been found. Points are moved starting from the second
                for i1 in range (0, len(ring1)-1): #-1 because the first and last vertex are the same
                   for i2 in range(0, len(ring2)-1) :
                      vertex1 = ring1[i1]
                      vertex2 = ring2[i2]
                      if vertex1[0] == vertex2[0] and vertex1[1] == vertex2[1]:
                         vertexPrev1 = ring1[(i1 + len(ring1)-1 - 1) % (len(ring1) - 1)]
                         vertexPrev2 = ring2[(i2 + len(ring2)-1 - 1) % (len(ring2) - 1)]
                         vertexNext1 = ring1[(i1 + len(ring1)-1 + 1) % (len(ring1) - 1)]
                         vertexNext2 = ring2[(i2 + len(ring2)-1 + 1) % (len(ring2) - 1)]
                         if (vertexPrev1[0]!=vertexPrev2[0] and vertexPrev1[1]!=vertexPrev2[1] and vertexNext1[0]!=vertexNext2[0] and vertexNext1[1]!=vertexNext2[1]) or (vertexPrev1[0]!=vertexNext2[0] and vertexPrev1[1]!=vertexNext2[1] and vertexNext1[0]!=vertexPrev2[0] and vertexNext1[1]!=vertexPrev2[1]):
                            #if we are here, then two rings touch only in one point
                            if found:
                               if vertexPrev1[0] + vertexNext1[0] - 2 * vertex1[0] > 0:
                                  vertex1.setX(vertex1[0] + 0.1)
                               else:
                                  vertex1.setX(vertex1[0] - 0.1)
                               if vertexPrev1[1] + vertexNext1[1] - 2 * vertex1[1] > 0:
                                  vertex1.setY(vertex1[1] + 0.1)
                               else: 
                                  vertex1.setY(vertex1[1] - 0.1)
                            else: #if this is only the first common point found:
                               found = True

       # Now save the resulting polygon in the new layer:
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
