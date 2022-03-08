NAME=gut
VERSION=0.0.1

INSTALL_DIR=$${HOME}/bin/

install:
	mkdir -p $(INSTALL_DIR) 
	find -name 'git-*.sh' |\
		sed 's@^./\(.*\)\.sh$$@./\1.sh\n'$(INSTALL_DIR)'\1@' |\
		xargs -n 2 cp
