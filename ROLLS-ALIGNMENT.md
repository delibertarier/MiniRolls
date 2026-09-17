# Alignment Mini-ROLLS met productie-ROLLS

Dit document beschrijft hoe Mini-ROLLS de architectuur van de bestaande
ROLLS-applicatie volgt, wat lokaal een stand-in is, en wat bewust niet
nagebouwd wordt. Doel: discovery en modernisering zien dezelfde *vorm*
als op het productiesysteem, terwijl de subset op een Apple Silicon Mac
draait zonder HP COBOL, OpenVMS, commercieel Formgen of Oracle.

## 1. Productie-ROLLS (as-is)

ROLLS draait op het SIROL-cluster (HP Integrity RX2800 i2, OpenVMS):

| Onderdeel | Productie |
| --- | --- |
| Platform | OpenVMS Integrity (Itanium), cluster SIROL7 / SIROL8 / SIROL9 |
| Compiler | HP COBOL II/XL, primair ANSI COBOL 1985 (X3.23-1985), ook 1974-compatibel |
| Schermen | Formgen-layouts; COBOL heeft geen `SCREEN SECTION` |
| Data | Oracle (embedded SQL in het analysemodel) plus files via DCL-logicals |
| Jobs | DCL: user jobs versus automatic jobs |
| Programma’s | `ROLSnnnn` — interactief 60xx, batch 61–63xx, gemeenschappelijk 90xx |
| Copy library | Tekstbibliotheek (`.TLB`) met copy members |

Mini-ROLLS is geen port van die stack. Het is een representatieve subset met
dezelfde artefactsoorten en naamgeving.

## 2. Wat Mini-ROLLS wél gelijk trekt

### Taal en bronvorm

- Vast (fixed/reference) formaat, kolom 72, sequence numbers.
- Dialect ANSI COBOL 85: `EXIT PROGRAM` in subprogramma’s, `STOP RUN` in
  batch/hoofdprogramma’s. Geen `GOBACK`, geen continuatieregels in deze
  corpus.
- Lokaal: GnuCOBOL `cobc -fixed -std=cobol85`. Dat is de licentievrije
  analogie van HP COBOL II, geen vervanging van de HP-compiler in productie.

### Programmafamilies en catalogi

| Familie | Rol | Mini-ROLLS |
| --- | --- | --- |
| `ROLS0001`, `ROLS60x0` | Menu’s | Aanwezig in corpus en `.LAY` |
| `ROLS6002` / `6011` / `6021` | Create order / klant / product | Uitvoerbaar |
| `ROLS6005` / `6013` / `6023` | Lijsten | Uitvoerbaar |
| `ROLS6003` / `6004` | Modify / cancel | Schermen en programma’s bestaan; volledige persistentie volgt later |
| `ROLS6012` / `6022` | Zoeken | Plaatsaanduiding |
| `ROLS6100` / `6200` / `6300` | Batch | Jobs + binaries; verwerking is plaatsaanduiding |
| `ROLS90xx` | Validatie, bedrag, lookup | 9001 actief; 9002/9003 vereenvoudigd |
| `Application_cob.lst` / `Cobjobs.lst` | Compile-lijsten interactief vs batch | Zelfde splitsing als legacy |

### Formgen, geen SCREEN SECTION

Productie-ROLLS legt schermen buiten COBOL. Mini-ROLLS doet dat ook:

- Layouts in `forms/*.LAY` (`FORM`, `TITLE`, `MENU`, `FIELD`, `ACTION`).
- COBOL-programma’s blijven `ACCEPT` / `DISPLAY`.
- `tests/architecture.sh` weigert `SCREEN SECTION` in `cobol/`.

Lokaal tekent `local-runtime/formgen.py` de `.LAY` als terminalformulier.
Dat is een emulator, geen gelicentieerd Formgen-product. De emulator hoort
**niet** bij Graphify-input (`local-runtime/` uitsluiten).

### OpenVMS-logicals in FILE-CONTROL

Op OpenVMS wijst `ASSIGN TO ORDERS` naar een DCL-logical. Mini-ROLLS gebruikt
dezelfde implementor-names, geen POSIX-paden in COBOL:

```cobol
SELECT ORDER-FILE ASSIGN TO ORDERS
  ORGANIZATION IS SEQUENTIAL.
```

GnuCOBOL `-std=cobol85` behandelt dat als `ASSIGN EXTERNAL`. De lokale mapping
staat in `local-runtime/logicals.sh` (en in de TUI):

| Logical | Lokaal bestand |
| --- | --- |
| `ORDERS` | `data/orders.dat` |
| `CUSTOMERS` | `data/customers.dat` |
| `PRODUCTS` | `data/products.dat` |
| `HISTORY` | `data/order_history.dat` |

`./run.sh`, `make seed` en `jobs/*.JOB` sourcen die mapping. COBOL blijft
daardoor ontdekbaar als OpenVMS-achtig; het pad zit alleen in de runtime.

