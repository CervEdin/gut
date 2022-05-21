NAME=gut
VERSION=0.0.1
files=$(wildcard *.sh *.sed)
programs=$(addprefix bin/, $(files))
INSTALL_DIR=$${HOME}/bin/
installed_programs=$(addprefix $(INSTALL_DIR), $(notdir $(programs)))
installed_links=$(basename $(installed_programs))

bin:
	mkdir bin

bin/%.sh : %.sh
	cp $< $@

bin/%.sed : %.sed
	cp $< $@

$(programs): | bin

$(INSTALL_DIR):
	mkdir $(INSTALL_DIR)

ls:
	echo $(installed_programs)
	echo $(installed_links)
	echo $(INSTALL_DIR)

$(INSTALL_DIR)%.sh : bin/%.sh
	cp $< $@
	chmod +x $@

$(INSTALL_DIR)%.sed : bin/%.sed
	cp $< $@
	chmod +x $@

$(INSTALL_DIR)% : $(INSTALL_DIR)%.sh
	ln -fs $< $@

$(INSTALL_DIR)% : $(INSTALL_DIR)%.sed
	ln -fs $< $@

all: $(installed_programs) $(installed_links)

uninstall:
	find $(installed_programs) $(installed_links) -delete

clean:
	rm bin/*

debug: $(programs)
	sed -i '2 { /^set -euox$$/{p;d;} ; /^\(set -euo\)\([^x]\)/{ s@@\1x\2@;p;d } ; s@^@set -euox\n@ }' $?

debug_all: debug all
