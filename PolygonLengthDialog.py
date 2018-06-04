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
from Ui_PolygonLength import Ui_PolygonLength
from glob import glob
from os import path
import numpy
import os
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import osr
import shutil
import time
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# create the dialog for inventory queries
class PolygonLengthDialog(QtGui.QDialog):

  #class variables:
  iface = None
  pathToTempFolder = None
  
  def __init__(self, interface, path): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_PolygonLength ()
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
    lowestPoints = QgsVectorLayer("Point?crs=" + landslides.crs().toWkt(), "Lowest points", "memory")
    lengthLines = QgsVectorLayer("LineString?crs=" + landslides.crs().toWkt(), "Length lines", "memory")
    highestPoints.startEditing()
    highestPoints.dataProvider().addAttributes([QgsField(self.ui.getSelectedIdField(), QVariant.String)])
    highestPoints.updateFields()
    lowestPoints.startEditing()
    lowestPoints.dataProvider().addAttributes([QgsField(self.ui.getSelectedIdField(), QVariant.String)])
    lowestPoints.updateExtents()
    lengthLines.startEditing()
    lengthLines.dataProvider().addAttributes([QgsField(self.ui.getSelectedIdField(), QVariant.String), QgsField("length", QVariant.Double)])
    lengthLines.updateFields()
    
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

        command = 'gdalwarp -overwrite -q -cutline ' + singleFeatureVectorLayerFileName + ' -tr ' + str(demPixelWidth) + ' ' + str(demPixelHeight) + ' -of GTiff ' + demPath + ' ' + intermediateResultsFolderName + 'rasterized.tif -wo CUTLINE_ALL_TOUCHED=TRUE -te ' + str(left) + ' ' + str(bottom) + ' ' + str(right) + ' ' + str(top)# -crop_to_cutline' 
        os.system(command)

        pathToClippedRaster = intermediateResultsFolderName + "rasterized.tif"
        maskedRaster = gdal.Open(pathToClippedRaster)

        #try:
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
        minHeight = 10000
        maxHeightIndices = [0.0, 0.0] 
        minHeightIndices = [0.0, 0.0]
        
        for col in range(0, cols):
           for row in range(0, rows):
              if data[row, col] != inputBand.GetNoDataValue():
                 pixelCenterX = originX + col * pixelWidth + 0.5 * pixelWidth
                 pixelCenterY = originY + row * pixelHeight - 0.5 * pixelWidth
                 demXOffset = int((pixelCenterX - demOriginX) / demPixelWidth)
                 demYOffset = int((pixelCenterY - demOriginY) / demPixelHeight)
                 heightValue = demBand.ReadAsArray(demXOffset, demYOffset, 1, 1)
                 if heightValue > maxHeight:
                    maxHeight = heightValue
                    maxHeightIndices = [pixelCenterX, pixelCenterY]
                 if heightValue < minHeight:
                    minHeight = heightValue
                    minHeightIndices = [pixelCenterX, pixelCenterY]
        
        highestPoint = None
        lowestPoint = None
        lengthLine = None
        if maxHeight != -1:     
           # create the highest point from highest pixel:
           highestPoint = self.createPointFromPixel(maxHeightIndices[0], maxHeightIndices[1], pixelWidth, pixelHeight, landslide)
           highestPointFeature = QgsFeature()
           highestPointFeature.setGeometry(highestPoint)
           highestPointFeature.initAttributes(1)
           highestPointFeature.setAttribute(0, landslide[self.ui.getSelectedIdField()])
           highestPoints.dataProvider().addFeatures([highestPointFeature])

        if minHeight != 10000:
           # create the lowest point from lowest pixel:
           lowestPoint = self.createPointFromPixel(minHeightIndices[0], minHeightIndices[1], pixelWidth, pixelHeight, landslide)
           lowestPointFeature = QgsFeature()
           lowestPointFeature.setGeometry(lowestPoint)
           lowestPointFeature.initAttributes(1)
           lowestPointFeature.setAttribute(0, landslide[self.ui.getSelectedIdField()])
           lowestPoints.dataProvider().addFeatures([lowestPointFeature])
            
        if highestPoint is not None and lowestPoint is not None:
           #initialSegment = QgsGeometry.fromPolyline([highestPoint, lowestPoint])
           finalListOfPoints = self.processSegment(landslide, highestPoint.asPoint(), lowestPoint.asPoint())
           finalResultSegment = QgsGeometry.fromPolyline(finalListOfPoints)
           # temporary length lines, later to be substituted by lengthLine method result
           lengthLine = QgsFeature()  
           lengthLine.setGeometry(finalResultSegment)
           lengthLine.initAttributes(2)
           lengthLine.setAttribute(0, landslide[self.ui.getSelectedIdField()])
           lengthLine.setAttribute(1, landslide.geometry().length())
           lengthLines.dataProvider().addFeatures([lengthLine])

        #except:
        #    count = 1
        
    singleFeatureVectorLayer = None
    singleFeatureVectorLayerFileName = None
    fet = None
    command = None
    pathToClippedRaster = None
    maskedRaster = None
    inputBand = None
    data = None
     
    highestPoints.commitChanges()
    lowestPoints.commitChanges()
    lengthLines.commitChanges()
    highestPoints.updateExtents()
    lowestPoints.updateExtents()
    lengthLines.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(highestPoints)
    QgsMapLayerRegistry.instance().addMapLayer(lowestPoints)
    QgsMapLayerRegistry.instance().addMapLayer(lengthLines)
    
    #close the window if button pressed:
    super(PolygonLengthDialog, self).accept()

    
  def processSegment(self, lsPolygon, startPoint, endPoint):
      # 1) find the outline of the landslide polygon:     
      lsPolygonWkt = lsPolygon.geometry().exportToWkt()
      polygonOgr = ogr.CreateGeometryFromWkt(lsPolygonWkt)
      polygonOgrRing = polygonOgr.GetGeometryRef(0)
      polygonOgrRingWkt = polygonOgrRing.ExportToWkt()
      polygonOgrLinestringWkt = polygonOgrRingWkt.replace("LINEARRING", "LINESTRING")
      lsOutline = ogr.CreateGeometryFromWkt(polygonOgrLinestringWkt)

      # 2) create segment from startPoint and endPoint, and count how many times it crosses the polygon outline:
      seg = QgsGeometry.fromPolyline([startPoint, endPoint])
      segOgr = ogr.CreateGeometryFromWkt(seg.exportToWkt())
      intersectionsOgr = segOgr.Intersection(lsOutline)
      numberOfIntersections = 0
      if seg.intersects(QgsGeometry.fromWkt(polygonOgrLinestringWkt)):
          numberOfIntersections = intersectionsOgr.GetGeometryCount()
          intersections = seg.intersection(QgsGeometry.fromWkt(polygonOgrLinestringWkt))
          if not intersections.isMultipart():
              numberOfIntersections = 1
                     
      # 3) count the "extra" units in case the highest and lowest points lie outside of the landslide polygon:
      allowedNumberOfIntersections = 0
      if not lsPolygon.geometry().contains(startPoint):
          allowedNumberOfIntersections = allowedNumberOfIntersections + 1
      if not lsPolygon.geometry().contains(endPoint):
          allowedNumberOfIntersections = allowedNumberOfIntersections + 1
          
      # 4) if there are too many intersections, split the line:
      # solution from https://www.easycalculation.com/analytical/perpendicular-bisector-line.php
      if numberOfIntersections > allowedNumberOfIntersections or not lsPolygon.geometry().contains(QgsPoint((startPoint.x() + endPoint.x()) / 2, (startPoint.y() + endPoint.y()) / 2)):
          #construct the perpendicular bisector:	
          perpendicularBisector = self.getPerpendicularBisector(startPoint, endPoint)
          
          # 4e: find an intersection of the perpendicular bisector with the landslide polygon:
          intersectingSegment = None
          intersectionResult = perpendicularBisector.intersection(lsPolygon.geometry())
          
          if intersectionResult.isMultipart():
              multipleIntersectingSegments = intersectionResult.asGeometryCollection()
              minArea = sys.float_info.max
              for i in range(len(multipleIntersectingSegments)):
                  currentSegment = multipleIntersectingSegments[i]
                  xCurrentSegmentMid = (currentSegment.asPolyline()[0].x() + currentSegment.asPolyline()[1].x()) / 2
                  yCurrentSegmentMid = (currentSegment.asPolyline()[0].y() + currentSegment.asPolyline()[1].y()) / 2
                  
                  currentTriangle = QgsGeometry.fromPolygon([[startPoint, endPoint, QgsPoint(xCurrentSegmentMid, yCurrentSegmentMid)]])
                  if currentTriangle.area() < minArea:
                      minArea = currentTriangle.area()
                      intersectingSegment = currentSegment
                      

                  
          else: #if intersection result is singlepart
              intersectingSegment = intersectionResult
 
          
          xIntersectingSegmentMid = (intersectingSegment.asPolyline()[0].x() + intersectingSegment.asPolyline()[1].x()) / 2
          yIntersectingSegmentMid = (intersectingSegment.asPolyline()[0].y() + intersectingSegment.asPolyline()[1].y()) / 2
          
          #temporal adding a new point layer to the map:
          intersectingSegmentMid = QgsFeature()
          intersectingSegmentMid.setGeometry(QgsGeometry.fromPoint(QgsPoint(xIntersectingSegmentMid, yIntersectingSegmentMid)))
          
          # 4f: add a new point to the initialSegment         
          listOfPoints = []
          listOfPoints.append(startPoint)
          if ((startPoint.x()-xIntersectingSegmentMid)*(startPoint.x()-xIntersectingSegmentMid) + (startPoint.y()-yIntersectingSegmentMid)*(startPoint.y()-yIntersectingSegmentMid)) > 10000:
              resultPoints1 = self.processSegment(lsPolygon, startPoint, QgsPoint(xIntersectingSegmentMid, yIntersectingSegmentMid))
              for i in range(1, len(resultPoints1)-1):
                  listOfPoints.append(resultPoints1[i])
          listOfPoints.append(QgsPoint(xIntersectingSegmentMid, yIntersectingSegmentMid))
          if((endPoint.x()-xIntersectingSegmentMid)*(endPoint.x()-xIntersectingSegmentMid) + (endPoint.y()-yIntersectingSegmentMid)*(endPoint.y()-yIntersectingSegmentMid)) > 10000:
              resultPoints2 = self.processSegment(lsPolygon, QgsPoint(xIntersectingSegmentMid, yIntersectingSegmentMid), endPoint)
              for i in range(1, len(resultPoints2)-1):
                  listOfPoints.append(resultPoints2[i])
          listOfPoints.append(endPoint)
          return listOfPoints
                  
      else:
          return [startPoint, endPoint]
                 
                      
  def getPerpendicularBisector(self, startPoint, endPoint):
      # 1) find the middle of the segment, which also lies on the perpendicular bisector:
      xMid = (startPoint.x() + endPoint.x()) / 2
      yMid = (startPoint.y() + endPoint.y()) / 2
      
      # 2) calculate the slope of initial line and handle special cases:
      if startPoint.x()==endPoint.x():
          return QgsGeometry.fromPolyline([QgsPoint(0.0, yMid), QgsPoint(600000.0, yMid)])
      if startPoint.y()==endPoint.y():
          return QgsGeometry.fromPolyline([QgsPoint(xMid, 0.0),	QgsPoint(xMid, 6000000.0)])     
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
    
  # x and y are coordinates of the pixel center, width and height are the pixel dimensions
  # Returns a QgsPoint
  def createPointFromPixel(self, x, y, width, height, landslide):
      # create a polygon from the highest pixel:
      pointLeftDown = QgsPoint(x-width*0.5, y-height*0.5)
      pointLeftUp = QgsPoint(x-width*0.5, y+height*0.5)
      pointRightUp = QgsPoint(x+width*0.5, y+height*0.5)
      pointRightDown = QgsPoint(x+width*0.5, y-height*0.5)
      rubberBand = QgsRubberBand( self.iface.mapCanvas(), QGis.Polygon )
      rubberBand.addPoint(pointLeftDown)
      rubberBand.addPoint(pointLeftUp)
      rubberBand.addPoint(pointRightUp)
      rubberBand.addPoint(pointRightDown)
      pixelPolygonGeom = rubberBand.asGeometry()

      #clip the highest pixel polygon with the landslide extent:
      clippedPolygon = landslide.geometry().intersection(pixelPolygonGeom)
           
      #get the centroid of the clipped polygon:
      centroid = clippedPolygon.centroid()
      return  centroid
              
