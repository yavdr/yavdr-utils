#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import logging
import os
import subprocess

class vdrSXFE():
    def __init__(self, main_instance, path='/usr/bin/vdr-sxfe',origin='127.0.0.1',port='37890'):
        self.main_instance = main_instance
        self.main_instance.hdf.updateKey('yavdr.frontend.autocrop','0')
        os.environ['__GL_SYNC_TO_VBLANK']="1"
        # TODO Display config:
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.updateKey('system.x11.display.0.device','DFP-0')) # REMOVE
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.0.device'))
        if self.main_instance.hdf.readKey('system.x11.dualhead.enabled') == "1":
            os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.0.device'))
        if self.main_instance.hdf.readKey('vdr.tempdisplay'):
            os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.1.device'))
            
        self.cmd = [
            '/usr/bin/vdr-sxfe --post tvtime:method=use_vo_driver \
            --reconnect --audio=pulseaudio \
            --syslog xvdr+tcp://%s:%s'%(origin,port)
            ]
        self.proc = None
        self.environ = os.environ
        logging.debug('vdr-sxfe command: %s',' '.join(self.cmd))
        
    def attach(self):
        logging.info('starting vdr-sxfe')
        self.proc = subprocess.Popen(self.cmd,shell=True,env=self.environ)
        logging.debug('started vdr-sxfe')
        
    def detach(self,active=0):
        logging.info('stopping vdr-sxfe')
        try:
            self.proc.kill()
        except:
            logging.info('vdr-sxfe already terminated')
        self.proc = None
        self.main_instance.vdrCommands.vdrRemote.disable()
        
    def status(self):
        if self.proc: return "NOT_SUSPENDED"
        else: return "SUSPEND_DETACHED"
        
    def resume(self):
        if self.proc: pass
        else: self.attach()
        
    def activateWindow(self,window):
        window.activate(int(time.strftime("%s",time.gmtime())))
        logging.debug(u"activate softhddevice window with xid ",window.xid())
        
        
        
        
