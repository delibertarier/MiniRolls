COBC ?= cobc
COPYDIR = copylib
BINDIR = bin
COBFLAGS = -fixed -std=cobol85 -I$(COPYDIR) -ext TXT

INTERACTIVE_SOURCES = \
	cobol/ROLS0001.COB \
	cobol/ROLS6001.COB \
	cobol/ROLS6002.COB \
	cobol/ROLS6003.COB \
	cobol/ROLS6004.COB \
	cobol/ROLS6005.COB \
	cobol/ROLS6010.COB \
	cobol/ROLS6011.COB \
	cobol/ROLS6012.COB \
	cobol/ROLS6013.COB \
	cobol/ROLS6020.COB \
	cobol/ROLS6021.COB \
	cobol/ROLS6022.COB \
	cobol/ROLS6023.COB \
	cobol/ROLS9001.COB \
	cobol/ROLS9002.COB \
	cobol/ROLS9003.COB

.PHONY: setup syntax build clean seed test db

setup:
	@command -v cobc >/dev/null || (echo "Install GnuCOBOL: brew install gnucobol" && exit 1)
	@command -v sqlite3 >/dev/null || (echo "Install SQLite: brew install sqlite" && exit 1)
	@mkdir -p $(BINDIR) data
	@chmod +x jobs/*.JOB tests/*.sh run.sh
	@echo "Dependencies OK"


syntax: setup
	@./tests/source-audit.sh
	@echo "Strict COBOL-85 syntax check"
	@for p in cobol/*.COB; do \
	  echo "Checking $$p"; \
	  $(COBC) -fsyntax-only $(COBFLAGS) $$p || exit 1; \
	done
	@echo "Syntax check complete"

build: syntax
	@echo "Building fixed-format COBOL-85 Mini-ROLLS"
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/mini-rolls $(INTERACTIVE_SOURCES)
	@echo "Building batch ROLS6100"
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ROLS6100 cobol/ROLS6100.COB cobol/ROLS9003.COB
	@echo "Building batch ROLS6200"
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ROLS6200 cobol/ROLS6200.COB cobol/ROLS9003.COB
	@echo "Building batch ROLS6300"
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ROLS6300 cobol/ROLS6300.COB
	@echo "Building local Formgen harness executables"
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6002 local-runtime/harness/UI6002.COB cobol/ROLS6002.COB cobol/ROLS9001.COB cobol/ROLS9002.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6003 local-runtime/harness/UI6003.COB cobol/ROLS6003.COB cobol/ROLS9001.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6004 local-runtime/harness/UI6004.COB cobol/ROLS6004.COB cobol/ROLS9001.COB cobol/ROLS9003.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6011 local-runtime/harness/UI6011.COB cobol/ROLS6011.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6012 local-runtime/harness/UI6012.COB cobol/ROLS6012.COB cobol/ROLS9003.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6021 local-runtime/harness/UI6021.COB cobol/ROLS6021.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6022 local-runtime/harness/UI6022.COB cobol/ROLS6022.COB cobol/ROLS9003.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6005 local-runtime/harness/UI6005.COB cobol/ROLS6005.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6013 local-runtime/harness/UI6013.COB cobol/ROLS6013.COB
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ui-ROLS6023 local-runtime/harness/UI6023.COB cobol/ROLS6023.COB
	@echo "Building seed utility ROLS7999"
	$(COBC) -x $(COBFLAGS) -o $(BINDIR)/ROLS7999 cobol/ROLS7999.COB
	@echo "Build complete"

db:
	@rm -f data/minirolls.db
	sqlite3 data/minirolls.db < sql/schema.sql
	@echo "SQLite local database created: data/minirolls.db"

seed: build
	@rm -f data/orders.dat data/customers.dat data/products.dat data/order_history.dat
	@touch data/order_history.dat
	./bin/ROLS7999
	@echo "Native COBOL sequential seed files created"

test: seed
	./tests/smoke.sh

clean:
	rm -rf $(BINDIR)/* data/minirolls.db
