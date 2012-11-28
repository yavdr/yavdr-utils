#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import logging
import os
import gobject
import psutil
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
        #print self.cmd[0]
        self.main_instance.hdf.updateKey('vdr.pip.cmd',self.cmd[0])
        self.cmd = [self.main_instance.hdf.readKey('vdr.pip.cmd',self.cmd[0])]
        logging.info("PIP vdr cmdline: \n %s", self.cmd)
        self.screenX = wnckctrl.screen_height
        self.screenY = wnckctrl.screen_width
        self.pipX = 720 * self.screenX / 1920
        self.pipY = self.pipX * self.screenY/self.screenX
        self.marginX = 10
        self.marginY = 10
        self.proc = None
        self.shddbus = None
        self.interface = 'de.tvdr.vdr.plugin'
        self.remote_interface = 'de.tvdr.vdr.remote'
        
    def play_recording(self,path):
        self.bus = self.main_instance.systembus
        self.dbusrecordings = self.bus.get_object("de.tvdr.vdr1","/Recordings")
        interface = 'de.tvdr.vdr.recording'
        answer, msg = self.dbusrecordings.Play(path,dbus_interface = interface, signature='v')
        return answer, msg


    def run_vdr(self):
        logging.info(u"starting PIP vdr")
        self.proc = subprocess.Popen(self.cmd, shell=True) # Spawn process
        gobject.child_watch_add(self.proc.pid,self.on_exit,self.proc) # Add callback on exit
        while not self.shddbus:
            try:
                self.shddbus = self.main_instance.systembus.get_object("de.tvdr.vdr1","/Plugins/softhddevice")
                self.remote = self.main_instance.systembus.get_object("de.tvdr.vdr1","/Remote")
                logging.debug('dbus2vdr of pip vdr ready')
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
        #gobject.timeout_add(500,self.channelswitch)
                                    
    def channelswitch(self):
                                    
        try:
            ochnum, chname = self.main_instance.vdrCommands.vdrRemote.channel()
            logging.info('current channel of main vdr is %s', ochnum)
        except:
            logging.exception('error getting channel')
        chnum = None
        try:
            while ochnum != chnum:
                time.sleep(0.5)
                answer, msg = self.remote.SwitchChannel(dbus.String(chnum),
                                    dbus_interface=self.remote_interface)
                answer, msg = self.remote.SwitchChannel(dbus.String(''),
                                    dbus_interface=self.remote_interface)
                chnum,chname = msg.split(' ',1)
                logging.debug('could not switch to channel, channel is: %s %s',chnum,chname)
                    
            logging.info("Switched to %s: %s",answer,msg)
        except: logging.exception('could not switch channel')
        return False
                                    
    
        
        

    def detach(self):
        self.shddbus.SVDRPCommand(dbus.String("deta"),dbus.String(''),dbus_interface=self.interface)
        self.main_instance = main_instance
        self.bus = self.main_instance.systembus
        self.dbusrecordings = self.bus.get_object("de.tvdr.vdr","/Recordings")
        self.interface = 'de.tvdr.vdr.recording'

    def stopvdr(self):
        logging.debug("vdrPIP.stopvdr()")
        self.proc.terminate()

    def on_exit(self,pid, condition,data):
        logging.info("exit vdr-pip, called function with pid=%s, condition=%s, data=%s",pid, condition,data)
        a,b = data.communicate()
        print a,b
        self.proc = None
