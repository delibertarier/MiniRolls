#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

# Corpus must look like HP COBOL II / OpenVMS ROLLS, not a Unix rewrite.
if grep -n 'ASSIGN TO "' cobol/*.COB; then
  echo "FAIL: quoted ASSIGN paths belong in local logical mapping, not COBOL"
  exit 1
fi
if grep -nE 'ASSIGN TO .*(/|data/)' cobol/*.COB; then
  echo "FAIL: POSIX paths in ASSIGN; use OpenVMS-style logical names"
  exit 1
fi
if grep -n 'SCREEN SECTION' cobol/*.COB; then
  echo "FAIL: SCREEN SECTION is not the ROLLS Formgen architecture"
  exit 1
fi
if grep -nE 'EXEC[ ]+SQL' cobol/*.COB; then
  echo "FAIL: embedded SQL belongs in sql/ fixtures, not compiled local COBOL (no Oracle/Pro*COBOL license)"
  exit 1
fi

grep -q 'ASSIGN TO ORDERS' cobol/ROLS6002.COB
grep -q 'ASSIGN TO CUSTOMERS' cobol/ROLS6011.COB
grep -q 'ASSIGN TO PRODUCTS' cobol/ROLS6021.COB
grep -q 'ASSIGN TO HISTORY' cobol/ROLS6004.COB
grep -q 'ASSIGN TO ORDERS' cobol/ROLS7999.COB
grep -q 'ASSIGN TO CUSTOMERS' cobol/ROLS7999.COB
grep -q 'ASSIGN TO PRODUCTS' cobol/ROLS7999.COB

echo "PASS: ASSIGN logicals, no SCREEN SECTION, no compiled EXEC SQL"
