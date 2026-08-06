# Triagem Snyk Code (SAST) — flext-sh/flext-infra

Gerado do scan Snyk da org Datacosmos (dump 2026-08-06).

**2 achados** — critical 0, high 0, medium 1, low 1

| categoria | achados |
|---|---|
| Arbitrary File Write via Archive Extraction (Tar Slip) | 1 |
| Jinja auto-escape is set to false. | 1 |

## Achados

Coluna **Decisão**: `corrigir` / `falso-positivo` / `risco-aceito`.

| # | sev | categoria | arquivo | linha | CWE | Decisão |
|---|---|---|---|---|---|---|
| 1 | medium | Arbitrary File Write via Archive Extraction (Tar Slip) | `src/flext_infra/release/_release_artifact_source.py` | 212 | - | |
| 2 | low | Jinja auto-escape is set to false. | `tests/unit/codegen/test_codegen_catalog_extensions.py` | 209 | - | |

## Como triar

1. Abrir `arquivo:linha` e seguir o fluxo de dados até o sink.
2. Classificar: **corrigir** (entrada externa alcança o sink sem sanitização), **falso-positivo** (credencial de fixture, path de constante — registrar em `.snyk` com justificativa), **risco-aceito** (com prazo de revisão).

Dados brutos: `~/snyk-violations/sast/flext-sh__flext-infra.sast.json`

