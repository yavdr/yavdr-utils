#!/usr/bin/python
# Alexander Grothe 2011
#
# This script requires python-uinput V 0.6.1. Additional required packages are libudev0 and libudev-dev.
#
### Fetch the code for python-uinput from git: ###
#
# git clone git://github.com/tuomasjjrasanen/python-uinput.git
# cd python-uinput
# git clone git://github.com/tuomasjjrasanen/libsuinput.git
# sudo python setup.py install
#
###
#
# This script must be run as superuser or with sufficent rights to create an uinput device and exspects a lircd socket under /var/run/lirc/lircd.$(pidof lircd) if none is given by --lircd-socket /PATH/TO/LIRCD_SOCKET
# lircd must not be startet with --uinput, but with --release="_up"

import string
import socket
import time
import sys
import uinput
import subprocess
import datetime
from optparse import OptionParser

class Lirc2uinput:
    """Sends keystrokes to a virtual uinput device after applying a repeat-filter"""
    def __init__(self, uinput_name="lircd", options=None):
        self.lastkey = None
        self.wait_repeats = options.wait_repeats
        self.max_gap = options.max_gap
        self.min_gap = options.min_gap
        self.acceleration = options.acceleration
        self.lircd_socket = options.lircd_socket
        self.gap_delta = (self.max_gap - self.min_gap)*self.acceleration
        self.current_gap = self.max_gap
        self.repeat_num = 0
        self.timestamp = datetime.datetime.now()
        self.events = (
            uinput.KEY_UP,
            uinput.KEY_DOWN,
            uinput.KEY_MENU,
            uinput.KEY_OK,
            uinput.KEY_ESC,
            uinput.KEY_LEFT,
            uinput.KEY_RIGHT,
            uinput.KEY_RED,
            uinput.KEY_GREEN,
            uinput.KEY_YELLOW,
            uinput.KEY_BLUE,
            uinput.KEY_0,
            uinput.KEY_1,
            uinput.KEY_2,
            uinput.KEY_3,
            uinput.KEY_4,
            uinput.KEY_5,
            uinput.KEY_6,
            uinput.KEY_7,
            uinput.KEY_8,
            uinput.KEY_9,
            uinput.KEY_INFO,
            uinput.KEY_PLAY,
            uinput.KEY_PAUSE,
            uinput.KEY_STOP,
            uinput.KEY_RECORD,
            uinput.KEY_FASTFORWARD,
            uinput.KEY_REWIND,
            uinput.KEY_NEXT,
            uinput.KEY_BACK,
            uinput.KEY_POWER2,
            uinput.KEY_CHANNELUP,
            uinput.KEY_CHANNELDOWN,
            uinput.KEY_PREVIOUS,
            uinput.KEY_VOLUMEUP,
            uinput.KEY_VOLUMEDOWN,
            uinput.KEY_MUTE,
            uinput.KEY_SUBTITLE,
            uinput.KEY_EPG,
            uinput.KEY_CHANNEL,
            uinput.KEY_FAVORITES,
            uinput.KEY_MODE,
            uinput.KEY_TIME,
            uinput.KEY_PVR,
            uinput.KEY_SETUP,
            uinput.KEY_TEXT,
            uinput.KEY_PROG1,
            uinput.KEY_PROG2,
            uinput.KEY_PROG3,
            uinput.KEY_PROG4,
            uinput.KEY_AUDIO,
            uinput.KEY_VIDEO,
            #uinput.KEY_IMAGES, # undefined key within python-uinput, to be replaced by KEY_CAMERA for example
            uinput.KEY_FN,
            uinput.KEY_SCREEN
            )
        self.device = uinput.Device(self.events, uinput_name)

    def get_gap(self,repeat_num):
        if self.current_gap > self.min_gap:
            new_gap = self.current_gap - self.gap_delta
        else:
            #print "minimum gap reached"
            pass
        return self.current_gap
    
    def send_key(self,key):
        keycmd = eval('uinput.%s'%(key.replace("_up","")))
        #print keycmd
        now = datetime.datetime.now()
        if key.endswith("_up"):
            print "released %s"%(key[:-3])
            self.device.emit(keycmd, 0)
            self.repeat_num = 0
            self.timestamp = datetime.datetime.now()
            self.current_gap = self.max_gap
        elif self.lastkey == keycmd:
            if (now - self.timestamp).microseconds < self.current_gap:
                #print "Passing keypress... too early"#"repeated %s %s times"%(key,self.repeat)
                pass     
            else:
                #print "Repeated keypress"
                if self.repeat_num >= self.wait_repeats:
                    self.current_gap = self.get_gap(self.repeat_num)
                else:
                    pass
                self.device.emit(keycmd, 1)
                self.device.emit(keycmd, 0)
                self.timestamp = datetime.datetime.now()
                self.repeat_num += 1

        else:
            #print "first keypress"
            self.device.emit(keycmd, 1)
            self.device.emit(keycmd, 0)
            self.timestamp = datetime.datetime.now()
            self.current_gap = self.max_gap
            self.repeat_num = 0

        self.lastkey=keycmd


class main:
    """Listens to LIRC's domain socket and calls a method each time an
    IR command is received."""
    def __init__(self):
        parser = Options()
        self.options = parser.get_opts()
        if not self.options.lircd_socket:
            # use /var/run/lirc/lircd.<pidof lircd> as socket 
            pid = int(subprocess.check_output(['pidof', "lircd"]))
            self.socket_path =  "/var/run/lirc/lircd.%s"%(pid)
        else:
            self.socket_path = self.options.lircd_socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.uinputdev = Lirc2uinput(options=self.options)

    def listen2socket(self):
        self.sock.connect(self.socket_path)
        buf = ""
        while 1:
            buf += self.sock.recv(1024)
            lines = string.split(buf, "\n")
            for line in lines[:-1]:
                code,count,cmd,device = string.split(line, " ")
                self.lirc_message(cmd)
            buf = lines[-1]

    def lirc_message(self, cmd):
        self.uinputdev.send_key(cmd)

class Options:
    def __init__(self):
        self.parser = OptionParser()
        self.parser.add_option("-l", "--min-gap", dest="min_gap", default=150000, type="int",
                  help="set minimum gap between repeated keystrokes (default 150000)", metavar="MIN_GAP")
        self.parser.add_option("-u", "--max-gap", dest="max_gap", default=300000, type="int",
                  help="set maximum gap between repeated keystrokes (default 300000)", metavar="MAX_GAP")
        self.parser.add_option("-r", "--min-repeats", dest="wait_repeats", default=2, type="int",
                  help="number of repeats before using accelerated keypresses (default = 2)", metavar="WAIT_REPEATS")
        self.parser.add_option("-a", "--acceleration", dest="acceleration", default=0.25, type="float",
                  help="acceleration to get from MAX_GAP to MIN_GAP. default value of 0.25 equals 4 repeated keystrokes to reach maximum speed",
                    metavar="ACCELERATION")
        self.parser.add_option("-s", "--lircd-socket", dest="lircd_socket", default=None,
                  help="choose lircd socket to listen on", metavar="LIRCD_SOCKET")
    def get_opts(self):
        (options, args) = self.parser.parse_args()
        return options


if __name__ == "__main__":
    vlirc = main()
    vlirc.listen2socket()
