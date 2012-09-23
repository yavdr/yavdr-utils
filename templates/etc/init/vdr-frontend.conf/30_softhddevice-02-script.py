import sys, os, subprocess, gobject, dbus, socket, string, struct, datetime, syslog, pyudev
from pyudev.glib import GUDevMonitorObserver

bus = dbus.SystemBus()

def sendremote(key):
    dbusremote = bus.get_object("de.tvdr.vdr","/Remote")
    answer, message = dbusremote.HitKey(dbus.String(key),dbus_interface='de.tvdr.vdr.remote')
    if answer == 250:
        return True
    else:
        return False

def remote(signal):
    dbusremote = bus.get_object("de.tvdr.vdr","/Remote")
    answer = None
    message = None
    if signal == "enable":
         answer, message = dbusremote.Enable(dbus_interface='de.tvdr.vdr.remote')
    elif signal == "disable":
         answer, message = dbusremote.Disable(dbus_interface='de.tvdr.vdr.remote')
    elif signal == "status":
         answer, message = dbusremote.Status(dbus_interface='de.tvdr.vdr.remote')
    return answer, message

def manualstart():
    dbusshutdown = bus.get_object("de.tvdr.vdr","/Shutdown")
    return dbusshutdown.ManualStart(dbus_interface='de.tvdr.vdr.shutdown')

def confirmShutdown(user=False):
    dbusshutdown = bus.get_object("de.tvdr.vdr","/Shutdown")
    code, message, shutdownhooks, message = dbusshutdown.ConfirmShutdown(dbus.Boolean(user),dbus_interface='de.tvdr.vdr.shutdown')
    if code in [250,990]: return True
    else:
        syslog.syslog(u"vdr won't shutdown: %s: %s"%(code,message))
        return False

def setUserInactive():
    dbusshutdown = bus.get_object("de.tvdr.vdr","/Shutdown")
    dbusshutdown.SetUserInactive(dbus_interface='de.tvdr.vdr.shutdown')
    send_shutdown()
    settings.time = gobject.timeout_add(300000,send_shutdown)

def vdrsetupget(option):
    dbussetup = bus.get_object("de.tvdr.vdr","/Setup")
    return dbussetup.Get(dbus.String(option),dbus_interface='de.tvdr.vdr.setup')

def get_status():
    dbusfstatus =  bus.get_object("de.tvdr.vdr","/Plugins/softhddevice")
    code, mode = dbusfstatus.SVDRPCommand(dbus.String("STAT"),dbus.String(None),dbus_interface='de.tvdr.vdr.plugin')
    return mode.split()[-1]

def frontend(command,value=None):
    dbusdetach = bus.get_object("de.tvdr.vdr","/Plugins/softhddevice")
    reply, answer = dbusdetach.SVDRPCommand(dbus.String(command),dbus.String(value),dbus_interface='de.tvdr.vdr.plugin')
    dbusremote = bus.get_object("de.tvdr.vdr","/Remote")
    if command == "DETA":
        remote("disable")
    if command == "ATTA":
        remote("enable")

def detach():
    frontend("DETA")
    return True

def send_shutdown():
    if confirmShutdown():
        dbusremote = bus.get_object("de.tvdr.vdr","/Remote")
        answer, message =  dbusremote.Enable(dbus_interface='de.tvdr.vdr.remote')
        sendremote("POWER")
        answer, message =  dbusremote.Disable(dbus_interface='de.tvdr.vdr.remote')
    return True

def soft_detach():
    frontend("DETA")
    settings.timer = gobject.timeout_add(300000,send_shutdown)
    return False

def resume(status):
    if status == "SUSPENDED":
        frontend("RESU")
    elif status == "SUSPEND_DETACHED":
        frontend("ATTA","-d %s"%(settings.env["DISPLAY"]))

