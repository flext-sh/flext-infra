#!/usr/bin/env bash
# /// flext-command
# verb = "check"
# what = "docs"
# summary = "Valida documentação gerada e site MkDocs"
# description = "Executa o pipeline flext-infra completo e falha quando projeções versionadas ficam stale."
# domain = "validation"
# mutates = false
# aliases = []
# example = "make check WHAT=docs"
# rules = ["flext-docs", "docs validate", "mkdocs build", "generated freshness"]
# params = []
# ///
set -euo pipefail

_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly _root
cd "${_root}"

make docs WHAT=all

readonly generated_paths=(
  README.md
  docs/api-reference
  docs/index.md
  docs/guides/README.md
  mkdocs.yml
)

if ! git diff --exit-code -- "${generated_paths[@]}"; then
  printf '%s\n' \
    "ERROR: documentação gerada está stale; rode 'make docs WHAT=fix' e versione a saída." \
    >&2
  exit 1
fi

printf '%s\n' "docs: geração idempotente, validação e build válidos"
