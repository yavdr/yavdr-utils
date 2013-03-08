SUBDIRS = common db-utils process-template signal-event dvb-test \
          irserver2uinput lircd2uinput xrandr-eventd
.PHONY: $(SUBDIRS)

ALL = $(addsuffix -all,$(SUBDIRS))
INSTALL = $(addsuffix -install,$(SUBDIRS))
CLEAN = $(addsuffix -clean,$(SUBDIRS))

all: $(ALL)
install: $(INSTALL)
clean: $(CLEAN)

$(ALL): common.h
	$(MAKE) -C $(@:-all=) all

$(INSTALL):
	$(MAKE) -C $(@:-install=) install
	for f in events templates; do \
	  cp -pr $$f $(DESTDIR)/usr/share/yavdr; done
	chmod +x $(DESTDIR)/usr/share/yavdr/events/actions/*
	cp -pr defaults $(DESTDIR)/usr/share/yavdr
	install -d -m 755 $(DESTDIR)/usr/sbin
	install -m 700 untie-packages $(DESTDIR)/usr/sbin
	install -m 700 yavdr-upgrade $(DESTDIR)/usr/sbin
	install -m 700 change-vdr-uid $(DESTDIR)/usr/sbin
	install -m 700 create-initial-database $(DESTDIR)/usr/sbin
	install -m 700 yavdr-post-install $(DESTDIR)/usr/sbin	
	install -d -m 755 $(DESTDIR)/usr/bin
	install -m 755 devilspie-wrapper $(DESTDIR)/usr/bin	
	install -m 755 yavdr-desktop-helper $(DESTDIR)/usr/bin	
	install -d -m 755 $(DESTDIR)/etc/yavdr
	cp -a etc $(DESTDIR)
	cp -a usr $(DESTDIR)
	install -m 755 yavdr-applauncher $(DESTDIR)/usr/bin	
	install -m 755 yavdr-applauncherd $(DESTDIR)/usr/bin	
	install -d -m 755 $(DESTDIR)/etc/dbus-1/system.d/
	install -m 644 org.yavdr.applauncher.conf $(DESTDIR)/etc/dbus-1/system.d
	install -m 755 xrandr-eventd/yavdr-xrandr-eventd $(DESTDIR)/usr/bin


$(CLEAN):
	$(MAKE) -C $(@:-clean=) clean

