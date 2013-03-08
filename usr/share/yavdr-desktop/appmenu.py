#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Gerald Dachs 2012
# Alexander Grothe 2012
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import logging

import ConfigParser
import pygtk
pygtk.require('2.0')
import gtk
import gobject

class YavdrDock:
    def __init__(self, main_instance):
        self.main_instance = main_instance
        config = ConfigParser.SafeConfigParser()
        config.read('/usr/share/yavdr-desktop/dialog.cfg')
        

        # create the main window, and attach delete_event signal to terminating
        # the application
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        #color = gtk.gdk.color_parse('#000000')
        #self.window.modify_bg(gtk.STATE_NORMAL, color)
        #self.window.set_border_width(1)
        self.window.set_border_width(0)
        self.window.set_has_frame(False)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)

        self.window.set_decorated(False)
        self.window.show()

        # a horizontal box to hold the buttons
        self.hbox = gtk.HBox()
        self.hbox.show()
        self.window.add(self.hbox)

        focus_is_not_set = True
        for section in config.sections():
            # create several images with data from files and load images into
            # buttons
            image = gtk.Image()
            image.set_from_file(config.get(section, 'Image'))
            image.show()
            # a button to contain the image widget
            bgcolor = gtk.gdk.color_parse('#000000')#('#020507') TODO: Make Window kompletely transparent (incl. widget borders)
            fgcolor = gtk.gdk.color_parse('#004466')
            accolor = gtk.gdk.color_parse('#FFFFFF')
            self.button = gtk.Button()
            style = self.button.get_style().copy()
            style.bg[gtk.STATE_NORMAL] = bgcolor
            style.bg[gtk.STATE_SELECTED] = accolor
            style.bg[gtk.STATE_ACTIVE] = accolor
            style.bg[gtk.STATE_PRELIGHT] = fgcolor
            
            #set the button's style to the one you created
            self.button.set_style(style)
            #self.button.props.relief = gtk.RELIEF_NONE
            self.button.add(image)
            self.button.show()
            self.hbox.pack_start(self.button)
            self.button.connect("clicked", self.button_clicked, config.get(section, 'Exec'), config.get(section,'modal'),config.get(section,'exitOnPID'))
            self.button.set_state(gtk.STATE_NORMAL)
            #if focus_is_not_set:
            #    #self.button.grab_focus()
            #    #self.button.set_state(gtk.STATE_PRELIGHT)
            #    focus_is_not_set = False
        for child in self.hbox.get_children():
                child.set_state(gtk.STATE_NORMAL)        
        child = self.hbox.get_children()[0]
        child.grab_focus()
        child.set_state(gtk.STATE_PRELIGHT)

    # is invoked when the button is clicked.  It calls the program.
    def button_clicked(self, widget, data=None, modal=None, exitOnPID=1):
        try:
            self.main_instance.settings.dialog = 0
            if data.startswith('frontend-dbus-send /frontend'):
                eval("self.main_instance.dbusService.%s()" % data.split()[-1])
            else:
                self.main_instance.dbusService.start_application(data,modal,exitOnPID)
        except:
            logging.exception("error calling " + data)
        finally:
            self.window.destroy()
        return True

    def lirc_handler(self, code):
        for child in self.hbox.get_children():
                child.set_state(gtk.STATE_NORMAL)
        if code == "KEY_UP":
            child = self.hbox.get_children()[0]
            child.grab_focus()
            child.set_state(gtk.STATE_PRELIGHT)
        elif code == "KEY_DOWN":
            child = self.hbox.get_children()[-1]
            child.grab_focus()
            child.set_state(gtk.STATE_PRELIGHT)
            
        elif code == "KEY_LEFT":
            prevchild = None
            for child in self.hbox.get_children():
                if child is self.hbox.get_focus_child():
                    if prevchild:
                        prevchild.grab_focus()
                        prevchild.set_state(gtk.STATE_PRELIGHT)
                    else:
                        child.set_state(gtk.STATE_PRELIGHT)
                    break
                prevchild = child
            
        elif code == "KEY_RIGHT":
            prevchild = None
            for child in self.hbox.get_children():
                if child == self.hbox.get_children()[-1]: 
                    child.grab_focus()
                    child.set_state(gtk.STATE_PRELIGHT)
                    break
                if prevchild is self.hbox.get_focus_child():
                    child.grab_focus()
                    child.set_state(gtk.STATE_PRELIGHT)
                    break
                
                prevchild = child
            
        elif code == "KEY_OK":
            child = self.hbox.get_focus_child()
            child.emit("clicked")
            return True
        elif code == "KEY_ESC" or  code == self.main_instance.hdf.readKey("yavdr.desktop.key_dialog"):
            self.main_instance.settings.dialog = 0
            self.main_instance.vdrCommands.vdrRemote.enable()
            self.window.destroy()
            #gtk.main_quit()
            return True
        return True
    
