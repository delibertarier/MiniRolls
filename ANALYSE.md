# Mini-ROLLS — functionele en technische analyse

Analyse van de gewenste werking en de technische uitgangspunten, opgesteld
voor realisatie van de lokale Mini-ROLLS-applicatie. Dit document verdeelt
het doelbeeld in functies die in deze versie aanwezig moeten zijn, en
functies die bewust nog niet worden opgeleverd.

Domein: order-, klant- en productbeheer met batchverwerking. Dialect: ANSI
COBOL-85. Lokale uitvoering: macOS (Apple Silicon) met GnuCOBOL.

Architectuur ten opzichte van productie-ROLLS: [ROLLS-ALIGNMENT.md](ROLLS-ALIGNMENT.md).

Samenvatting van deze versie: **7 functies aanwezig**, **11 nog niet
aanwezig**, **13 functionele eisen**, **8 technische eisen**.

---

## 1. Nog niet aanwezig

Onderstaande operatorfuncties horen bij het Mini-ROLLS-doelbeeld maar worden
in deze oplevering niet gebouwd. Menu-items of programma’s mogen bestaan als
plaatsaanduiding; de businesslogica en persistentie ontbreken.

Deze versie levert een bedienbare keten voor vastleggen en raadplegen: klant,
product en order aanmaken, plus lijsten. Mutatie ná vastlegging, zoeken,
voorraad en batch vallen buiten de oplevering.

Plaatsaanduidingen (zoekschermen, modify/cancel, batchjobs) blijven in het
programmamodel zichtbaar voor latere incrementen, zonder dat de operator daar
nu een afgeronde functie van mag verwachten.

Van 18 operatorfuncties uit het doelbeeld (bron: `requirements/` en
`forms/`) zitten er 7 in deze versie en 11 nog niet.

### Ontbrekende functionaliteit

| Functie | Eis | Wat ontbreekt | Zichtbaar voor de operator? |
| --- | --- | --- | --- |
| Order wijzigen | REQ-ORD-003 | Aantal van een open order persistent bijwerken | Scherm bestaat; wijziging wordt niet opgeslagen |
| Order annuleren (volledig) | REQ-ORD-004 | Orderstatus CANCELLED, history mét tijdstempel, voorraad vrijgeven | Scherm bestaat; order blijft OPEN |
| Klant zoeken | REQ-CUS-001 | Opvragen van klantgegevens op identifier | Scherm bestaat; geen weergave van de klant |
| Product zoeken | REQ-PRD-001 | Opvragen van productgegevens op identifier | Scherm bestaat; geen weergave van het product |
| Klant onderhouden | REQ-CUS-002 | Naam en status van een bestaande klant wijzigen | Alleen nieuw aanmaken is mogelijk |
| Product onderhouden | REQ-PRD-002 | Naam, prijs en voorraad van een bestaand product wijzigen | Alleen nieuw aanmaken is mogelijk |
| Orderbedrag uit productprijs | REQ-ORD-001 | Bedrag = prijs × aantal, per gekozen product | Create rekent met een vast tarief 10,00 |
| Batch orderverwerking | REQ-ORD-005 / REQ-BAT-003 | Open orders verwerken en status bijwerken | Job start een programma zonder gegevensverwerking |
| Batch voorraadaanpassing | REQ-PRD-003 / REQ-BAT-001 | Voorraad aftrekken of vrijgeven op basis van orders | Job start een programma zonder file I/O |
| Dagelijks rapport | REQ-BAT-002 | Aggregatie van orders (aantal en bedrag per status) | Job toont alleen een tekstregel, geen rapport |
| Voorraadmutaties vastleggen | REQ-ORD-004 / schema STOCK_MOVEMENT | Aparte mutatieregistratie per product | Niet in de runtime; alleen in het logische SQL-model |

### Evenmin in deze versie

| Onderwerp | Toelichting |
| --- | --- |
| Meerdere orderregels | Een order heeft in deze versie één product. `ORDER_LINE` bestaat alleen in het logische SQL-model. |
| Server-side controle actieve klant / bestaand product | De TUI filtert actieve klanten bij kiezen. COBOL valideert dat niet opnieuw. |
| Uniciteit van namen | Dubbele klant- of productnamen worden toegestaan. |
| Native COBOL-schermen | Geen `SCREEN SECTION`. Schermen liggen in `.LAY`; invoer via de Formgen-emulator. |

---

## 2. Doelbeeld

Mini-ROLLS ondersteunt een operator bij het beheren van klanten, producten en
orders. Een order hoort bij een actieve klant en een geldig product, bevat een
aantal, krijgt een status en een berekend bedrag. Open orders kunnen worden
gewijzigd of geannuleerd. Batchjobs verwerken orders, passen voorraad aan en
leveren een dagrapport.

### Functionele eisen — volledig doelbeeld

