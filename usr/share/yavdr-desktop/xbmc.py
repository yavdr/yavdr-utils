#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import gobject
import logging
import os
import time
import socket
import subprocess

class XBMC():
    def __init__(self, main_instance, path='/usr/bin/xbmc',standalone="--standalone"):
        self.main_instance = main_instance
        os.environ['__GL_SYNC_TO_VBLANK']="1"
        # TODO Display config:
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.updateKey('system.x11.display.0.device','DFP-0')) # REMOVE
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.0.device'))
        if self.main_instance.hdf.readKey('system.x11.dualhead.enabled') == "1":
            os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.0.device'))
        if self.main_instance.hdf.readKey('vdr.tempdisplay'):
            os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.1.device'))
            
        self.cmd = ['/usr/lib/xbmc/xbmc.bin',standalone,
                                '--lircdev','/var/run/lirc/lircd']
        self.proc = None
        self.environ = os.environ
        logging.debug('xbmc command: %s',' '.join(self.cmd))
        
    def attach(self,frontend=True):
        logging.info('starting xbmc')
        try:
            self.proc = subprocess.Popen(self.cmd,env=self.environ)
            gobject.child_watch_add(self.proc.pid,self.on_exit,self.proc) # Add callback on exit
            logging.debug('started xbmc')
        except:
            logging.exception('could not start xbmc')
                
    def on_exit(self,pid, condition,data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",pid, condition,data)
        self.main_instance.settings.external_prog = 0
        if condition == 0:
            logging.info(u"normal exit")
            if self.main_instance.hdf.readKey('vdr.frontend') != 'xbmc':
                gobject.timeout_add(500,self.main_instance.reset_external_prog)
            else:
                self.main_instance.settings.frontend_active = 0
        elif condition < 16384:
            logging.warn(u"abnormal exit: %s",condition)
            gobject.timeout_add(500,self.main_instance.reset_external_prog)
        elif condition == 16384:
            logging.info(u"XBMC shutdown")
            self.main_instance.dbusService.send_shutdown(user=True)
        elif condition == 16896:
            logging.info(u"XBMC wants a reboot")
            logging.info(self.main_instance.powermanager.restart())
        
        
    def detach(self,active=0):
        logging.info('stopping xbmc')
        try:
            logging.debug('sending terminate signal')
            self.proc.terminate()
        except:
            logging.info('xbmc already terminated')
        self.proc = None
        #self.main_instance.vdrCommands.vdrRemote.disable()
        
    def status(self):
        if self.proc: return "NOT_SUSPENDED"
        else: return "SUSPEND_DETACHED"
        
    def resume(self):
        if self.proc: pass
        else: self.attach()
        
    def activateWindow(self,window):
        window.activate(int(time.strftime("%s",time.gmtime())))
        logging.debug(u"activate xbmc window with xid ",window.xid())
        
        
        
        
