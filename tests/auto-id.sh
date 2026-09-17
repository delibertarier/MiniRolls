#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
ROLLS_ROOT="$(pwd)"
. ./local-runtime/logicals.sh

out=$(printf 'CONTOSO\n' | ./bin/ui-ROLS6011)
echo "$out" | grep -q "OK CUSTOMER STORED ID 000003"

out=$(printf 'KEROSENE\n000001500\n0000500\n' | ./bin/ui-ROLS6021)
echo "$out" | grep -q "OK PRODUCT STORED ID 000003"

out=$(printf '000003\n000003\n4\n' | ./bin/ui-ROLS6002)
echo "$out" | grep -q "OK ORDER CREATED ID 000003"

python3 - <<'PY'
from pathlib import Path
cus = Path("data/customers.dat").read_bytes()
prd = Path("data/products.dat").read_bytes()
ordr = Path("data/orders.dat").read_bytes()
assert cus[92:98] == b"000003", cus[92:138]
assert b"CONTOSO" in cus[98:128]
assert prd[104:110] == b"000003", prd[104:]
assert b"KEROSENE" in prd[110:140]
assert ordr[88:94] == b"000003"
assert ordr[94:100] == b"000003"
assert ordr[100:106] == b"000003"
print("PASS: next IDs assigned and persisted")
PY