| Eis | Gewenste uitkomst | In deze versie? |
| --- | --- | --- |
| REQ-ORD-001 Create Order | Order vastleggen voor actieve klant en geldig product, met aantal, status en berekend bedrag | Deels — vastleggen ja; bedrag niet uit productprijs |
| REQ-ORD-002 Validate Order | Gedeelde controle: order-id en aantal groter dan nul | Ja |
| REQ-ORD-003 Modify Order | Aantal van een open order wijzigen na validatie | Nee |
| REQ-ORD-004 Cancel Order | Open order annuleren, history bewaren, voorraad vrijgeven | Nee |
| REQ-ORD-005 Process Orders | Batch verwerkt open orders via gemeenschappelijke lookup | Nee |
| REQ-CUS-001 Search Customer | Klant opvragen op identifier | Nee |
| REQ-CUS-002 Maintain Customer | Klant aanmaken of onderhouden (naam, status) | Deels — alleen aanmaken |
| REQ-PRD-001 Search Product | Product opvragen op identifier | Nee |
| REQ-PRD-002 Maintain Product | Naam, prijs en voorraad onderhouden | Deels — alleen aanmaken |
| REQ-PRD-003 Stock Update | Batch werkt voorraad bij op verwerkte orders | Nee |
| REQ-BAT-001 Stock Update job | Voorraadjob voert het COBOL-programma uit op ordergegevens | Nee |
| REQ-BAT-002 Daily Report | Dagrapport vat orderverwerking samen | Nee |
| REQ-BAT-003 Manual Order Processing | Operator kan orderverwerking handmatig starten | Nee — start wel, verwerkt niet |

### Beoogde gebruikersketen

| Stap | Actor | Resultaat |
| --- | --- | --- |
| 1. Stamgegevens | Operator | Klant en product bestaan en zijn raadpleegbaar |
| 2. Order vastleggen | Operator | OPEN-order met juist bedrag |
| 3. Order bijstellen | Operator | Aantal of annulering persistent |
| 4. Verwerken | Batch / operator | Orders verwerkt, voorraad bijgewerkt |
| 5. Rapporteren | Batch | Dagoverzicht per status |

Deze versie dekt stap 1 (alleen aanmaken + lijst, geen zoeken of wijzigen)
en stap 2 (vastleggen, met vereenvoudigd bedrag). Stap 3 tot 5 zijn nog niet
aanwezig.

---

## 3. In deze versie

De operator kan stamgegevens en orders vastleggen en lijsten raadplegen, in
boxed formulieren. Identifiers worden toegekend bij opslaan. Bij een nieuwe
order kiest de operator klant en product uit een lijst.

Aanmaken is append-only. Bestaande klanten, producten en orders zijn in deze
versie niet te wijzigen. Het orderbedrag volgt niet de productprijs.

### Aanwezige functionaliteit

| Functie | Programma | Gedrag |
| --- | --- | --- |
| Hoofd- en deelschermen | ROLS0001 / 6001 / 6010 / 6020 + `.LAY` | Menu’s voor orders, klanten en producten |
| Klant aanmaken | ROLS6011 | Naam invoeren; identifier automatisch; status ACTIVE |
| Product aanmaken | ROLS6021 | Naam, prijs en voorraad; identifier automatisch |
| Order aanmaken | ROLS6002 | Klant en product kiezen, aantal invoeren; identifier automatisch; status OPEN |
| Orders lijsten | ROLS6005 | Alle orders uit het sequential bestand |
| Klanten lijsten | ROLS6013 | Alle klanten uit het sequential bestand |
| Producten lijsten | ROLS6023 | Alle producten uit het sequential bestand |

### Aanwezige ondersteuning (geen aparte eindfunctie)

| Onderdeel | Rol |
| --- | --- |
| ROLS9001 | Gedeelde validatie: identifier en aantal > 0 |
| Automatische identifiers | Hoogste bestaande nummer + 1 bij create |
| Formulierbediening | Cursor in `[ ]`, Tab/Enter, SAVE/CANCEL |
| Klant-/productkeuze | Lijst op naam bij create order |

---

## 4. Technisch ontwerp

Mini-ROLLS volgt de productievorm van ROLLS op het SIROL-cluster (OpenVMS
Integrity, HP COBOL II/XL ANSI 85, Formgen, Oracle), zonder die stack lokaal
te eisen. De lokale uitvoering is GnuCOBOL op Apple Silicon plus een
Formgen-emulator in de Python-standaardbibliotheek. Geen HP COBOL-, VSI
OpenVMS-, Formgen- of Oracle/Pro*COBOL-licentie.

### Productie ROLLS versus lokale stand-in

