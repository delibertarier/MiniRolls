#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

if grep -RniE '^[0-9]{6} .*\bGOBACK\b' cobol/*.COB; then
  echo "FAIL: GOBACK found; strict COBOL-85 baseline requires STOP RUN or EXIT PROGRAM"
  exit 1
fi

for p in ROLS0001 ROLS6100 ROLS6200 ROLS6300; do
  grep -q 'STOP RUN' "cobol/$p.COB" || {
    echo "FAIL: $p must terminate with STOP RUN"
    exit 1
  }
done

for p in ROLS6001 ROLS6002 ROLS6003 ROLS6004 ROLS6005 ROLS6010 ROLS6011 ROLS6012 ROLS6013 ROLS6020 ROLS6021 ROLS6022 ROLS6023 ROLS9001 ROLS9002 ROLS9003; do
  grep -q 'EXIT PROGRAM' "cobol/$p.COB" || {
    echo "FAIL: $p must return with EXIT PROGRAM"
    exit 1
  }
done

echo "PASS: COBOL-85 dialect termination checks"
