#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import logging

class vdrSXFE():
    def __init__(self, path='/usr/bin/vdr-sxfe',origin='127.0.0.1',port='37890'):
        self.main_instance.hdf.updateKey('yavdr.frontend.vdr-sxfe.autocrop','0')
        os.environ['USE_AUTOCROP']= self.main_instance.hdf.readKey('yavdr.frontend.vdr-sxfe.autocrop')
        os.environ['__GL_SYNC_TI_VBLANK']=1
        # TODO Display config:
        os.environ['__GL_SYNC_DISPLAY_DEVICE'= self.main_instance.hdf.updateKey('system.x11.display.0.device','DFP-0') # REMOVE
        os.environ['__GL_SYNC_DISPLAY_DEVICE'= self.main_instance.hdf.readKey('system.x11.display.0.device')
        cmd = [path]
        self.main_instance.hdf.updateKey('system.x11.hud','0') # REMOVE
        # HUD
        if self.main_instance.hdf.readKey('system.x11.hud'):
            cmd.append('--opengl --hud=opengl')
        # Video, Audio and logging
        cmd.append('--post tvtime:method=use_vo_driver --reconnect --audio=pulse --syslog --silent --tcp')
        cmd.append('--config=/etc/vdr-sxfe/config_xineliboutput')
        cmd.append('xvdr://%s:%s'%(origin,port))
        self.proc = None
        
    def attach(self):
        self.proc = subprocess.Popen(cmd,env=os.environ)
        
    def detach(self):
        self.proc.terminate()
        
    def status(self):
        if self.proc: return "NOT_SUSPENDED"
        else: return "SUSPEND_DETACHED"
        
    def resume(self):
        if self.proc: pass
        else: self.attach()
        
    def activateWindow(self,window):
        window.activate(int(time.strftime("%s",time.gmtime())))
        logging.debug(u"activate softhddevice window with xid ",window.xid())
        
        
        
        
