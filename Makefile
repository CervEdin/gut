NAME=gut
VERSION=0.0.1
files=$(wildcard *.sh *.sed)
shell_files=$(wildcard *.sh)
programs=$(addprefix bin/, $(files))
shell_programs=$(addprefix bin/, $(shell_files))
INSTALL_DIR=${HOME}/bin/
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

debug: $(shell_programs)
	sed -i -e '2 { /^set -[eu]*xo\{0,1\} pipefail$$/{p;d;}' \
		-e '/^\(set -eu\)\(o\)\{0,1\}/{ s@@\1x\2@;p;d }' \
		-e 's@^@set -euxo pipefail\n@ }' $?

debug_all: debug all
