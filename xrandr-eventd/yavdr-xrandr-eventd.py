#!/usr/bin/python
#
# examples/xrandr.py -- demonstrate the RandR extension
#
#    Copyright (C) 2009 David H. Bronke <whitelynx@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import sys, os, pprint
import time
#import hdf

# Change path so we find Xlib
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from Xlib import X, display, Xutil
from Xlib.ext import randr

# Application window (only one)
class Window:
    def __init__(self, display):
        self.d = display

        # Check for extension
        if not self.d.has_extension('RANDR'):
            sys.stderr.write('%s: server does not have the RANDR extension\n'
                             % sys.argv[0])
            print self.d.query_extension('RANDR')
            sys.stderr.write("\n".join(self.d.list_extensions()))
            if self.d.query_extension('RANDR') is None:
                sys.exit(1)

        # print version
        r = self.d.xrandr_query_version()
        print 'RANDR version %d.%d' % (r.major_version, r.minor_version)


        # Grab the current screen
        self.screen = self.d.screen()

        self.window = self.screen.root.create_window(
            50, 50, 300, 200, 2,
            self.screen.root_depth,
            X.InputOutput,
            X.CopyFromParent,

            # special attribute values
            background_pixel = self.screen.white_pixel,
            event_mask = (X.ExposureMask |
                          X.StructureNotifyMask |
                          X.ButtonPressMask |
                          X.ButtonReleaseMask |
                          X.Button1MotionMask),
            colormap = X.CopyFromParent,
            )

        self.gc = self.window.create_gc(
            foreground = self.screen.black_pixel,
            background = self.screen.white_pixel
            )

        # Set some WM info

        self.WM_DELETE_WINDOW = self.d.intern_atom('WM_DELETE_WINDOW')
        self.WM_PROTOCOLS = self.d.intern_atom('WM_PROTOCOLS')

        self.window.set_wm_name('Xlib example: xrandr.py')
        self.window.set_wm_icon_name('xrandr.py')
        self.window.set_wm_class('xrandr', 'XlibExample')

        self.window.set_wm_protocols([self.WM_DELETE_WINDOW])
        self.window.set_wm_hints(flags = Xutil.StateHint,
                                 initial_state = Xutil.NormalState)

        self.window.set_wm_normal_hints(flags = (Xutil.PPosition | Xutil.PSize
                                                 | Xutil.PMinSize),
                                        min_width = 20,
                                        min_height = 20)

        # Map the window, making it visible