### Jobs: user vs automatic

| Productie (DCL) | Mini-ROLLS |
| --- | --- |
| User job, handmatig | `jobs/ROLJ6100.JOB` → `ROLS6100` |
| Automatic stock | `jobs/ROLA6200.JOB` → `ROLS6200` |
| Automatic rapport | `jobs/ROLA6300.JOB` → `ROLS6300` |

De bestanden zijn uitvoerbare POSIX-shell (nodig op macOS) met DCL-analogie
in commentaar (`$ SET DEFAULT` / `$ RUN`), zodat de jobnaam en het
programma-doel gelijk blijven.

### Copy library

`copylib/COPYLIB.TLB` is het manifest (rol van de legacy `.TLB`).
Members `CPM-ORDER`, `CPM-CUSTOMER`, `CPM-PRODUCT`, `CPM-PAR9001`,
`CPM-COMMON` worden met `COPY` en `-ext TXT` ingelezen — dezelfde scheiding
tussen structuur en programma als in ROLLS.

### Oracle als analysemodel, niet als runtime

Productie-ROLLS praat met Oracle. Mini-ROLLS compileert **geen** `EXEC SQL`
(dat zou Pro*COBOL/Oracle vragen). Het logische model ligt in `sql/`:

- `oracle-as-is-schema.sql` — Oracle-achtige as-is
- `schema.sql` — zelfde model, lokaal als SQLite-analysebestand (`make db`)
- `ROLS6200.SQL` / `ROLS6300.SQL` — batch-SQL als artefact
- `embedded-sql-examples.cbl.txt` — voorbeeld `EXEC SQL`, niet gelinkt

SQLite is alleen een licentievrije leesbaarheidscheck van dat schema.
COBOL leest sequential files, geen database.

## 3. Bewuste stand-ins (licentie- en platformgrens)

Deze keuzes zijn verplicht om lokaal op M1 te blijven draaien:

| Niet gebruiken | Waarom | Stand-in |
| --- | --- | --- |
| HP COBOL II/XL | Propriëtaire compiler | GnuCOBOL 85 |
| VSI OpenVMS / Integrity | Geen SIROL-hardware of OpenVMS-licentie | macOS + env-logicals |
| Commercieel Formgen | Licentie | Python stdlib-emulator |
| Oracle RDBMS + Pro*COBOL | Licentie | Sequential files + SQL-fixtures |
| RMS indexed / cluster quorum | Geen OpenVMS RMS | `ORGANIZATION IS SEQUENTIAL` |

Regels die deze grens bewaken: REQ-TEC-007, REQ-TEC-008,
`tests/architecture.sh`.

## 4. Wat Mini-ROLLS niet claimt gelijk te zijn

Functioneel is Mini-ROLLS een **subset**. Aanwezig: aanmaken en lijsten van
klant, product en order; automatische identifiers; kiezen van klant/product
op een create-order-formulier.

Nog niet gelijk aan productie-ROLLS (en ook niet beloofd in deze versie):

- persistent wijzigen van een order
- volledig annuleren (status + voorraad)
- zoeken op identifier
- onderhouden van bestaande klant/product
- orderbedrag uit echte productprijs
- batchverwerking, voorraadupdate, dagrapport
- `ORDER_LINE` en `STOCK_MOVEMENT` in de runtime
- native Formgen-gedrag (kleuren, field-level help, block mode, enz.)

Zie [ANALYSE.md](ANALYSE.md) voor het volledige doelbeeld, wat in deze versie
aanwezig is, wat ontbreekt, en het technische ontwerp.

## 5. Twee paden: discovery versus lokale run

**Discovery / Graphify — alleen corpus**

```text
cobol/  copylib/  forms/  jobs/  sql/  requirements/
Application_cob.lst  Cobjobs.lst
```

**Niet aanleveren:** `local-runtime/`, `tests/ground-truth.md`, `bin/`, `data/`.

**Lokale run op Mac**

```bash
make build
make seed
./run.sh
```

`./run.sh` zet de logicals, start de Formgen-emulator, en CALL’t de
`bin/ui-ROLS*` harnesses. Het COBOL-menu (`ROLS0001`) blijft in het corpus
voor CALL-extractie; de operator loopt via `.LAY`-menu’s.

## 6. Korte checklist “lijkt het op ROLLS?”

- [x] COBOL-85, fixed format, `ROLSnnnn`
- [x] Geen `SCREEN SECTION`; schermen in `.LAY`
- [x] Copy members + `.TLB`-manifest
- [x] `ASSIGN TO` logicals, geen Unix-paden in COBOL
- [x] User job `ROLJ` vs automatic `ROLA`
- [x] Oracle-SQL als apart artefact
- [x] Interactief vs batch in gescheiden lijsten
- [x] Geen HP/OpenVMS/Formgen/Oracle nodig voor `./run.sh`
