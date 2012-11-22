#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import gobject
import logging
import socket
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class adeskbarDBus():
    '''wrapper for adeskbar'''
    def __init__(self,sbus):
        #self.adeskbar = sbus.get_object("com.adcomp.adeskbar","/Control")
        #self.interface = 'com.adcomp.adeskbar'
        pass

    def hide(self):
        #answer = self.adeskbar.hide(dbus_interface=self.interface)
        return False