#        self.window.map()

        # Enable all RandR events.
        self.window.xrandr_select_input(
            randr.RRScreenChangeNotifyMask
            | randr.RRCrtcChangeNotifyMask
            | randr.RROutputChangeNotifyMask
            | randr.RROutputPropertyNotifyMask
            )

        self.pp = pprint.PrettyPrinter(indent=4)

        #print "Screen info:"
        #self.pp.pprint(self.window.xrandr_get_screen_info()._data)

        #print "Screen size range:"
        #self.pp.pprint(self.window.xrandr_get_screen_size_range()._data)

        #print "Primary output:"
        #self.pp.pprint(self.window.xrandr_get_output_primary()._data)

        resources = self.window.xrandr_get_screen_resources()._data

        #print "Modes:"
        #for mode_id, mode in self.parseModes(resources['mode_names'], resources['modes']).iteritems():
        #    print "    %d: %s" % (mode_id, mode['name'])

        self.sequence_number = 0
        self.outputs = {}
        self.valid_crtcs = {}
        self.crtcs = {}
        
        self.stateHandled = {}
        
        for output in resources['outputs']:
            output_info = self.d.xrandr_get_output_info(output, resources['config_timestamp'])._data
            
            #self.pp.pprint(self.d.xrandr_get_output_info(output, resources['config_timestamp'])._data)
            self.outputs[output] = output_info
            if output_info['connection'] == 0 and output_info['crtc'] != 0:
                for crt in output_info['crtcs']:
                    if crt not in self.valid_crtcs:
                        self.valid_crtcs[crt] = (self.d.xrandr_get_crtc_info(crt, resources['config_timestamp'])._data)
                        self.stateHandled[crt] = 0
        
        for crtc in resources['crtcs']:
            crtc_info = self.d.xrandr_get_crtc_info(crtc, resources['config_timestamp'])._data

            #self.pp.pprint(self.d.xrandr_get_crtc_info(crtc, resources['config_timestamp'])._data)
            if crtc_info['mode'] != 0 and crtc_info['width'] != 0 and crtc_info['height'] != 0:
                for output in crtc_info['outputs']:
                    outputinfo = self.outputs[output]
                    #print "%s is on" % (outputinfo['name'], )
                self.crtcs[crtc] = crtc_info
        
        #print "OUTPUTs:"
        #self.pp.pprint(self.outputs)
        #print "CRTCs:"
        #self.pp.pprint(self.valid_crtcs)
        #self.pp.pprint(self.crtcs)
        #print "Raw screen resources:"
        #self.pp.pprint(resources)
        
        self.handleChange()
        
    # Main loop, handling events
    def loop(self):
        current = None
        while 1:
            i= self.d.pending_events()
            while i > 0:
                i = i - 1
                e = self.d.next_event()
                
                # sequence handled
                if (self.sequence_number == e._data['sequence_number']):
                    continue
                
                # Window has been destroyed, quit
                if e.type == X.DestroyNotify:
                    sys.exit(0)

                # Screen information has changed
                elif e.type == self.d.extension_event.ScreenChangeNotify:
                    #print 'Screen change'
                    self.handleChange()

                # CRTC information has changed
                elif e.type == self.d.extension_event.CrtcChangeNotify:
                    crtc = e._data['crtc']
                    #print 'CRTC %d change' % (crtc, )
                    #self.sequence_number = e._data['sequence_number']
                    if crtc in self.valid_crtcs:
                        if e._data['mode'] != 0 and e._data['width'] != 0 and e._data['height'] != 0:
                            self.valid_crtcs[crtc] = self.d.xrandr_get_crtc_info(crtc, e._data['timestamp'])._data
                            self.crtcs[crtc] = self.d.xrandr_get_crtc_info(crtc, e._data['timestamp'])._data
                                
                            for output in self.crtcs[crtc]['outputs']:
                               outputinfo = self.outputs[output]
                               #print "%s is on now" % (outputinfo['name'], )
                        else:
                            if crtc in self.crtcs:
                                for output in self.crtcs[crtc]['outputs']:
                                    outputinfo = self.outputs[output]
                                    #print "%s is off now" % (outputinfo['name'], )
                                del self.crtcs[crtc]
                        
                        self.handleChange()

                # Output information has changed
                elif e.type == self.d.extension_event.OutputChangeNotify:
                    #print 'Output change'
                    if e._data['connection'] == 0 and e._data['crtc'] != 0:
                        self.outputs[e._data['e._data']] = e._data
                    else:
                        if e._data['crtc'] in self.outputs:
                            del self.outputs[e._data['crtc']]
                            
                    self.handleChange()    
                #    self.pp.pprint(self.outputs);

                # Output property information has changed
                #elif e.type == self.d.extension_event.OutputPropertyNotify:
                    #print 'Output property change'
                    #print self.pp.pprint(e._data)

                # Somebody wants to tell us something
                elif e.type == X.ClientMessage:
                    if e.client_type == self.WM_PROTOCOLS:
                        fmt, data = e.data
                        if fmt == 32 and data[0] == self.WM_DELETE_WINDOW:
                            sys.exit(0)
            time.sleep(2)
            self.window.xrandr_get_screen_info()
    
    def handleChange(self):
        #self.pp.pprint(self.stateHandled);
        #self.pp.pprint(self.valid_crtcs);
        #return
        for crt in self.valid_crtcs:
            if len(self.valid_crtcs[crt]['outputs']) > 0:
                output = self.valid_crtcs[crt]['outputs'][0]
                #print output
                
                #self.pp.pprint(output)
                if crt in self.crtcs:
                    print "%s is on" % (self.outputs[output]['name'])
                    if (self.stateHandled[crt] == 0):
                        print " -> switch on"
                        self.stateHandled[crt] = 1
                else:
                    print "%s is off" % (self.outputs[output]['name'])
                    if (self.stateHandled[crt] == 1):
                        print " -> switch off"
                        self.stateHandled[crt] = 0
                    
            
        #self.pp.pprint(self.crtcs);


if __name__ == '__main__':
    Window(display.Display()).loop()

