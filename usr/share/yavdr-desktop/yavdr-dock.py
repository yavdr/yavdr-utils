#!/usr/bin/env python

# example images.py

import ConfigParser
import pygtk
pygtk.require('2.0')
import gtk
import pylirc
import gobject
import subprocess
import syslog

class YavdrDock:
    # is invoked when the button is clicked.  It just prints a message.
    def button_clicked(self, widget, data=None):
        try:
            subprocess.call(data)
        except:
            syslog.syslog("error calling " + data) 
        gtk.main_quit()
        return True

    def lirc_handler(self, lirc_socket, condition):
        cmds = pylirc.nextcode()
        if cmds:
            for code in cmds:
                if code == "KEY_UP":
                    child = self.hbox.get_children()[0]
                    child.grab_focus()
                    continue
                if code == "KEY_DOWN":
                    child = self.hbox.get_children()[-1]
                    child.grab_focus()
                    continue
                if code == "KEY_LEFT":
                    prevchild = None
                    for child in self.hbox.get_children():
                        if child is self.hbox.get_focus_child():
                            if prevchild:
                                prevchild.grab_focus()
                            break
                        prevchild = child
                    continue
                if code == "KEY_RIGHT":
                    prevchild = None
                    for child in self.hbox.get_children():
                        if prevchild is self.hbox.get_focus_child():
                            child.grab_focus()
                            break
                        prevchild = child
                    continue
                if code == "KEY_OK":
                    child = self.hbox.get_focus_child()
                    child.emit("clicked")
                    return True
                if code == "KEY_EXIT":
                    gtk.main_quit()
                    return True
        return True
    
    def __init__(self):
        config = ConfigParser.SafeConfigParser()
        config.read('example.cfg')
        
        try:
            lirc_socket = pylirc.init("yavdr-dock")
            gobject.io_add_watch(lirc_socket, gobject.IO_IN, self.lirc_handler)
        except:
            syslog.syslog("LIRC initialization error!")

        # create the main window, and attach delete_event signal to terminating
        # the application
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        color = gtk.gdk.color_parse('#000000')
        self.window.modify_bg(gtk.STATE_NORMAL, color)
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
            bgcolor = gtk.gdk.color_parse('#020507')
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
            self.button.props.relief = gtk.RELIEF_NONE
            self.button.add(image)
            self.button.show()
            self.hbox.pack_start(self.button)
            self.button.connect("clicked", self.button_clicked, config.get(section, 'Exec'))

            if focus_is_not_set:
                self.button.grab_focus()
                focus_is_not_set = False

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    YavdrDock()
    main()
