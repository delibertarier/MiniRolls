#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 - <<'PY'
import importlib.util
from pathlib import Path

root = Path(".").resolve()
spec = importlib.util.spec_from_file_location("formgen", root / "local-runtime" / "formgen.py")
formgen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formgen)

session = formgen.FormSession(formgen.parse("ROLS6002"))
assert [field.typ for field in session.fields] == ["LOOKUP", "LOOKUP", "NUMERIC"]
assert [a["label"] for a in session.actions] == ["SAVE", "CANCEL"]
assert session.handle("enter") == "lookup"

session.fields[0].set_choice("000001", "ACME")
session.handle("tab")
assert session.handle("enter") == "lookup"
session.fields[1].set_choice("000002", "GASOIL")
session.handle("tab")
assert session.handle("char:2") is None
layout = formgen.layout_form(session)
text = "\n".join(layout["lines"])
assert "ROLLS - CREATE ORDER" in text
assert "ACME" in text
assert "GASOIL" in text
assert "[ 00002 ]" in text
assert "(choose with Enter)" not in text

session.handle("tab")
assert session.focused_action()["key"] == "SAVE"
assert session.handle("enter") == "submit"
assert session.values() == ["000001", "000002", "00002"]

blank = formgen.FormSession(formgen.parse("ROLS6002"))
assert blank.handle("enter") == "lookup"
blank.focus = len(blank.fields) + 1
assert blank.handle("enter") == "cancel"
assert blank.handle("esc") == "cancel"

cus = formgen.FormSession(formgen.parse("ROLS6011"))
assert [field.name for field in cus.fields] == ["CUS-NAME"]
prd = formgen.FormSession(formgen.parse("ROLS6021"))
assert [field.name for field in prd.fields] == ["PRD-NAME", "PRD-PRICE", "PRD-STOCK"]

print("PASS: create forms use auto IDs and customer/product pickers")
PY
