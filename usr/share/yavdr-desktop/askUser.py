#!/usr/bin/python
# vim: set fileencoding=utf-8
import sys
import dbus
import gobject
import logging
import traceback
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

class 

class Questioner():
    def __init__(self,bus):
        self.bus = bus
        self.dicts = {}
            
    def ask_question(self, title, mydict):
        qlist = []
        self.mydict[title] = mydict[title]
        for i in mydict[title]:
            qlist.append(i[0])
        self.qlist = dbus.Array(qlist)
        self.dbusremote = self.bus.get_object("de.tvdr.vdr","/Remote")
        self.interface = 'de.tvdr.vdr.remote'
        ret = 550
        while ret !=250:
            ret,msg = self.dbusremote.AskUser(dbus.String(title),dbus.Array(self.qlist),dbus_interface=self.interface)
            
class AskUserListener():
  def __init__(self,bus):
    self.bus = bus

  def osd_signal_handler(self,*args, **kwargs):

    if kwargs['member'] == 'AskUserSelect':
        if len(args) > 1:
            print "Answer to %s is: %s"%(args[0],args[1])
            if type(quest.mydict[args[0]][args[1]][1]) == type(unicode('')):
                print "Answer to %s is: %s"%(args[0],quest.mydict[args[0]][args[1]][1])
            else:
                quest.mydict[args[0]][args[1]][1]()
        else: print args
