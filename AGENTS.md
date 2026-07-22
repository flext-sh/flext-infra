# AGENTS.md — flext-infra

<!-- BEGIN AI-HUB MANAGED UNIVERSAL CORE -->
<!-- UNIVERSAL-GOVERNANCE v4 -->

## Universal Agent Engineering Core

`~/.agents` is the sole universal authority. AI Hub distributes and configures
it but never competes with it. Project law may be stricter; the newest explicit
operator instruction prevails and lower authority must be reconciled.

1. **Truth with evidence.** Claims require the exact command, working directory,
   exit status, decisive output, and bounded scope.
2. **Research before mutation.** Read current authority, intent, owner Bead,
   implementation owner, consumers, generated projections, concurrent WIP, and
   validation route. Never invent behavior or results.
3. **One active intent.** Preserve the goal, target, Bead, exclusions, phase,
   required gates, and stop condition through delegation and continuation.
4. **Root cause and one owner.** Change the canonical owner and complete the
   cutover. No bypass, fallback, shim, suppression, hardcode, fake, duplicate
   route, silent default, or old-and-new coexistence.
5. **Fix forward.** Preserve shared work; never destructively discard unknown
   changes. Re-read mutable files and classify relevant paths and hunks.
6. **Typed and generated boundaries.** Parse untrusted input once into canonical
   types. Change sources, not projections; regenerate and prove idempotence.
7. **Continuous green.** No completion while the project or environment is
   broken, partially migrated, dirty from task WIP, ahead of remote, missing
   real-use QA, or carrying stale generated output or docs. Run native global
   and changed-scope gates; Python requires Ruff, Pyrefly, Pyright, Mypy, and
   Pytest coverage plus applicable build and integrated validation.
8. **Beads is execution truth.** Beads owns work, plans, memory, dependencies,
   status, evidence, and closure. GitHub is its continuous external coordination,
   PR, review, and CI mirror after the orchestrator organizes Beads completely.
9. **Separated roles.** The orchestrator coordinates, owns semantic Beads state,
   validates, approves or rejects merges, rolls out, and closes; it does not
   implement. Workers directly implement one Bead in one branch and worktree but
   never merge or close. The standing documenter continuously audits, updates,
   validates, and removes stale canonical skills, ADRs, docs, Python docstrings,
   examples, and executable snippets under the same validated PR flow; the
   governance/CI helper also remains active.
10. **No stall by reporting.** Five-minute status reports include the agent table
    and epic evolution and never pause execution. Compaction, continuation, and
    status transfer context only.
11. **Historical material is evidence only.** Archives, generated or tool homes,
    backups, sessions, caches, and legacy trees are never live authority.
12. **Stop only for a real blocker.** Ask one precise question only when authority
   conflicts or an action would be destructive; otherwise continue to the
   observable stop condition.
13. **Short validated slices.** Deliver in small, independently validated
   units that merge to the integration branch quickly — one Bead, one
   reviewable PR, hours not days. Mega-lanes and long-lived WIP are defects;
   the orchestrator splits any unit that cannot merge green within a session.
14. **Living documentation.** Project knowledge is durable, never rebuilt
   per session. On entering a project, read its docs first and validate key
   claims quickly against live reality. Every change that produces new
   understanding or behavior updates the affected docs in the SAME change;
   stale docs are defects filed as beads, never worked around.
15. **Tests reflect canonical reality.** Tests are executable checks of current
    behavior, never a source of truth; a test that violates canonical policy is
    corrected to match the policy, not accommodated. Performance optimization is
    evidence-first: profile with cProfile to find the hot path before changing
    anything, then optimize with the project's typed OO/MRO/lazy-import patterns;
    accelerate test selection with impact analysis (e.g. pytest-testmon) and
    parallelism (pytest-xdist) rather than deleting or weakening coverage.
16. **Parametrized config, generators, and managed binaries.** config, settings,
    and templates are the sole source of configuration and business rules; the
    correct generator produces every derived surface (never hand-edit a
    projection). ai-hub owns the installation of binaries and the provisioning of
    environments; no manual, machine-specific path or binary hardcode. There is
    no product-, agent-, or daemon-specific hardcoded code anywhere — every such
    value is parametrized through config/settings/templates.

<!-- /UNIVERSAL-GOVERNANCE -->
<!-- END AI-HUB MANAGED UNIVERSAL CORE -->

> **General FLEXT law & workspace conventions live in the root [`../AGENTS.md`](../AGENTS.md) — read it first.** It is the SSOT for facade layering, config/settings access, the `make`-only workflow, the testing law, and multi-agent git discipline. This file adds ONLY `flext-infra`-specific knowledge and never repeats the root.
>
> **Standalone / independent mode:** if this package is checked out on its own (imported as a dependency, vendored, or cloned solo) there is no parent workspace, so `../AGENTS.md` does not resolve. Then read the root law from the raw file on the SAME branch/release the project is on: <https://raw.githubusercontent.com/flext-sh/flext/0.12.0-dev/AGENTS.md> (pin the branch/tag to your working line, never `main`).

