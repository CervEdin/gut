NAME=gut
VERSION=0.0.1

INSTALL_DIR=$${HOME}/bin/

install:
	mkdir -p $(INSTALL_DIR) 
	find -name 'git-*' \( -name '*.sed' -o -name '*.sh' \) |\
		sed 's@^./\(.*\)\(\.[A-z]\{1,4\}\)$$@./\1\2\n'$(INSTALL_DIR)'\1@' |\
		xargs -n 2 cp
