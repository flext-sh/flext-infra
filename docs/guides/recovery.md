# Recovery runbook

<!-- TOC START -->

- [Broken bootstrap (the checkout's Makefile misbehaves)](#broken-bootstrap-the-checkouts-makefile-misbehaves)
- [Install-mode mismatch](#install-mode-mismatch)
- [The recovery loop](#the-recovery-loop)
- [Orphan imports](#orphan-imports)
- [Racing-lane merges](#racing-lane-merges)
- [Render provenance](#render-provenance)

<!-- TOC END -->

How to diagnose and heal a checkout whose own tooling is the broken part.
Every cure here is owned state re-applied by a verb — never a hand patch
that the next generation cannot reproduce (aihub-l42it.11 consolidation
postmortem, 2026-10-13).

## Broken bootstrap (the checkout's Makefile misbehaves)

Symptom: `make setup` fails inside the emitted recipe (unbound shell
variables, references to template features the pinned motor never emits).

1. Diagnose with a healthy motor from outside the broken checkout — the
   family workspace's flext-infra checkout runs every check verb against any
   repository root:

   ```sh
   ~/flext/.venv/bin/python -m flext_infra check run \
       --repository-root /path/to/broken-checkout --gates fresh-import
   ```

2. Heal by re-rendering with the pinned motor: run `make gen` in a checkout
   whose setup works, commit the regenerated artifacts, and let the broken
   checkout adopt them. Hand-editing an emitted recipe is a bootstrap-only
   exception: mark it as superseded by the next owner render in the commit.

3. The Makefile render recipe initializes every shell variable it reads; the
   soundness contract in
   `tests/unit/codegen/makefile_bootstrap_soundness_tests.py` fails any
   template evolution that reintroduces a read-before-assignment.

## Install-mode mismatch

`verify-environment` rejects a checkout synced in the other mode (CI's
frozen non-editable build vs the local editable binding). Outside CI the
`_builtin_require_environment` gate heals itself: it re-runs the declared
`uv sync` and re-verifies once. In CI the mismatch stays a loud failure —
CI environments never heal; provision with `make setup`.

## The recovery loop

- Run the `make gen` / `make mod` / `make gen` / `make gen` fixed-point loop
  on the local (editable) path: the CI identity gate demands a pristine tree
  and must not gate recovery passes.
- Reserve `CI=Y` for the final fixed-point proof after committing, when the
  tree is clean and the install is frozen non-editable.
- Commit each applied migration state the loop produces; the identity gate
  admits the next pass only from a clean tree.

## Orphan imports

The `deps` gate (deptry) fails any import the declared dependencies do not
cover, at check time. Cure the declaration (the project's dependency SSOT or
the org override surface), never the consumer's import.

## Racing-lane merges

Before an administrative merge of diverged lanes: realign the branch
(`git merge` the integration base), then run at least
`fresh-import`, `lint`, and `conflict-markers` on the realigned branch —
through a healthy motor when the branch's own bootstrap is broken. Textual
mergeability is not semantic integrity.

## Render provenance

Generated artifacts carry `# @flext-rendered-by: flext-infra <version>`.
A drift between this stamp and the consumed motor is a regeneration order:
`make gen` re-renders with the pinned generator. `codegen conform
--mode check` (part of `make verify-clean`) detects the drift; the stamp
makes the report name both sides.
