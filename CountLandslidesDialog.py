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
from Ui_CountLandslides import Ui_CountLandslides
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
class CountLandslidesDialog(QtGui.QDialog):
  
  def __init__(self): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_CountLandslides ()
    self.ui.setupUi(self)

  #Event handling in case "OK" was pressed
  def accept(self):
    
    highestPoints = self.ui.getSelectedHighestPointsLayer()
    mappingUnits = self.ui.getSelectedMappingUnitsLayer()
    
    mappingUnits.startEditing()
        
    # add a "count" field if it does not exist yet:
    countFieldFound = 0
    fieldIndex = -1
    for field in mappingUnits.dataProvider().fields():
      fieldIndex = fieldIndex + 1
      if field.name() == "count":
	countFieldFound = 1
    if countFieldFound == 0: # if the layer has no "count" field
      mappingUnits.dataProvider().addAttributes([ QgsField("count",  QVariant.Int)])
      mappingUnits.commitChanges()
      mappingUnits.startEditing()
      fieldIndex = fieldIndex + 1
    
    # count how many highest points are in each mapping unit:
    for mappingUnit in mappingUnits.getFeatures():
      countValue = 0
      for highestPoint in highestPoints.getFeatures():
	if mappingUnit.geometry().contains(highestPoint.geometry()):
	  countValue = countValue + 1
      mappingUnits.changeAttributeValue(mappingUnit.id(), fieldIndex, countValue)
                
    mappingUnits.commitChanges()     
    mappingUnits.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(mappingUnits)
    
    #close the window if button pressed:
    super(CountLandslidesDialog, self).accept()

    
  def getOpenMapLayers(self):
      layers = QgsMapLayerRegistry.instance().mapLayers()
      return layers
    
