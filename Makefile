NAME=gut
VERSION=0.0.1
files=$(wildcard *.sh *.sed)
shell_files=$(wildcard *.sh)
programs=$(addprefix bin/, $(files))
shell_programs=$(addprefix bin/, $(shell_files))
INSTALL_DIR=${HOME}/bin
installed_programs=$(addprefix $(INSTALL_DIR)/, $(notdir $(programs)))
installed_links=$(basename $(installed_programs))

default: all

bin:; mkdir -p $@

bin/%.sh : %.sh | bin
	cp $< $@

bin/%.sed : %.sed | bin
	cp $< $@

$(INSTALL_DIR):; mkdir -p $(INSTALL_DIR)

.PHONY: help
## Display helpful information:
##   - which gut programs are installed
##   - the installation directory
##   - the most relevant targets
## and other helpful information.
help:
	$(info installed programs are: $(installed_programs))
	$(info installed links are:  $(installed_links))
	$(info installation directory:  $(INSTALL_DIR))
	@printf "\n"
	@printf "A (non-exhaustive and generated) list of available targets:\n\n"
	@awk -f list-make-targets.awk \
		$(MAKEFILE_LIST) | sort | sed 's/\r/\n\t\t/g'
	@echo "for a full list, please consult the make file"

$(INSTALL_DIR)/%.sh : bin/%.sh | $(INSTALL_DIR)
	cp $< $@
	chmod +x $@

$(INSTALL_DIR)/%.sed : bin/%.sed | $(INSTALL_DIR)
	cp $< $@
	chmod +x $@

$(INSTALL_DIR)/% : $(INSTALL_DIR)/%.sh
	ln -fs $< $@

$(INSTALL_DIR)/% : $(INSTALL_DIR)/%.sed
	ln -fs $< $@

## Make all of gut
all: $(installed_programs) $(installed_links)

## Uninstall all of gut
uninstall:
	find $(installed_programs) $(installed_links) -delete

clean:
	rm bin/*

## Compile all bash scripts with flags to
##   set -e fail on error
##   set -u fail on unbound variable
##   set -o pipefail erros in pipeilines
debug: $(shell_programs)
	sed -i -e '1 { /^#!\/bin\/bash$$/!q; }' \
		-e '2 { /^set -[eu]*xo\{0,1\} pipefail$$/{p;d;}' \
		-e '/^\(set -eu\)\(o\)\{0,1\}/{ s@@\1x\2@;p;d }' \
		-e 's@^@set -euxo pipefail\n@ }' $?

debug_all: debug all

.PHONY: lint
## Run linter on files in project
lint: \
	lint-python \
	lint-shell

.PHONY: lint-python
## Run autopep8 on python files and fix the following errors:
## E301 - Add missing blank line.
## E302 - Add missing 2 blank lines.
## E303 - Remove extra blank lines.
## E304 - Remove blank line following function decorator.
## E305 - Expected 2 blank lines after end of function or class.
## E306 - Expected 1 blank line before a nested definition.
lint-python: **/*.py
	autopep8 -i --select=E301,E302,E303,E304,E305,E306 $^

.PHONY: lint-shell
## Run shellcheck on all shell scripts.
lint-shell: **/*.sh
	shellcheck -f gcc $^