| Productie (SIROL) | Deze versie op M1 | Licentie |
| --- | --- | --- |
| HP COBOL II/XL, ANSI 85 (ook 74-compatibel) | GnuCOBOL `-fixed -std=cobol85` | Homebrew, geen HP-compiler |
| OpenVMS logicals, `ASSIGN TO ORDERS` | Zelfde implementor-names; env `ORDERS` / `CUSTOMERS` / `PRODUCTS` / `HISTORY` | Geen OpenVMS |
| Formgen-schermen, geen `SCREEN SECTION` | `.LAY`-corpus + `local-runtime/formgen.py` | Geen commercieel Formgen |
| Oracle + embedded SQL | `sql/` alleen als analysemodel; niet gecompileerd | Geen Oracle/Pro*COBOL |
| DCL user job ROLJ / automatic ROLA | Zelfde namen; POSIX sh met DCL-analogie in commentaar | Geen DCL |

Drie lagen:

- **COBOL-corpus** — programma’s `ROLSnnnn`, copy members, jobs, forms, SQL,
  requirements. Geen `SCREEN SECTION`. Geschikt als input voor discovery.
- **Lokale runtime** — Python Formgen-emulator, ui-harnesses, sequential
  `.dat` via logicals, seed ROLS7999. SQLite-schema mag bestaan; COBOL leest
  het niet.
- **Taalcontract** — `cobc -fixed -std=cobol85`, kolom 72, geen
  continuatieregels, interactief `EXIT PROGRAM`, batch `STOP RUN`.

### Technische eisen

| Eis | Keuze |
| --- | --- |
| REQ-TEC-001 Dialect | ANSI COBOL 1985 / GnuCOBOL cobol85 (HP COBOL II-analogie) |
| REQ-TEC-002 Bronformaat | Fixed/reference format, audit op kolom 72 |
| REQ-TEC-003 Families | Interactief 60xx, batch 61–63xx, gemeenschappelijk 90xx |
| REQ-TEC-004 Copy library | CPM-ORDER, CUSTOMER, PRODUCT, PAR9001, COMMON |
| REQ-TEC-005 Database-artifacts | Oracle-fixture in `sql/`; runtime = sequential files |
| REQ-TEC-006 Jobs en forms | ROLJ/ROLA `.JOB` en `.LAY` zonder `SCREEN SECTION` |
| REQ-TEC-007 Licentiegrens | Geen HP COBOL, OpenVMS, Formgen of Oracle op M1 |
| REQ-TEC-008 ASSIGN | Logicals `ORDERS`, `CUSTOMERS`, `PRODUCTS`, `HISTORY` — geen POSIX-paden in COBOL |

### Programma-indeling

| Familie | Verantwoordelijkheid | Deze versie |
| --- | --- | --- |
| ROLS0001 / 60x0 | Menu’s | Aanwezig als navigatie |
| ROLS6002 / 6011 / 6021 | Create | Aanwezig, inclusief automatische ID |
| ROLS6005 / 6013 / 6023 | Lijsten | Aanwezig |
| ROLS6003 / 6004 | Wijzigen / annuleren | Nog niet aanwezig als volledige functie |
| ROLS6012 / 6022 | Zoeken | Nog niet aanwezig |
| ROLS6100 / 6200 / 6300 | Batch | Nog niet aanwezig |
| ROLS9001 | Validatie | Aanwezig |
| ROLS9002 | Bedragberekening | Aanwezig in vereenvoudigde vorm (vast tarief) |
| ROLS9003 | Gemeenschappelijke lookup/DB | Nog niet aanwezig |

### Datamodel

Het logische model bevat CUSTOMER, PRODUCT, ORDERS, ORDER_LINE,
ORDER_HISTORY en STOCK_MOVEMENT. De runtime van deze versie gebruikt
denormaliseerde sequential records en één product per order.

| Logische entiteit | Runtime deze versie |
| --- | --- |
| CUSTOMER | `customers.dat` — 46 bytes per record |
| PRODUCT | `products.dat` — 52 bytes per record |
| ORDERS + ORDER_LINE | `orders.dat` — één record, één product |
| ORDER_HISTORY | Gereserveerd; volledige cancel-keten nog niet aanwezig |
| STOCK_MOVEMENT | Niet aanwezig in de runtime |

### Contract scherm → COBOL (aanwezige creates)

| Functie | Invoer naar ACCEPT | Daarna |
| --- | --- | --- |
| Order aanmaken | klant-id, product-id, aantal | volgende order-id, validatie, bedrag, WRITE |
| Klant aanmaken | naam | volgende klant-id, status ACTIVE, WRITE |
| Product aanmaken | naam, prijs, voorraad | volgende product-id, WRITE |

### Nog te ontwerpen in een volgend increment

| Onderwerp | Technische opgave |
| --- | --- |
| Modify | Sequential rewrite of geïndexeerd bestand; alleen OPEN orders |
| Cancel | Statusupdate + history + voorraadvrijgave |
| Zoeken | Read op identifier i.p.v. gemeenschappelijke stub |
| Prijs | ROLS9002 leest PRODUCT.PRICE en vermenigvuldigt met aantal |
| Batch | ROLS6100/6200 met file I/O; ROLS6300 met aggregatie |
| Lookup-service | ROLS9003 als echte gemeenschappelijke I/O-routine |
