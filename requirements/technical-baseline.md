# Technical Baseline Requirements

## REQ-TEC-001 COBOL dialect
The representative source corpus shall target ANSI COBOL 1985 style and avoid
modern language constructs unless required for local GnuCOBOL execution.

## REQ-TEC-002 Fixed source format
COBOL programs and copy members shall use classic fixed/reference source format.

## REQ-TEC-003 Program families
Interactive and batch programs shall retain ROLSnnnn naming and separate
application/batch compilation lists.

## REQ-TEC-004 Copy library
Database structures, linkage areas and common structures shall be represented
as separately managed copy members.

## REQ-TEC-005 Database artifacts
The corpus shall contain separate SQL artifacts and an Oracle-oriented schema
for static analysis while retaining a locally executable macOS test profile.

## REQ-TEC-006 Jobs and forms
The corpus shall contain legacy-looking JOB and layout artifacts so that
cross-artifact dependency extraction can be evaluated.

## REQ-TEC-007 License and platform boundary
The compiled local profile shall remain runnable on Apple Silicon with
GnuCOBOL and the Python standard library. It shall not require HP COBOL,
OpenVMS, commercial Formgen, or Oracle/Pro*COBOL. Production-like ASSIGN
logicals (ORDERS, CUSTOMERS, PRODUCTS, HISTORY) are resolved locally via
environment mapping. Embedded SQL and Oracle schema remain analysis
artifacts under sql/, never part of the local link step.

## REQ-TEC-008 File assignment
COBOL FILE-CONTROL shall ASSIGN TO implementor-names (OpenVMS logical
analogs), not POSIX paths. The local runtime supplies the mapping.