**Package:** `flext_infra` · ~82k src LOC (largest in the workspace) · deps: `flext-cli`, `flext-core`

## Overview

Infrastructure tooling: code generation, workspace conform, dependency modernization, and declarative enforcement. It *drives* `make gen` / `make build` / `make check` and generates other packages' facets and `[MANAGED]` pyproject sections.

## Structure

```
src/flext_infra/
├── api.py cli.py __main__.py   # FlextInfra facade + FlextInfraCli (main / docs_main)
├── iteration.py                # MRO facade over _iteration_{matching,directory,workspace,project}.py
├── codegen/        # scaffolding, conform, census, lazy-init/facet generation, pipeline, consolidator, py.typed
├── detectors/      # policy detectors: dep/runtime, MRO shape, class placement, loose-test, silent-failure
├── fixers/         # base/rope/transformer/manual/gate fixers + orchestration
├── transformers/   # source modernizers: signature, class-nesting, compat, Result/DI
├── rules/          # YAML policy catalogs (class nesting, typing census, import modernization, constants, legacy)
├── schemas/        # JSON schemas for codegen + workspace manifests
├── templates/      # Jinja: package roots, lazy-init roots, Makefile/build artifacts
├── config/         # declarative codegen/enforcement policy (codegen.yaml, …) validated by pydantic
├── deps/           # dependency detection, extra-paths, pyrefly repair, modernizer.py ([MANAGED] pyproject)
├── gates/ check/ validate/     # gate resolution, workspace check orchestration, validators (cycles, tiers, …)
├── docs/ github/ maintenance/ release/ workspace/ services/ _enforcement/ basemk/
├── constants.py typings.py protocols.py models.py utilities.py   # AUTO-GENERATED facets
└── _constants/ _typings/ _protocols/ _models/ _utilities/
```

## Code Map

| Symbol | Kind | Location | Role |
|--------|------|----------|------|
| `FlextInfra` | class | `api.py` | public facade (Rope workspace access, health) |
| `FlextInfraCli` / `main` / `docs_main` | class+fns | `cli.py` | entry points `flext-infra`, `flext-docs` |
| `FlextInfraEnforcementEngine` | class | `_enforcement/engine.py` | catalog-backed enforcement collector |
| `FlextInfraCodegenPipeline` | class | `codegen/pipeline.py` | codegen pipeline (used by `services/cli_routes_codegen.py`) |
| `FlextInfraCodegenConsolidator` | class | `codegen/consolidator.py` | facet consolidation |
| `FlextInfraPyprojectModernizer` | class | `deps/modernizer.py` | `[MANAGED]` pyproject enforcement |
| `FlextInfraUtilitiesIteration` | class | `iteration.py` | MRO iteration helpers |

## Conventions (specific to this package)

- **Rules-as-data:** policy lives in `rules/*.yaml` + `config/*.yaml`, validated with pydantic `model_validate` — not hardcoded in Python. Add a rule = new YAML row, not a new detector class.
- **Codegen owns generated output:** package `__init__`/facet roots, `py.typed`, and `[MANAGED]` pyproject sections are generated. Change the codegen source/template + `make build WHAT=gen` (or `WHAT=mod`); never hand-edit the output.
- Enforcement/detection target a **rope-semantic** path (ADR-005 direction).

## Anti-Patterns / Gotchas

- **Build/tooling package — NOT a runtime dependency.** Reached only via its CLI (`flext-infra`, `flext-docs`) + its pytest11 enforcement plugin. Only `flext-tests` legitimately depends on it; no other package may `import flext_infra` at runtime.
- **Rope-only is the target, not yet absolute:** some detectors/fixers/`_utilities` still use AST (`import ast` / `NodeVisitor`). When migrating the detect path, move it to the rope semantic model — but do not claim "AST is banned everywhere"; verify per file.
- Do not hand-edit generated packages elsewhere in the workspace — fix them here.

## Commands

```bash
make check PROJECT=flext-infra       # ruff/pyrefly/mypy/pyright
make test  PROJECT=flext-infra       # tests/{unit,integration,refactor}
make build WHAT=gen                  # regenerate facets workspace-wide (this package is the engine)
```

<!-- AIHUB-WORKSPACE-PROVIDERS-BEGIN -->
## Workspace providers

These routes are generated from provider-owned manifests.

- flext: read `.agents/skills/flext-context-routing/SKILL.md` first.
<!-- AIHUB-WORKSPACE-PROVIDERS-END -->
