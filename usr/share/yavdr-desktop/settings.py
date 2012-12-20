#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import logging
import os
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import subprocess
import time
DBusGMainLoop(set_as_default=True)


class Settings():
    ''' read and store configuration, handle input devices using udev'''
    def __init__(self,main_instance):
        self.hdf = main_instance.hdf
        self.bus = main_instance.systembus
        self.options = main_instance.options
        self.vdrCommands = main_instance.vdrCommands
        self.frontend_active = 0
        self.external_prog = 0
        self.external_proc = {}
        self.dialog = 0
        self.env = os.environ
        self.timer = None
        self.vdr_remote = True

        self.manualstart = self.vdrCommands.vdrShutdown.manualstart()
        logging.info(u"vdr was started manually: %s",self.manualstart)
        try:
            self.acpi_wakeup = self.check_acpi()
        except:
            self.acpi_wakeup = None
            logging.info(u"no readable acpiwakeup file found")
        # *** TODO: Replace by an elaborated config loader ***
        self.conf = {
        'logo_attached': self.hdf.updateKey("yavdr.desktop.bg_attached",
                "/usr/share/yavdr/images/yavdr_logo.png"),
        'logo_detached':self.hdf.updateKey("yavdr.desktop.bg_detached",
                "/usr/share/yavdr/images/yaVDR_background_detached.jpg"),
        'key_detach':self.hdf.updateKey("yavdr.desktop.key_detach","KEY_PROG1"),
        'key_xbmc':self.hdf.updateKey("yavdr.desktop.key_xbmc","KEY_PROG2"),
        'key_power':self.hdf.updateKey("yavdr.desktop.key_power","KEY_POWER2"),
        'key_dialog':self.hdf.updateKey("yavdr.desktop.key_dialog","KEY_PROG3"),
        'start_always_detached':self.hdf.updateKey("yavdr.desktop.start_detached",'0'),
        'display':self.hdf.updateKey("yavdr.desktop.display", os.environ['DISPLAY']),
        'default_frontend':self.hdf.updateKey('vdr.frontend','softhddevice'),
        }
        logging.debug(type(self.hdf.readKey("yavdr.desktop.key_xbmc","KEY_PROG2")))
        #self.hdf.writeFile()
        # *** END TODO ***
        #self.updateDisplay()
        self.apps = {}

    def check_pulseaudio(self):
        pulse = 1
        while pulse == 1:
          try:
            if "module-native-protocol-tcp" in subprocess.check_output(["/usr/bin/pactl","list","modules"]): pulse = 0
            time.sleep(1)
          except subprocess.CalledProcessError: pulse = 1

    def SetTimeout(self,timeout_s,call_f):
        timeout_ms = 1000 * timeout_s
        self.timer = gobject.timeout_add(timeout_ms,call_f)

    def CancelTimeout(self):
        try: gobject.source_remove(self.timer)
        except: pass

    def GetActiveWindowTitle(self):
        '''get title of active window'''
        return subprocess.Popen(["xprop", "-id", subprocess.Popen(["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE, env=settings.env).communicate()[0].strip().split()[-1], "WM_NAME"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip().split('"', 1)[-1][:-1]

    def updateDisplay(self):
        self.env["DISPLAY"] = self.conf['display'] #+self.getTempDisplay()

    def getTempDisplay(self):
        tempdisplay = ".0"
        return tempdisplay

    def check_acpi(self):
        timestr = open('/var/cache/vdr/acpiwakeup.time.old','r').read().splitlines()[0]
        wakeup = datetime.datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.utcnow()
        logging.debug("acip-wakeup.time.old has timestamp: %s"%(wakeup.ctime()))
        logging.debug("comparing to: %s"%(now.ctime()))
        if wakeup < now:
            d = now - wakeup
        else:
            d = wakeup - now
        if d.seconds > 360:
            logging.info("assuming manual start")
            return False
        else:
            logging.info("assuming start for acpi-wakeup")
            return True

    def tsplit(self,string, delimiters):
        """extends str.split - supports multiple delimiters."""
        delimiters = tuple(delimiters)
        stack = [string,]
        for delimiter in delimiters:
            for i, substring in enumerate(stack):
                substack = substring.split(delimiter)
                stack.pop(i)
                for j, _substring in enumerate(substack):
                    stack.insert(i+j, _substring)
        return stack
