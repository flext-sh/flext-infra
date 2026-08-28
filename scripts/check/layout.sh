#!/bin/sh
set -eu

: "${PROJECT_ROOT:?PROJECT_ROOT is required}"
: "${RUNTIME_PYTHON:?RUNTIME_PYTHON is required}"
exec "$RUNTIME_PYTHON" -m flext_infra check run \
  --workspace "$PROJECT_ROOT" --gates layout --projects .
