#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

echo "Auditing fixed-format COBOL sources..."

if grep -RniE '^[0-9]{6} .*\bGOBACK\b' cobol/*.COB; then
  echo "FAIL: GOBACK is outside the strict COBOL-85 benchmark profile"
  exit 1
fi

if grep -RniE '^[0-9]{6} .*>|^[0-9]{6} .*\bCONTINUE\b' cobol/*.COB >/dev/null 2>&1; then
  : # CONTINUE is valid COBOL-85; retained intentionally.
fi

# Every source must be fixed format with six sequence columns + indicator column.
for f in cobol/*.COB; do
  awk 'length($0)>0 && $0 !~ /^[0-9]{6}[ *-]/ {print FILENAME ":" NR ": invalid fixed-format prefix"; bad=1} END {exit bad}' "$f"
done

echo "PASS: source audit"

echo "Checking fixed-format 72-column boundary..."
python3 - <<'PY'
from pathlib import Path
bad=[]
for root in ("cobol","copylib"):
    for p in Path(root).glob("*"):
        if not p.is_file():
            continue
        if root == "copylib" and p.name.upper() == "COPYLIB.TLB":
            continue
        if root == "copylib" and p.suffix.upper() != ".TXT":
            continue
        if root == "cobol" and p.suffix.upper() != ".COB":
            continue
        for n,line in enumerate(p.read_text(errors="ignore").splitlines(),1):
            if len(line) > 72:
                bad.append((str(p),n,len(line),line))
if bad:
    for p,n,l,line in bad:
        print(f"FAIL: {p}:{n} has {l} columns: {line}")
    raise SystemExit(1)
print("PASS: all COBOL/copybook lines fit fixed-format columns")
PY

echo "Checking for fixed-format continuation lines..."
if grep -n '^......-' cobol/*.COB copylib/*.TXT >/tmp/mini-rolls-cont.txt 2>/dev/null; then
  cat /tmp/mini-rolls-cont.txt
  echo "FAIL: continuation lines are intentionally disallowed in this corpus"
  exit 1
fi
echo "PASS: no fixed-format continuation lines"

echo "Checking ROLS6002 calculation parameters..."
grep -q '01 P PIC 9(6).' cobol/ROLS6002.COB || {
  echo "FAIL: P declaration missing in ROLS6002"; exit 1; }
grep -q '01 Q PIC 9(5).' cobol/ROLS6002.COB || {
  echo "FAIL: Q declaration missing in ROLS6002"; exit 1; }
grep -q 'CALL "ROLS9002" USING P Q WS-AMOUNT' cobol/ROLS6002.COB || {
  echo "FAIL: ROLS9002 parameter call mismatch"; exit 1; }
echo "PASS: ROLS6002 calculation parameters declared"
