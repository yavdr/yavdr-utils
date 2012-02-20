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
	install -m 644 yavdrdb.hdf $(DESTDIR)/var/lib/

$(CLEAN):
	$(MAKE) -C $(@:-clean=) clean

