#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
forms=Path("forms"); missing=[]
for p in forms.glob("*.LAY"):
    for line in p.read_text().splitlines():
        if line.startswith("MENU "):
            target=line.split("|")[-1].strip()
            if target not in ("BACK","EXIT") and not (forms/f"{target}.LAY").exists():
                missing.append(f"{p}: missing {target}.LAY")
if missing:
    print("\n".join(missing)); raise SystemExit(1)
print("PASS: every menu target has a .LAY")
PY
for t in ROLS6005 ROLS6013 ROLS6023; do
  test -x "bin/ui-$t" || { echo "FAIL: bin/ui-$t missing"; exit 1; }
done
echo "PASS: all list executables exist"
