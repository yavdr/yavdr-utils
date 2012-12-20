#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
import wnck
import gtk
import time
import logging

class wnckController():
    def __init__(self,main_instance):
        self.main_instance = main_instance
        self.settings = main_instance.settings
        self.windows = {
        'frontend':None,
        'softhddevice_pip':None,
        'xbmc':None
        }
        self.windownames = [
            'softhddevice','VDR',
            'Connecting to VDR ...',
            #'VDR - 127.0.0.1',
            'xine',
            'xine: vdr:/tmp/vdr-xine/stream#demux:mpeg_pes',
            'Geany','XBMC Media Center',
            'YouTube TV']
        self.screen = wnck.screen_get_default()
        self.screen.connect("window-opened", self.on_window_opened)
        self.screen.connect('window-closed', self.on_window_closed)

        self.screen_height = self.screen.get_height()
        self.screen_width = self.screen.get_width()

    def on_window_opened(self,screen,window):
        gtk.main_iteration()
        wname = window.get_name()
        logging.debug("new Window %s"%wname)
        window.connect('name-changed', self.window_name_changed)
        self.window_name_changed(window)


    def window_name_changed(self, window):
        wname = window.get_name()
        logging.debug('window_name_changed: %s'%wname)
        if wname in self.windownames:
            logging.info('wname in windownames')
            if wname == 'softhddevice' or ('VDR' in wname) or ('xine' in wname) or ('Connecting' in wname):
                if self.windows['frontend'] == None:
                    logging.debug("assigning new main window")
                    self.windows['frontend'] = window
                    self.maximize_and_undecorate(window)
                    #window.connect('geometry-changed', self.on_window_geochanged)
                elif self.windows['softhddevice_pip'] == None and self.windows['frontend'].get_xid() != window.get_xid():
                    logging.debug("softhddevice_pip")
                    self.windows['softhddevice_pip'] = window
                    self.resize(window,1200,795,720,405,1,0)
                elif window.get_xid() == self.windows['frontend'].get_xid():
                    logging.debug("main window already defined")
                else:
                    logging.debug("too many softhddevice windows!")
                
            elif wname == 'XBMC Media Center':
                logging.info("Detected XBMC Media Center")
                try:
                    gdkwindow = gtk.gdk.window_foreign_new(window.get_xid())
                    gdkwindow.set_icon_list([gtk.gdk.pixbuf_new_from_file('/usr/share/icons/hicolor/48x48/apps/xbmc.png')])
                    if not window.is_fullscreen():
                        logging.debug("no fullscreen - maximizing and undecorating")
                        window.set_fullscreen(0)
                        window.maximize()
                        #gdkwindow.set_decorations(0)
                        #window.make_below()
                        window.unmake_above()
                except: logging.exception('XBMC window not changable')
                
            elif wname in self.windownames:
                self.maximize_and_undecorate(window)

    def maximize_and_undecorate(self,window):
        logging.debug("Window recognized: %s"%window.get_name())
        logging.debug("Window is fullscreen: %s"%window.is_fullscreen())
        logging.debug("Window is maximized: %s"%window.is_maximized())
        gdkwindow = gtk.gdk.window_foreign_new(window.get_xid())
        gdkwindow.set_decorations(0)
        if window.is_fullscreen():
            logging.debug("set to maximized view")
            window.set_fullscreen(0)
            window.maximize()
        if not window.is_maximized():
            window.maximize()
        window.activate(int(time.strftime("%s",time.gmtime())))

        gdkwindow.set_icon_list([gtk.gdk.pixbuf_new_from_file('/usr/share/icons/xineliboutput-sxfe.svg')])

    def resize(self,window,x=0,y=0,w=1280,h=720,above=0,d=0):
        logging.debug("run resize")
        if window != None:
            if window.is_fullscreen():
                window.set_fullscreen(0)
            if window.is_maximized():
                window.unmaximize()
            if above == 1:
                window.make_above()
            else:
                window.unmake_above()
            window.set_geometry(0,255,x,y,w,h)
            gdkwindow = gtk.gdk.window_foreign_new(window.get_xid())
            gdkwindow.set_decorations(d)
        self.main_instance.adeskbar.hide()

    def on_window_geochanged(self,window):
        logging.debug("Window Geometry changed")
        logging.debug(window.get_name())
        gdkwindow = gtk.gdk.window_foreign_new(window.get_xid())
        if window.is_fullscreen():
            logging.debug("window is fullscreen")
            window.set_fullscreen(0)
            window.maximize()
            gdkwindow.set_decorations(0)
        elif window.is_maximized():
            logging.debug("window maximized")
            gdkwindow.set_decorations(0)
            #window.set_fullscreen(1)
        elif not window.is_maximized():
            logging.debug("window not maximized")
            #gdkwindow.set_decorations(1)

    def on_window_closed(self,screen,window):
        logging.debug("Closed Window %s:"%(window.get_name()))
        if window in self.windows.itervalues():
            WindowKey = [key for key, value in self.windows.iteritems() if value == window][0]
            print WindowKey
            self.windows[WindowKey] = None
