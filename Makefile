SUBDIRS = common db-utils process-template signal-event dvb-test 
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
	install -m 644 helpers/hdf_prefill $(DESTDIR)/usr/share/yavdr/helpers/
	install -m 644 helpers/conffiles $(DESTDIR)/usr/share/yavdr/helpers/
	install -m 755 scripts/yavdr-db-tool $(DESTDIR)/usr/bin/
	install -m 755 scripts/yavdr-db-dump $(DESTDIR)/usr/bin/

$(CLEAN):
	$(MAKE) -C $(@:-clean=) clean

