# Workspace Check Report

Generated: 2026-11-22 04:35:02 UTC
Check phase: primary
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| aihub-vkb1j.14 | FAIL | 1 |

## Details

### aihub-vkb1j.14
Root: `/home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14`
- lint: PASS (0 issues)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14/.reports/gates/20261122T043448.070689Z-4157781/check/34e3859e-6b19-4c8c-9d7c-0646cf9f7777/aihub-vkb1j.14/lint.raw.log)
- pyrefly: FAIL (1 issues)
  - src/flext_infra/_utilities/_semantic_cutover/aliases.py:280:17 [missing-attribute] Object of type `FlextInfraProtocolsRopeRuntime.RopeSemanticModule | None` has no attribute `get_scope`
  Object of class `NoneType` has no attribute `get_scope`
  Object of class `RopeSemanticModule` has no attribute `get_scope`
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14/.reports/gates/20261122T043448.070689Z-4157781/check/34e3859e-6b19-4c8c-9d7c-0646cf9f7777/aihub-vkb1j.14/pyrefly.raw.log)
