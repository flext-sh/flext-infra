# SonarCloud triage — flext-sh/flext-infra

<!-- TOC START -->

- [Pull request #2095 — reliability gate (2026-10-24)](#pull-request-2095-reliability-gate-2026-10-24)

<!-- TOC END -->

This is an evidence report, not a task tracker. The canonical tracker is bead
`flext-y9dqj` (P0 security lane under epic `flext-1engx`).

## Pull request #2095 — reliability gate (2026-10-24)

The reliability rating on new code was E, from five findings returned by
`api/issues/search?componentKeys=flext-sh_flext-infra&pullRequest=2095&impactSoftwareQualities=RELIABILITY`.

| Rule | Location | Disposition | Evidence |
| --- | --- | --- | --- |
| `pythonbugs:S2583` | `src/flext_infra/gates/base_gate.py` (`self._runner or u.Cli`) | Fixed in `ef86e7952c` | The runner is now a required port whose typed default is `u.Cli`, so the always-true fallback branch is gone. |
| `python:S8510` (×2) | `src/flext_infra/codemod/semantic_apply.py:353` | Fixed in `ef86e7952c` | The for-else family-suffix loop now uses its own `position`/`part` names instead of shadowing `index`/`word`. |
| `python:S930` | `src/flext_infra/_utilities/rope_class_move.py:137` | False positive, operator-authorized | `directory` iterates over `target.parents`, where `target` is a `Path`. `Path.with_suffix(".py")` is a valid one-argument call. |
| `python:S8495` | `src/flext_infra/_utilities/lazy_init_render.py:219` | False positive, operator-authorized | `_lazy_init_import` returns a variable-length sequence of output lines, typed `t.StrSequence`, not a fixed-length record. |

Authorization: operator answer of 2026-10-24, recorded in tracker memory
`operator-ruling-2026-10-24-security-cooldown-and-fp`.

Marking the two false positives in SonarCloud needs `SONAR_TOKEN` through the ai-hub
credential projection (ai-hub ADR-0040). That token is not present in the projected
environment yet; the gap is tracked on `flext-y9dqj`.
