# Triagem Semgrep — flext-sh/flext-infra

Gerado do dump da plataforma Semgrep (deployment `datacosmos`, 2026-08-06).

Bead de rastreio: `mro-p57t.12`

## Resumo

**10 findings** — high 2, medium 8, low 0
Confiança: high 3, medium 1, low 6

| regra | achados |
|---|---|
| `python.lang.security.audit.non-literal-import.non-literal-import` | 5 |
| `package_managers.dependabot.dependabot-missing-cooldown.dependabot-missing-cooldown` | 3 |
| `python.lang.compatibility.python37.python37-compatibility-importlib2` | 1 |
| `trailofbits.python.tarfile-extractall-traversal.tarfile-extractall-traversal` | 1 |

## Findings

Coluna **Decisão** a preencher: `corrigir` / `falso-positivo` / `risco-aceito`.

| # | sev | conf | regra | arquivo | linha | Decisão |
|---|---|---|---|---|---|---|
| 1 | high | low | `python37-compatibility-importlib2` | `src/flext_infra/codemod/discovery.py` | 5 | |
| 2 | high | medium | `tarfile-extractall-traversal` | `src/flext_infra/release/_release_artifact_source.py` | 211 | |
| 3 | medium | high | `dependabot-missing-cooldown` | `.github/dependabot.yml` | 4 | |
| 4 | medium | high | `dependabot-missing-cooldown` | `.github/dependabot.yml` | 11 | |
| 5 | medium | high | `dependabot-missing-cooldown` | `.github/dependabot.yml` | 18 | |
| 6 | medium | low | `non-literal-import` | `src/flext_infra/_utilities/rope_helpers.py` | 40 | |
| 7 | medium | low | `non-literal-import` | `src/flext_infra/_utilities/rope_runtime_base.py` | 17 | |
| 8 | medium | low | `non-literal-import` | `src/flext_infra/services/cli_routes.py` | 93 | |
| 9 | medium | low | `non-literal-import` | `src/flext_infra/validate/runtime_census.py` | 69 | |
| 10 | medium | low | `non-literal-import` | `src/flext_infra/validate/runtime_census.py` | 86 | |

## Como triar

1. Abrir `arquivo:linha` e seguir o fluxo até o sink.
2. Classificar: **corrigir** (entrada externa alcança o sink), **falso-positivo** (registrar via `nosemgrep` ou `.semgrepignore` com justificativa), **risco-aceito** (com prazo de revisão).
3. Priorizar findings high com confidence=high.

Dados brutos: `~/semgrep-violations/by-repo/flext-sh__flext-infra.json`

