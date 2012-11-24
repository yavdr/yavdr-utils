#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import logging

class vdrDBusCommands():
    def __init__(self,main_instance):
        self.main_instance = main_instance
        self.vdrSetup = dbusVDRSetup(main_instance.systembus)
        self.vdrShutdown = dbusShutdown(main_instance.systembus,main_instance)
        self.vdrRemote = dbusRemote(main_instance.systembus)
        if self.vdrSetup.check_plugin('softhddevice'):
            self.vdrSofthddevice = dbusSofthddeviceFrontend(main_instance,self)
            logging.debug(u'softhddevice has been loaded by VDR')
        else:
            logging.info(u'softhddevice has not been loaded by VDR')

        
class dbusVDRSetup():
    '''wrapper for setup interface provided by the dbus2vdr plugin'''
    def __init__(self,bus):
        self.bus = bus
        self.dbussetup = self.bus.get_object("de.tvdr.vdr","/Setup")
        self.interface = 'de.tvdr.vdr.setup'
        self.get_dbusPlugins()

    def vdrsetupget(self,option):
        value = self.dbussetup.Get(dbus.String(option),dbus_interface=self.interface)
        logging.debug(u"got value %s for setting %s"%(value,option))
        return value

    def get_dbusPlugins(self):
        '''wrapper for dbus plugin list'''
        logging.info(u"asking vdr for plugins")
        dbusplugins = self.bus.get_object("de.tvdr.vdr","/Plugins")
        raw = dbusplugins.List(dbus_interface="de.tvdr.vdr.plugin")
        self.plugins = {}
        for name, version in raw:
            logging.debug(u"found plugin %s %s"%(name,version))
            self.plugins[name]=version
        
    def check_plugin(self,plugin):
        if plugin in self.plugins:
            return True
        else:
            return False


class dbusRemote():
    '''wrapper for remote interface provided by the dbus2vdr plugin'''
    def __init__(self,bus):
        self.dbusremote = bus.get_object("de.tvdr.vdr","/Remote")
        self.interface = 'de.tvdr.vdr.remote'

    def sendkey(self,key):
        answer, message = self.dbusremote.HitKey(dbus.String(key),dbus_interface=self.interface)
        if answer == 250: return True
        else: return False

    def enable(self):
        logging.info('remote enabled')
        answer, message = self.dbusremote.Enable(dbus_interface=self.interface)
        if answer == 250: 
            logging.info('remote enabled')
            return True
        else: return False

    def disable(self):
        answer, message = self.dbusremote.Disable(dbus_interface=self.interface)
        if answer == 250: return True
        else: return False

    def status(self):
        answer, message = self.dbusremote.Status(dbus_interface=self.interface)
        if answer == 250: 
            logging.info('remote disabled')
            return True
        else: return False


class dbusSofthddeviceFrontend():
    '''handler for softhddevice's svdrp plugin command interface provided by the dbus2vdr plugin'''
    def __init__(self,main_instance,parent):
        logging.debug(u"init dbusSofthddeviceFrontend")
        self.main_instance = main_instance
        self.parent = parent
        
        try:
            self.dbusfe = main_instance.systembus.get_object("de.tvdr.vdr","/Plugins/softhddevice")
            self.interface = 'de.tvdr.vdr.plugin'
        except:
            
            logging.exception(u"could not call softhddevice dbus object")

    def activateWindow(self,window):
        window.activate(int(time.strftime("%s",time.gmtime())))
        logging.debug(u"activate softhddevice window with xid ",window.xid())
        
    def status(self):
        code, mode = self.dbusfe.SVDRPCommand(dbus.String("STAT"),dbus.String(None),dbus_interface=self.interface)
        logging.debug("got softhddevice plugin status: %s - %s",code,mode)
        return mode.split()[-1]

    def attach(self):
        logging.debug(u"attaching softhddevice frontend")
        display = u"-d "+self.main_instance.hdf.readKey('yavdr.desktop.display')+".0"
        reply, answer = self.dbusfe.SVDRPCommand(dbus.String("ATTA"),display,dbus_interface=self.interface)
        logging.debug(u"got answer %s: %s",reply,answer)
        self.main_instance.vdrCommands.vdrRemote.enable()
        self.main_instance.settings.frontend_active = 1

    def detach(self,active=0):
        logging.debug(u"detaching softhddevice frontend")
        reply, answer = self.dbusfe.SVDRPCommand(dbus.String("DETA"),dbus.String(None),dbus_interface=self.interface)
        logging.debug(u"got answer %s: %s",reply,answer)
        self.parent.vdrRemote.disable()
        self.main_instance.settings.frontend_active = 0
        if active == 1:
            self.main_instance.settings.frontend_active = 1
            self.main_instance.settings.external_prog = 1
        return True

    def resume(self):
        logging.debug(u"resuming softhddevice frontend")
        if self.status() == 'SUSPENDED':
            reply, answer = self.dbusfe.SVDRPCommand(dbus.String("RESU"),dbus.String(None),dbus_interface=self.interface)
            logging.debug(u"got answer %s: %s",reply,answer)
        else:
            self.attach()
        self.main_instance.settings.frontend_active = 1


class dbusShutdown():
    '''wrapper for shutdown interface provided by the dbus2vdr plugin'''
    def __init__(self,bus,main_instance):
        self.main_instance = main_instance
        self.dbusshutdown = bus.get_object("de.tvdr.vdr","/Shutdown")
        self.interface = 'de.tvdr.vdr.shutdown'

    def manualstart(self):
        return self.dbusshutdown.ManualStart(dbus_interface=self.interface)

    def confirmShutdown(self,user=False):
        code, message, shutdownhooks, message = self.dbusshutdown.ConfirmShutdown(dbus.Boolean(user),dbus_interface=self.interface)
        if code in [250,990]: return True
        else:
            logging.info(u"vdr not ready for shutdown: %s: %s"%(code,message))
            return False
