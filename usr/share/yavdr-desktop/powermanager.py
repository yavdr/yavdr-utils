#!/usr/bin/python
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

# dbus
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import logging

class PowerManager():
    def __init__(self,bus):
        self.bus = bus
        self.interface_ck = 'org.freedesktop.ConsoleKit.Manager'
        self.interface_up = 'org.freedesktop.UPower'
        self.ck = bus.get_object("org.freedesktop.ConsoleKit","/org/freedesktop/ConsoleKit/Manager")
        #self.up = bus.get_object("org.freedesktop.UPower","/org/freedesktop/UPower")
        
    def restart(self):
        logging.info('Reboot')
        try:
            answer = self.ck.Restart(dbus_interface=self.interface_ck)
            logging.debug(answer)
            return answer
        except:
            logging.exception('Reboot failed')
            return False
        
        
        
    def halt(self):
        self.ck.Shutdown(dbus_interface=self.interface_ck)
        
    #def suspend(self):
    #    self.up.Suspend(dbus_interface=self.interface_up)
