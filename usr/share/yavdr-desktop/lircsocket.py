#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

import gobject
import logging
import socket
import string
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class lircConnection():
    def __init__(self,main_instance,vdrCommands,socket_path="/var/run/lirc/lircd"):
        self.main_instance = main_instance
        self.socket_path = socket_path
        self.vdrCommands = vdrCommands
        self.try_connection()
        
    def connect_eventlircd(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        gobject.io_add_watch(sock, gobject.IO_IN, self.handler)

    def try_connection(self):
        try:
            self.connect_eventlircd()
            logging.info(u"conntected to Lirc-Socket on %s"%(self.socket_path))
            return False
        except:
            gobject.timeout_add(1000, self.try_connection)
            logging.error("Error: vdr-frontend could not connect to eventlircd socket")
            return True
            
    def handler(self, sock, *args):
        '''callback function for activity on eventlircd socket'''
        try:
            buf = sock.recv(1024)
            if not buf:
                sock.close()
                logging.error("Error reading from lircd socket")
                try_connection()
                return True
        except:
            sock.close()
            logging.exception('retry lirc connection')
            try_connection()
            return True
        lines = string.split(buf, "    n")
        for line in lines:
            if self.main_instance.settings.external_prog == 0: 
                try: 
                    if main_instance.settings.timer: 
                        gobject.source_remove(main_instance.settings.timer)
                        main_instance.settings.timer = None
                except: 
                    logging.debug('no timer to remove')
                try: 
                    code,count,cmd,device = string.split(line, " ")[:4]
                except: 
                    logging.exception(line)
                    return True
                if cmd == self.main_instance.hdf.readKey("yavdr.desktop.key_detach"):
                    if self.main_instance.frontend.status() == "NOT_SUSPENDED":
                        self.main_instance.frontend.detach()
                        self.main_instance.settings.frontend_active = 0
                    else:
                        self.main_instance.dbusService.resume(frontend.status())
                elif cmd == self.main_instance.hdf.readKey("yavdr.desktop.key_xbmc") and self.main_instance.settings.external_prog == 0:
                        cmd = ['/usr/lib/xbmc/xbmc.bin','--standalone','--lircdev','/var/run/lirc/lircd']
                        try:
                            self.main_instance.dbusService.start_xbmc()
                        except:
                            logging.exception('XBMC-START')
                        gobject.timeout_add(50, self.main_instance.dbusService.start_xbmc)
                        return True

                elif cmd == self.main_instance.hdf.readKey("yavdr.desktop.key_power"):
                    if self.main_instance.frontend.status() == "NOT_SUSPENDED":
                        self.main_instance.settings.timer = gobject.timeout_add(15000,self.main_instance.soft_detach)
                        self.main_instance.settings.frontend_active = 0
                    else:
                        self.main_instance.dbusService.send_shutdown()
                else:
                    if self.main_instance.settings.frontend_active == 0 and self.main_instance.settings.external_prog == 0:
                        self.main_instance.dbusService.atta()
                    else:
                        pass
        return True
