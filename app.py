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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
from PyQt4 import QtCore, QtGui
# Initialize Qt resources from file resources.py
import resources
import tempfile


# Import the code for the dialog
from CountLandslidesDialog import CountLandslidesDialog
from HighestPointsDialog import HighestPointsDialog
from HighestPercentDialog import HighestPercentDialog
from PolygonLengthDialog import PolygonLengthDialog
from PolygonWidthDialog import PolygonWidthDialog
from ResampleModisDialog import ResampleModisDialog
from AiAreaDialog import AiAreaDialog

class App: 
    
  #constants:
  PATH_TO_TEMP_FOLDER = tempfile.gettempdir()

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface

  def initGui(self):  
            
    #Count landslides action:
    self.countLandslidesAction = QAction(QIcon(), \
        "Count landslide events", self.iface.mainWindow())
    QObject.connect(self.countLandslidesAction, SIGNAL("activated()"), self.runCountLandslides)
    
    #Highest points action:
    self.highestPointsAction = QAction(QIcon(), \
        "Highest points", self.iface.mainWindow())
    QObject.connect(self.highestPointsAction, SIGNAL("activated()"), self.runHighestPoints)

	#Highest percent action:
    self.highestPercentAction = QAction(QIcon(), \
        "Highest N percent", self.iface.mainWindow())
    QObject.connect(self.highestPercentAction, SIGNAL("activated()"), self.runHighestPercent)
    
    #Polygon length action:
    self.polygonLengthAction = QAction(QIcon(), \
        "Polygon length", self.iface.mainWindow())
    QObject.connect(self.polygonLengthAction, SIGNAL("activated()"), self.runPolygonLength)
    
    #Polygon width action:
    self.polygonWidthAction = QAction(QIcon(), \
        "Polygon width", self.iface.mainWindow())
    QObject.connect(self.polygonWidthAction, SIGNAL("activated()"), self.runPolygonWidth)
    
    #Resample MODIS action:
    self.resampleModisAction = QAction(QIcon(), \
        "Zonal statistics for MODIS", self.iface.mainWindow())
    QObject.connect(self.resampleModisAction, SIGNAL("activated()"), self.runResampleModis) 
    
    #AI area action:
    self.aiAreaAction = QAction(QIcon(), \
        "Calculate Arias intensity for study area", self.iface.mainWindow())
    QObject.connect(self.aiAreaAction, SIGNAL("activated()"), self.runAiArea) 

    self.iface.addPluginToMenu("Landslide Tools", self.countLandslidesAction)
    self.iface.addPluginToMenu("Landslide Tools", self.highestPointsAction)
    self.iface.addPluginToMenu("Landslide Tools", self.highestPercentAction)
    self.iface.addPluginToMenu("Landslide Tools", self.polygonLengthAction)
    self.iface.addPluginToMenu("Landslide Tools", self.polygonWidthAction)
    self.iface.addPluginToMenu("Landslide Tools", self.resampleModisAction)
    self.iface.addPluginToMenu("Landslide Tools", self.aiAreaAction)

  def unload(self):
    # Remove the plugin menu item and icon
    self.iface.removePluginMenu("Landslide Tools",self.countLandslidesAction)
    self.iface.removePluginMenu("Landslide Tools", self.highestPointsAction)
    self.iface.removePluginMenu("Landslide Tools",self.highestPercentAction)
    self.iface.removePluginMenu("Landslide Tools", self.polygonLengthAction)
    self.iface.removePluginMenu("Landslide Tools", self.polygonWidthAction)
    self.iface.removePluginMenu("Landslide Tools", self.resampleModisAction)
    self.iface.removePluginMenu("Landslide Tools", self.aiAreaAction)


    
  #run method to calculate landslide area for each mapping unit:
  def runCountLandslides(self):
    dlg = CountLandslidesDialog()
    #show the dialog
    dlg.show()
    result = dlg.exec_()
    
    # See if OK was pressed
    if result == 1: 
      pass   
        
      
  #run method to calculate landslide highest points:
  def runHighestPoints(self):
    dlg = HighestPointsDialog(self.iface, self.PATH_TO_TEMP_FOLDER)
    #show the dialog
    dlg.show()
    result = dlg.exec_()
    
    # See if OK was pressed
    if result == 1: 
      pass   

  #run method to calculate the top N percent of a landslide:
  def runHighestPercent(self):
    dlg = HighestPercentDialog(self.iface, self.PATH_TO_TEMP_FOLDER)
    #show the dialog
    dlg.show()
    result = dlg.exec_()
    
    # See if OK was pressed
    if result == 1: 
      pass  
  
  #run method to calculate polygon length:
  def runPolygonLength(self):
    dlg = PolygonLengthDialog(self.iface, self.PATH_TO_TEMP_FOLDER)
    #show the dialog
    dlg.show()
    result = dlg.exec_()
    
    # See if OK was pressed
    if result == 1: 
      pass 

  #run method to calculate polygon width:
  def runPolygonWidth(self):
    dlg = PolygonWidthDialog(self.iface)
    #show the dialog
    dlg.show()
    result = dlg.exec_()
    
    # See if OK was pressed
    if result == 1: 
      pass 



  #run method for resample MODIS dialog:
  def runResampleModis(self):
      dlg = ResampleModisDialog(self.iface)
      dlg.show()
      result = dlg.exec_()
      if result == 1:
          pass
      
  #run method for AI area dialog:
  def runAiArea(self):
      dlg = AiAreaDialog(self.iface)
      dlg.show()
      result = dlg.exec_()
      if result == 1:
          pass 
      
