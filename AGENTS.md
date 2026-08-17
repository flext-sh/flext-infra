# AGENTS.md — flext-infra

> **Parent workspace law** lives in [`../AGENTS.md`](../AGENTS.md) — read it first.
> Universal engineering core: `~/.agents/UNIVERSAL_CORE.md`. Composition: global skills + parent/root `AGENTS.md` + this scope delta. Do not re-embed universal law.
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
- Config/settings canonical pattern: ADR-012.
- Codemod governance (ast-grep + make mod): ADR-014.

## Commands

```bash
make check PROJECT=flext-infra
make test  PROJECT=flext-infra
make build WHAT=artifacts
make work WHAT=status PROJECT=flext-infra BEAD=<id>
make work WHAT=start PROJECT=flext-infra BEAD=<id> KIND=feature NAME=<slug> APPLY=Y
make work WHAT=start PROJECT=flext-infra BEAD=<epic-id> NAME=<epic-slug> APPLY=Y
make work WHAT=start PROJECT=flext-infra BEAD=<child-id> EPIC=<epic-id> NAME=<child-slug> APPLY=Y
make work WHAT=land PROJECT=flext-infra BEAD=<id> APPLY=Y
make work WHAT=finish PROJECT=flext-infra BEAD=<id> APPLY=Y
```

`KIND` is optional and accepts only `feature|bugfix|hotfix|release`; omission
derives the namespace from the Bead issue type. Epic Beads own `epic/<slug>`.
Child starts omit `BASE`; the registered epic branch is their lifecycle target.
<!-- AIHUB-AGENTS-SCOPE-LOCAL-END -->
