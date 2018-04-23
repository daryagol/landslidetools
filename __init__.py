# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Zoomer
                                 A QGIS plugin
 Zoomer
                             -------------------
        begin                : 2013-11-23
        copyright            : (C) 2013 by darya
        email                : dgolovko@gfz-potsdam.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    from app import App
    return App(iface)