class Settings():
    def __init__(self):
        global gobject
        self.frontend_active = 0
        self.env = os.environ
        self.timer = None
        self.updateDisplay()
        self.manualstart = manualstart()
        try:
            self.acpi_wakeup = self.check_acpi()
        except:
            self.acpi_wakeup = None
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='input')
        self.devices = {}
        self.paths = {}
        self.inputEventFormat = 'llHHi'
        self.inputEventSize = 24
        self.conf = {
        'logo_detached':"/usr/share/yavdr/images/yaVDR_background_detached.jpg",
        'key_detach':"KEY_PROG1",
        'key_power':"KEY_POWER2"
        }
        for i in self.conf:
            if i in os.environ:
                self.conf[i] = os.environ[i]
        self.get_event_devices()

    def get_event_devices(self):
        for device in self.context.list_devices(subsystem='input',ID_INPUT_KEYBOARD=True):
            if device.sys_name.startswith('event') and not (('eventlircd_enable' in device) or ('eventlircd_enable' in device and device['eventlircd_enable'] is ('true'))):
                self.paths[device['DEVNAME']] = open(device['DEVNAME'],'rb')
                print "watching %s: %s"%(device.parent['NAME'], device['DEVNAME'])
                #print self.paths[device['DEVNAME']]
                self.devices[device['DEVNAME']] = gobject.io_add_watch(self.paths[device['DEVNAME']], gobject.IO_IN, self.evthandler)
        self.observer = GUDevMonitorObserver(self.monitor)
        self.observer.connect('device-event',self.udev_event)
        self.monitor.start()
        #print "started udev monitor"

    def udev_event(self,observer,action, device):
        if action == "add":
            print "added %s"%device['DEVNAME']
            if not "eventlircd_enable" in device:
                self.paths[device['DEVNAME']] = open(device['DEVNAME'],'rb')
                print "watching %s: %s"%(device.parent['NAME'], device['DEVNAME'])
                print self.paths[device['DEVNAME']]
                self.devices[device['DEVNAME']] = gobject.io_add_watch(self.paths[device['DEVNAME']], gobject.IO_IN, self.evthandler)
        elif action == "remove":
            try:
		self.paths[device['DEVNAME']].close()
            except:
                pass
            print "removed %s"%device['DEVNAME']
            gobject.source_remove(self.devices[device['DEVNAME']])

    def GetActiveWindowTitle(self):
        return subprocess.Popen(["xprop", "-id", subprocess.Popen(["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE, env=settings.env).communicate()[0].strip().split()[-1], "WM_NAME"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip().split('"', 1)[-1][:-1]

    def evthandler(self,path, *args):
        try:
            event = path.read(self.inputEventSize)
        except:
            print "Fehler"
            return False
        (time1, time2, typeev, code, value) = struct.unpack(self.inputEventFormat, event)
        
        if typeev == 1 and code == 115:
           #print "Volume+"
           sendremote("Volume+") 
	if typeev == 1 and code == 114:
           #print "Volume-"
           sendremote("Volume-")
        if typeev == 1 and code == 113 and value == 1:
           #print "Muting"
           sendremote("Mute")
        if typeev == 1 and code == 172 and value == 1:
           #print "Home"          
           if self.frontend_active == 1:
               #print "KEYBOARD: detach frontend"
               frontend("DETA")
               self.frontend_active = 0
           elif self.frontend_active == 0:
               #print "KEYBOARD:attach frontend"
               resume(get_status())
               self.frontend_active = 1
        if self.frontend_active == 0:
           if typeev == 1 and code == 28 and self.GetActiveWindowTitle() == 'WM_NAM':
               syslog.syslog("frontend attached by keyboard activity")
               resume(get_status())
               self.frontend_active = 1 
        return True

        
    def updateDisplay(self):
        self.env["DISPLAY"] = <?cs alt:desktop_display ?>":1"<?cs /alt ?>+self.getTempDisplay()
        
    def getTempDisplay(self):
        return subprocess.check_output(["dbget","vdr.tempdisplay"])
        
    def check_acpi(self):
        timestr = open('/var/cache/vdr/acpiwakeup.time.old','r').read().splitlines()[0]
        wakeup = datetime.datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.utcnow()
        print u"acip-wakeup.time.old hatte Wert: %s"%(wakeup.ctime())
        print u"vergleiche mit jetzt: %s"%(now.ctime())
        if wakeup < now:
            d = now - wakeup
        else:
            d = wakeup - now
        if d.seconds > 360:
            print "assuming manual start"
            return False
        else:
            print "assuming start for acpi-wakeup"
            return True

def handler(sock, *args):
    buf = sock.recv(1024)
    lines = string.split(buf, "\n")
    for line in lines[:-1]:
        try:
             gobject.source_remove(settings.timer)
             #print "removed timer"
        except: pass
        code,count,cmd,device = string.split(line, " ")
        if cmd == settings.conf['key_detach']:#"KEY_PROG1":
            if get_status() == "NOT_SUSPENDED":
                detach()
                settings.frontend_active = 0
            else:
                resume(get_status())
        elif cmd == settings.conf['key_power']:#"KEY_POWER2":
            if get_status() == "NOT_SUSPENDED":
                settings.timer = gobject.timeout_add(15000,soft_detach)
                settings.frontend_active = 0
            else:
                send_shutdown()
        else:
            if settings.frontend_active == 0:
                resume(get_status())
                settings.frontend_active = 1
            else:
                pass
    return True


settings = Settings()
subprocess.call(["/usr/bin/hsetroot","-full",settings.conf['logo_detached']], env=settings.env)
if settings.manualstart == True and settings.acpi_wakeup != True:
    resume(get_status())
else:
    if settings.manualstart == False:
        settings.timer = gobject.timeout_add(300000, send_shutdown)
    elif settings.acpi_wakeup == True:
        interval, default, answer = vdrsetupget("MinEventTimeout")
        interval_ms = interval  * 60000 # * 60s * 1000ms
        settings.timer = gobject.timeout_add(interval_ms, setUserInactive)   
    remote("disable")

def connect_eventlircd():
    socket_path = "/var/run/lirc/lircd"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)
    gobject.io_add_watch(sock, gobject.IO_IN, handler)

def try_connection():
  try:
      connect_eventlircd()
  except:
    print "Error: could not connect to eventlircd"

try_connection()
gobject.MainLoop().run()

