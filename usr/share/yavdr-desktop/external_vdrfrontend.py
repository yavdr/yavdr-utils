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
from xbmc import XBMC



if __name__ == '__main__':
    options = Options()
    main = Main(options.get_options())
    
    while gtk.events_pending():
        gtk.main_iteration()
    gtk.main()
