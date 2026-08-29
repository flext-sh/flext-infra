#!/bin/sh
set -eu

: "${PROJECT_ROOT:?PROJECT_ROOT is required}"
: "${RUNTIME_PYTHON:?RUNTIME_PYTHON is required}"
: "${FILE:?FILE is required for run WHAT=cprofile-test}"

case "$FILE" in
  /*|..|../*|*/../*|*/..)
    printf 'ERROR: FILE must be a repository-relative path\n' >&2
    exit 2
    ;;
  *) ;;
esac
test_path=${FILE%%::*}
if [ ! -f "$PROJECT_ROOT/$test_path" ]; then
  printf 'ERROR: cProfile test target does not exist: %s\n' "$test_path" >&2
  exit 2
fi
report_dir="$PROJECT_ROOT/.reports/cprofile"
mkdir -p "$report_dir"
set -- "$FILE" --no-cov -p no:metadata -n=0
if [ -n "${MATCH:-}" ]; then
  set -- "$@" -k "$MATCH"
fi
cd "$PROJECT_ROOT"
exec "$RUNTIME_PYTHON" -m cProfile -o "$report_dir/pytest.pstats" -m pytest "$@"
