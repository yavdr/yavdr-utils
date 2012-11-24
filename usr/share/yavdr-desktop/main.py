#!/usr/bin/python
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

# dbus
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import codecs
import datetime
import fcntl
import gobject
import gtk
import logging
import os
import re
import string
import subprocess
import sys
import time
import wnck

from optionparser import Options
from hdftool import HDF

# Import own Modules
from vdrDBusCommands import vdrDBusCommands
from settings import Settings
from lircsocket import lircConnection
from graphtft import GraphTFT
import dbusService
from wnckController import wnckController
from adeskbar import adeskbarDBus
from sxfe import vdrSXFE
from xine import vdrXINE

class Main():
    def __init__(self,options):
        # command line arguments
        self.options = options
        # Logging
        logging.basicConfig(
            filename=self.options.logfile,
            level=getattr(logging,self.options.loglevel),
            format='%(asctime)-15s %(levelname)-6s %(message)s'            
            )
        logging.info(u"Started yavdr-frontend")
        # dbus SystemBus and SessionBus
        try:
            self.systembus = dbus.SystemBus()
            logging.info(u'Connected to SystemBus')
        except:
            logging.exception(u"could not connect to SystemBus")
            sys.exit(1)
        try:
            self.sessionbus = dbus.SessionBus()
            logging.info(u'Connected to SessionBus')
        except:
            logging.exception(u"could not connect to SessionBus")
            sys.exit(1)   
        
        self.hdf = HDF(options.hdf_file)
        self.running = self.wait_for_vdrstart() # wait for VDR upstart job status running
        
        try:# Add watchdog for vdr-upstart-job to detect stopping and restarts
            logging.debug(u'connecting to upstart')
            self.upstart_vdr = self.systembus.get_object("org.freedesktop.DBus","/com/ubuntu/Upstart/jobs/vdr")
            self.upstart_vdr.connect_to_signal("VDR", self.signal_handler, dbus_interface="com.ubuntu.Upstart0_6.Instance")
            self.systembus.add_signal_receiver(self.signal_handler, interface_keyword='dbus_interface', member_keyword='member', sender_keyword='sender', path_keyword='path'
)
            logging.debug(u'connected to upstart')
        except dbus.DBusException:
            logging.debug(u'ran into exception')
            logging.exception(traceback.print_exc())

        self.vdrCommands = vdrDBusCommands(self) # dbus2vdr fuctions
        self.dbusService = dbusService.dbusService(self)
        self.settings = Settings(self)
        self.graphtft = GraphTFT(self)
        self.wnckC = wnckController(self)
        self.dbusPIP = dbusService.dbusPIP(self)
        self.adeskbar = adeskbarDBus(self.systembus)
        self.frontend = None
        self.lircConnection = lircConnection(self,self.vdrCommands) # connect to (event)lircd-Socket
        try:
            self.startup()
        except:
            logging.exception('no frontend initialized')
    
    def soft_detach():
        self.frontend.detach()
        settings.timer = gobject.timeout_add(300000,self.dbusService.send_shutdown)
        return False
            
    def startup(self):
        self.vdrCommands = vdrDBusCommands(self) # dbus2vdr fuctions
        self.graphtft = GraphTFT(self)
        logging.info('run startup()')
        if self.hdf.readKey('vdr.frontend') == 'softhddevice' and self.vdrCommands.vdrSetup.check_plugin('softhddevice'):
            logging.info(u'Configured softhddevide as primary frontend')
            self.frontend = self.vdrCommands.vdrSofthddevice
        elif self.hdf.readKey('vdr.frontend') == 'sxfe' and self.vdrCommands.vdrSetup.check_plugin('xineliboutput'):
            logging.info('using vdr-sxfe as primary frontend')
            self.frontend = vdrSXFE(self)
        elif self.hdf.readKey('vdr.frontend') == 'xine' and self.vdrCommands.vdrSetup.check_plugin('xine'):
            logging.info('using xine as primary frontend')
            self.frontend = vdrXINE(self)
        try:
            if self.frontend:
                logging.debug('self.frontend exists')
                self.dbusService.atta()
            else:
                logging.debug('self.frontend is None')
        except:
            logging.exception('no frontend initialized')
        
    def wait_for_vdrstart(self):
        upstart = self.systembus.get_object("com.ubuntu.Upstart", "/com/ubuntu/Upstart")
        status = None
        while not status == 'start/running':
            try:
                path = upstart.GetJobByName("vdr", dbus_interface="com.ubuntu.Upstart0_6")
                job = self.systembus.get_object("com.ubuntu.Upstart", path)
                path = job.GetInstance([], dbus_interface="com.ubuntu.Upstart0_6.Job")
                instance = self.systembus.get_object("com.ubuntu.Upstart", path)
                props = instance.GetAll("com.ubuntu.Upstart0_6.Instance", dbus_interface=dbus.PROPERTIES_IFACE)
                status = "%s/%s"%(props["goal"], props["state"])
            except: pass
            if not status: 
                logging.info('vdr upstart job not running, wait 1 s')
                time.sleep(1)
            else:
                logging.info('vdr upstart job running')
                return True
    
    def signal_handler(self,*args, **kwargs):
        if '/com/ubuntu/Upstart/jobs/vdr/_' == kwargs['path']:
            if kwargs['member'] == "StateChanged":
                logging.debug("StateChanged:")
                if not self.running and 'running' in args[0]:
                    self.hdf.readFile()
                    self.startup()
                    self.running = True
                    logging.debug(u"vdr upstart job running")
                if 'pre-stop' in args[0]:
                    self.running = False
                    self.dbusService.deta()
                    
                    logging.debug(u"vdr upstart job stopped/waiting")
            elif kwargs['member'] == "InstanceRemoved":
                logging.debug("killed job")
            elif kwargs['member'] == "InstanceAdded":
                logging.debug("added upstart-job")
            else:
                return
            if len(args):
                logging.info("VDR is %s", args[0])
                #logging.info(kwargs)
        
    def start_app(self,cmd,detachf=True, env=os.environ):
        logging.info('starting %s',cmd)
        if self.settings.frontend_active == 1 and detachf == True:
            logging.info('detaching frontend')
            self.dbusService.deta()
            self.wnckC.windows['frontend'] = None
            self.settings.reattach = 1
        else:
            self.settings.reattach = 0
        if cmd != ' ' and cmd != None and len(cmd)!=0:
            os.chdir(os.environ['HOME'])
            logging.info('starting %s',cmd)
            proc = subprocess.popen(cmd,env=os.env())
            gobject.child_watch_add(proc.pid,self.on_exit,proc) # Add callback on exit

    def on_exit(self,pid, condition,data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",pid, condition,data)
        self.settings.external_prog = 0
        if condition == 0:
            logging.info(u"normal exit")
            gobject.timeout_add(500,self.reset_external_prog)
        elif condition < 16384:
            logging.warn(u"abnormal exit: %s",condition)
            gobject.timeout_add(500,reset_external_prog)
        elif condition == 16384:
            logging.info(u"XBMC shutdown")
            self.dbusService.send_shutdown(user=True)
        elif condition == 16896:
            logging.info(u"XBMC wants a reboot")
        
        return False
        
    def reset_external_prog(self):
        self.settings.external_prog = 0
        if self.settings.reattach == 1:
            logging.info("restart vdr-frontend")
            self.dbusService.toggle()
            self.settings.frontend_active = 1
        else:
            self.settings.frontend_active = 0
        return False
        
     
        
if __name__ == '__main__':
    options = Options()
    main = Main(options.get_options())
    
    while gtk.events_pending():
        gtk.main_iteration()
    gtk.main()
