#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import logging
import os
import gobject
import subprocess
import time
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import subprocess
DBusGMainLoop(set_as_default=True)

class vdrPIP():
    def __init__(self,main_instance):
        self.main_instance = main_instance
        wnckctrl = main_instance.wnckC
        self.cmd = ['''/usr/bin/vdr \
        -i 1 \
        -m \
        -c /var/lib/vdr-pip \
        -L /usr/lib/vdr/plugins \
        -l 3 \
        -p 2101 \
        -E- \
        -P "softhddevice -D -g 720x405+0+0" \
        -Pdbus2vdr \
        -Pstreamdev-client \
        -v /srv/vdr/video.00 \
        --no-kbd''']
        print self.cmd[0]
        self.main_instance.hdf.updateKey('vdr.pip.cmd',self.cmd[0])
        self.cmd = [self.main_instance.hdf.readKey('vdr.pip.cmd',self.cmd[0])]
        self.screenX = wnckctrl.screen_height
        self.screenY = wnckctrl.screen_width
        self.pipX = 720 * self.screenX / 1920
        self.pipY = self.pipX * self.screenY/self.screenX
        self.marginX = 10
        self.marginY = 10
        self.proc = None
        self.shddbus = None
        self.interface = 'de.tvdr.vdr.plugin'


    def run_vdr(self):
        logging.info(u"starting PIP vdr")
        self.proc = subprocess.Popen(self.cmd, shell=True) # Spawn process
        gobject.child_watch_add(self.proc.pid,self.on_exit,self.proc) # Add callback on exit
        while not self.shddbus:
            try:
                self.shddbus = self.main_instance.systembus.get_object("de.tvdr.vdr1","/Plugins/softhddevice")
            except:
                logging.debug(u"dbus2vdr not jet ready")
                time.sleep(0.5)


    def attach(self,X=0,Y=0,x=0,y=0):
        '''if X and Y:
            geometry="-g %sx%s+%s+%s"%(X,Y,x,y)
        else:
            geometry = ""'''
        self.shddbus.SVDRPCommand(dbus.String("atta"),
                                    dbus.String('-a ""'),
                                    dbus_interface=self.interface)

    def detach(self):
        self.shddbus.SVDRPCommand(dbus.String("deta"),dbus.String(''),dbus_interface=self.interface)

    def stopvdr(self):
        self.proc.terminate()

    def on_exit(self,pid, condition,data):
        logging.info("exit vdr-pip, called function with pid=%s, condition=%s, data=%s",pid, condition,data)
        a,b = data.communicate()
        print a,b
        self.proc = None
