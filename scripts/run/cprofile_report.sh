#!/bin/sh
set -eu

: "${RUNTIME_PYTHON:?RUNTIME_PYTHON is required}"
exec "$RUNTIME_PYTHON" -m flext_infra._cprofile_entry
