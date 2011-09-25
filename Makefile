MANDIR=/usr/share/man

man: slug.py.1

man-install:
	install -D slug.py.1 $(DESTDIR)$(MANDIR)/man1/slug.py.1

slug.py.1: slug.py.xml
	xmlto man $?
slug.py.xml: slug.py.txt
	asciidoc -b docbook -d manpage $?

.PHONY: man man-install
