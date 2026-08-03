# AGENTS.md — flext-infra

> **Parent workspace law** lives in [`../AGENTS.md`](../AGENTS.md) — read it first. Universal engineering core: `~/.agents/UNIVERSAL_CORE.md`. Composition: global skills + parent/root `AGENTS.md` + this scope delta. Do not re-embed universal law.
>
> **Standalone / independent mode:** when `../AGENTS.md` does not resolve, pin the parent raw `AGENTS.md` URL to the same branch/release as this package (never `main`).

<!-- AIHUB-AGENTS-SCOPE-LOCAL-BEGIN -->
**Package:** `flext_infra` · ~82k src LOC · deps: `flext-cli`, `flext-core`

## Overview

Build/tooling package for codegen, workspace conformance, dependency modernization, and declarative enforcement. Drives canonical Make verbs; generates package facets and `[MANAGED]` pyproject sections. Not a runtime dependency — reach via CLI or pytest plugin (only `flext-tests` may depend on it).

## Structure

```text
src/flext_infra/
├── api.py cli.py __main__.py iteration.py
├── codegen/ detectors/ fixers/ transformers/ rules/ schemas/ templates/
├── config/ deps/ gates/ check/ validate/ docs/ github/ maintenance/
├── release/ workspace/ services/ _enforcement/ basemk/
├── constants.py typings.py protocols.py models.py utilities.py
└── _constants/ _typings/ _protocols/ _models/ _utilities/
```

## Code Map

| Symbol | Kind | Location | Role |
| --- | --- | --- | --- |
| `FlextInfra` | class | `api.py` | Rope workspace / health facade |
| `FlextInfraCli` | class | `cli.py` | CLI entry |
| `FlextInfraEnforcementEngine` | class | `_enforcement/engine.py` | catalog-backed enforcement |
| `FlextInfraCodegenPipeline` | class | `codegen/pipeline.py` | codegen pipeline |
| `FlextInfraPyprojectModernizer` | class | `deps/modernizer.py` | managed pyproject enforcement |

## Conventions (specific to this package)

- Rules-as-data: policy in `rules/*.yaml` + `config/*.yaml` (Pydantic); add a YAML row, not a detector class.
- Codegen owns facets / `py.typed` / `[MANAGED]` sections — change SSOT/templates, run the generator; never hand-edit output.
- Enforcement target is rope-semantic (ADR-005); some detectors still use AST — verify before claiming AST is banned.

## Commands

```bash
make check PROJECT=flext-infra
make test  PROJECT=flext-infra
make build WHAT=gen
```
<!-- AIHUB-AGENTS-SCOPE-LOCAL-END -->
