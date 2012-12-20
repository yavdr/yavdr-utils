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

class vdrXINE():
    def __init__(self, main_instance, path='/usr/bin/xine',origin='127.0.0.1',port='37890'):
        self.main_instance = main_instance
        self.main_instance.hdf.updateKey('yavdr.frontend.sxfe.autocrop','0') # Remove
        self.main_instance.hdf.updateKey('yavdr.frontend.xine.anamorphic','') # Remove
        self.main_instance.hdf.updateKey('yavdr.frontend.xine.autocrop','0') # Remove
        if self.main_instance.hdf.readKey('yavdr.frontend.sxfe.autocrop'):
            autocrop = "--post autocrop:enable_autodetect=1,enable_subs_detect=1,soft_start=1,stabilize=1"
        else:
            autocrop = ""
        if self.main_instance.hdf.readKey('yavdr.frontend.xine.anamorphic'):
            aspectratio = "--aspect-ratio=%s"%(self.main_instance.hdf.readKey('yavdr.frontend.xine.anamorphic'))
        else:
            aspectratio = ""
        os.environ['__GL_SYNC_TI_VBLANK']="1"
        # TODO Display config:
        self.main_instance.hdf.updateKey('system.x11.display.0.device','DFP-0') # REMOVE
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = str(self.main_instance.hdf.readKey('system.x11.display.0.device'))

        self.cmd = ['/usr/bin/xine --post tvtime:method=use_vo_driver \
            --config /etc/xine/config \
            --keymap=file:/etc/xine/keymap \
            --post vdr --post vdr_video --post vdr_audio --verbose=2 \
            --no-gui --no-logo --no-splash --deinterlace -pq \
            -A pulseaudio \
            %s %s \
            vdr:/tmp/vdr-xine/stream#demux:mpeg_pes'%(autocrop, aspectratio)]
        self.proc = None
        self.environ = os.environ
        logging.debug(' '.join(self.cmd))
        
    def attach(self):
        logging.info('starting xine')
        self.proc = subprocess.Popen(self.cmd,shell=True,env=os.environ)
        logging.info('started xine')
        
    def detach(self,active=0):
        logging.info('stopping xine')
        try:
            self.proc.kill()#.terminate()
        except:
            logging.info('xine already terminated')
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
        
        
        
        
