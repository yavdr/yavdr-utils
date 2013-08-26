CFLAGS=-g -fPIC -DUSE_UPSTART
LDLIBS=-lrt

all: xorg-launch-helper

xorg-launch-helper: xorg-launch-helper.o

clean:
	@rm -rf xorg-launch-helper *.o

install:
	@install xorg-launch-helper $(DESTDIR)/usr/bin/
