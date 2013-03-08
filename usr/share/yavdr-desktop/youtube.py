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
import psutil
import time
import socket
import subprocess


class YouTube:
    def __init__(self, main_instance, path='/usr/bin/google-chrome', browser="/opt/google/chrome/chrome"):
        self.main_instance = main_instance
        self.irxevent_cmd = ['/usr/bin/irxevent', '/home/alexander/leanback.lircrc']
        self.leanback_cmd = [browser, '--app=https://www.youtube.com/leanback']
        
    def attach(self):
        self.irxevent = subprocess.Popen(self.irxevent_cmd, env=os.environ)
        self.leanback = subprocess.Popen(self.leanback_cmd, env=os.environ)
        gobject.child_watch_add(self.leanback.pid,self.on_exit,self.leanback) # Add callback on exit

    def detach(self):
        self.leanback.terminate()
        self.irxevent.kill()
        self.irxevent = None
        self.leanback = None

    def resume(self):
        if self.leanback: pass
        else: self.attach()

    def status(self):
        if self.leanback: return "NOT_SUSPENDED"
        else: return "SUSPEND_DETACHED"

    def on_exit(self,pid, condition,data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",pid, condition,data)
        self.main_instance.settings.external_prog = 0
        if condition == 0:
            logging.info(u"normal exit")
            if self.main_instance.hdf.readKey('vdr.frontend') != 'xbmc':
                gobject.timeout_add(500,self.main_instance.reset_external_prog)
            else:
                self.main_instance.settings.frontend_active = 0
        else:
            logging.warn(u"abnormal exit: %s",condition)
            gobject.timeout_add(500,self.main_instance.reset_external_prog)
        PROCNAME = "irxevent"
        for proc in psutil.process_iter():
            if proc.name == PROCNAME:
                proc.kill()
