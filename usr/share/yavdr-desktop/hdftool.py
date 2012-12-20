import os
import re
import sys
import time
import fcntl
import argparse
import neo_cgi
import neo_util

class HDF:
    def __init__(self, file):
        self.file = file
        self.hdf = neo_util.HDF()
        self.readFile()
    def readKey(self, key, default = ""):
        return self.hdf.getValue(key, default)
    def writeKey(self, key, value):
        return self.hdf.setValue(key, value)
    def deleteKey(self, key):
        return self.hdf.removeTree(key)
    def dumpKey(self, key):
        dump = []
        for entry in self.hdf.dump().split("\n"):
            regex = re.compile('^%s'%key)
            if entry != "" and (key == '.' or re.search(regex, entry)):
                dump.append(entry)
        return "\n".join(dump)
    def childrensByKey(self, key):
        childrens = []
        dataset = self.hdf.getObj(key)
        try:
            child = dataset.child()
            while child:
                childrens.append(child.name())
                child = child.next()
        except:
            pass
        return childrens
    def checkKey(self, key):
        if self.readKey(key, "NULLNULLNULL") == "NULLNULLNULL":
            if len(self.childrensByKey(key)) > 0:
                return True
            else:
                return False
        else:
            return True
    def presetKey(self, key, value):
        if not self.checkKey(key):
            self.writeKey(key, value)
    def updateKey(self, key, value):
        if not self.checkKey(key) and self.readKey(key) != value:
            self.writeKey(key, value)
    def readFile(self):
        if os.path.exists(self.file) and os.path.isfile(self.file):
            return self.hdf.readFile(self.file);
    def writeFile(self):
        return self.hdf.writeFile(self.file);
    def __str__( self ):
        return self.hdf.dump()
