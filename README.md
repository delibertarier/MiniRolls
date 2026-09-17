# Mini-ROLLS v8 — candidate legacy baseline

Mini-ROLLS v8 separates the **as-is legacy corpus** from the **local macOS
execution harness**.

## Legacy corpus (input to modernization tooling)

- `cobol/` — strict fixed-format ANSI COBOL-85 programs
- `copylib/` — ROLLS-style copy members
- `forms/` — Formgen-like `.LAY` screen definitions
- `jobs/` — user and automatic jobs
- `sql/` — SQL and Oracle-oriented database artifacts
- `requirements/` — functional and technical requirements
- `Application_cob.lst`, `Cobjobs.lst`

There is deliberately **no `SCREEN SECTION`** in the COBOL corpus. Screen
definitions live in `.LAY` artifacts, reflecting the architecture described in
the supplied ROLLS development material.

## Production architecture vs local stand-in

Full ROLLS on the SIROL OpenVMS Integrity cluster uses HP COBOL II/XL
(ANSI COBOL 85, with 1974 compatibility), Formgen screens, Oracle SQL, and
DCL jobs. Mini-ROLLS mirrors that shape so discovery still sees ROLSnnnn
programs, copy members, .LAY forms, jobs and Oracle SQL — without HP COBOL,
VSI OpenVMS, commercial Formgen or Oracle licenses, and while remaining
runnable on an Apple Silicon Mac.

| Production ROLLS | Mini-ROLLS local (M1) |
| --- | --- |
| HP COBOL II/XL, ANSI 85 | GnuCOBOL `-fixed -std=cobol85` (Homebrew, no license) |
| OpenVMS RMS + DCL logicals (`ASSIGN TO ORDERS`) | Same ASSIGN names; GnuCOBOL EXTERNAL maps them to env vars |
| Formgen (.LAY, no SCREEN SECTION) | Same .LAY corpus; `local-runtime/formgen.py` emulator |
| Oracle + embedded SQL | SQL fixtures in `sql/` only; not compiled (no Pro*COBOL/Oracle) |
| Sequential/SQL data on SIROL | Sequential files under `data/` via logicals `ORDERS`, `CUSTOMERS`, `PRODUCTS`, `HISTORY` |
| User job ROLJ / automatic ROLA | Same names; POSIX `sh` with DCL analog comments |
| Copy library `.TLB` | `copylib/COPYLIB.TLB` manifest + `COPY ... TXT` |

Do **not** compile `EXEC SQL` into the macOS binaries. Do **not** add
`SCREEN SECTION`. Those would either demand licenses we cannot use, or
diverge from the Formgen architecture.

A full mapping (production SIROL versus this subset, including what is
intentionally not cloned) is in [ROLLS-ALIGNMENT.md](ROLLS-ALIGNMENT.md).

The functional and technical analysis (what this version delivers, what is
explicitly not present yet, and the technical design) is in
[ANALYSE.md](ANALYSE.md).

## Local-only runtime

`local-runtime/` is a development harness and must NOT be supplied to Graphify
or other legacy discovery tools.

It contains a small Python-standard-library Formgen emulator. It reads `.LAY`
files and draws a boxed terminal form. The cursor sits inside `[ ]`; typing
edits that field in place; Tab/Enter moves to the next field; values stay
visible until SAVE or CANCEL. Create forms assign the next ID automatically.
On Create Order, Enter on Customer or Product opens a list so the operator can
pick a name instead of typing an identifier. SAVE invokes a small compiled
harness around the corresponding COBOL program. The COBOL corpus itself remains
ACCEPT-based and has no `SCREEN SECTION`.

The COBOL business programs remain strict:

    -fixed -std=cobol85

Runtime data uses native COBOL sequential files. ROLS7999 is a test-only seed
utility.

## Run on macOS

```bash
brew install gnucobol sqlite
make clean
make syntax
make build
make db
make seed
make test
./run.sh
```

## Benchmark rule

For discovery experiments, use only:

```text
cobol/
copylib/
forms/
jobs/
sql/
requirements/
Application_cob.lst
Cobjobs.lst
```

Exclude:

```text
local-runtime/
tests/ground-truth.md
bin/
data/
ANALYSE.md
ROLLS-ALIGNMENT.md
```

`tests/ground-truth.md` is evaluation truth, never model input.

## v8.1 fix

v8.1 fixes a fixed-format truncation found by the strict compiler in
ROLS6002. The ROLS9002 CALL now uses a proper continuation line. The seed
utility ROLS7999 was also rewritten because its long source lines would have
been the next fixed-format failures. The source audit now explicitly rejects
COBOL/copybook lines extending beyond column 72.

## v8.2 fix

The 72-column source audit now checks only actual fixed-format COBOL source
(`cobol/*.COB`) and copy members (`copylib/*.TXT`). `COPYLIB.TLB` is a copy
library manifest, not COBOL source, and is therefore intentionally excluded.

## v8.3 fix

The previous v8.1 continuation was incorrect: in fixed-format COBOL an indicator
column `-` continues the previous lexical token, which caused
`ORD-PRODUCT-IDORD-QUANTITY`. v8.3 removes that continuation completely.
ROLS6002 uses short local parameter names for the ROLS9002 CALL. The source
audit now rejects continuation lines in this benchmark corpus so this class of
mistake cannot recur.

## v8.4 fix

v8.3 referenced short parameters P and Q but failed to declare them in
WORKING-STORAGE. v8.4 explicitly declares P as PIC 9(6) and Q as PIC 9(5)
immediately after WS-AMOUNT, and the source audit verifies that the
declarations and ROLS9002 call stay consistent.

## v9
Adds List Customers (ROLS6013) and List Products (ROLS6023). Orders,
Customers and Products now all have a list function. ROLS6005.LAY is included,
fixing the List Orders FileNotFoundError. The local runtime validates menu
targets before startup, and tests/form-config.sh guards this configuration.
