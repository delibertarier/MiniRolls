#!/bin/sh
set -e
cd "$(dirname "$0")"
exec python3 local-runtime/formgen.py
