SUBDIRS =  mcell3 mcell3dm mcell3r cBNGL limited_python limited_cpp smoldyn248 Proto_Andreas_1

.PHONY: all
all: subdirs


.PHONY: subdirs $(SUBDIRS)
subdirs: makefile $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@


.PHONY: clean
clean:
	(cd mcell3 ; make clean)
	(cd limited_python ; make clean)
	-(cd limited_cpp ; make clean)

