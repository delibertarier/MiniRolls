#!/bin/sh
set -e
cd "$(dirname "$0")"
ROLLS_ROOT="$(pwd)"
# shellcheck source=local-runtime/logicals.sh
. ./local-runtime/logicals.sh
exec python3 local-runtime/formgen.py
