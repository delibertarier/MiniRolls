#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

test -x bin/mini-rolls
test -x bin/ROLS6100
test -x bin/ROLS6200
test -x bin/ROLS6300
test -s data/orders.dat
test -s data/customers.dat
test -s data/products.dat

./jobs/ROLJ6100.JOB >/tmp/mini-rolls-batch1.txt
grep -q "completed" /tmp/mini-rolls-batch1.txt
./jobs/ROLA6200.JOB >/tmp/mini-rolls-batch2.txt
grep -q "completed" /tmp/mini-rolls-batch2.txt
./jobs/ROLA6300.JOB >/tmp/mini-rolls-batch3.txt
grep -q "daily report" /tmp/mini-rolls-batch3.txt

./tests/source-audit.sh
./tests/dialect.sh
echo "PASS: Mini-ROLLS v9 compile, native persistence seed and batch tests"
echo "NOTE: TUI form flows are interactive and should be checked with ./run.sh"

if grep -R "SCREEN SECTION" cobol/*.COB >/dev/null 2>&1; then
  echo "FAIL: SCREEN SECTION leaked into legacy corpus"
  exit 1
fi
test -x bin/ui-ROLS6002
test -x bin/ui-ROLS6004
test -x bin/ui-ROLS6011
test -x bin/ui-ROLS6021
test -x bin/ui-ROLS6013
test -x bin/ui-ROLS6023
./tests/form-config.sh
./tests/tui-form.sh
./tests/auto-id.sh
echo "PASS: v8 legacy/runtime separation checks"
