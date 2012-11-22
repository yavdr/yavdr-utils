#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
import logging

class GraphTFT():
    '''Handle GraphTFT if loaded'''
    hdfpath = 'yavdr.frontend.graphtft'
    viewnormal = 'yavdr.frontend.graphtft.view_normal'
    viewdetached = 'yavdr.frontend.graphtft.view_detached'
    def __init__(self,main_instance):
        self.settings = main_instance.settings
        self.bus = main_instance.systembus
        self.hdf = main_instance.hdf
        self.graphtft = main_instance.vdrCommands.vdrSetup.check_plugin('graphtft')
        self.loadsettings()
        
        
    def loadsettings(self):
        view = self.hdf.readKey(GraphTFT.viewdetached,"NonLiveTv")
        self.hdf.updateKey(GraphTFT.viewdetached,view)
        self.hdf.writeFile()
        
    def graphtft_switch(self):
        if self.graphtft:
            dbusgraph = self.bus.get_object("de.tvdr.vdr","/Plugins/graphtft")
            if self.settings.frontend_active == 0:
               dbusgraph.SVDRPCommand(dbus.String('TVIEW'),dbus.String(self.hdf.readKey(GraphTFT.viewdetached,"NonLiveTv")),dbus_interface='de.tvdr.vdr.plugin')
            elif self.settings.frontend_active == 1:
               dbusgraph.SVDRPCommand(dbus.String('RVIEW'),dbus.String(None),dbus_interface='de.tvdr.vdr.plugin')
