CFLAGS=-g

all: lircd2uinput.py lircd2uinput.conf

clean:

install:
	@install -m 755 -d $(DESTDIR)/usr/bin
	@install -m 755 lircd2uinput $(DESTDIR)/usr/bin
	@install -m 755 -d $(DESTDIR)/etc/init
	@install -m 644 lircd2uinput.conf $(DESTDIR)/etc/init
