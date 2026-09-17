# Map OpenVMS-style COBOL ASSIGN logicals to local sequential files.
# Production ROLLS (SIROL / HP COBOL II) resolves ASSIGN TO ORDERS via DCL
# logicals. Local GnuCOBOL -std=cobol85 uses ASSIGN EXTERNAL = environment
# variables. No HP COBOL, OpenVMS, Formgen or Oracle license is required.
#
# Source after setting ROLLS_ROOT to the project root.

: "${ROLLS_ROOT:=$(pwd)}"
export ORDERS="$ROLLS_ROOT/data/orders.dat"
export CUSTOMERS="$ROLLS_ROOT/data/customers.dat"
export PRODUCTS="$ROLLS_ROOT/data/products.dat"
export HISTORY="$ROLLS_ROOT/data/order_history.dat"
