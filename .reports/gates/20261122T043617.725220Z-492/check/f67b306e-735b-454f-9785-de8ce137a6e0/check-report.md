# Workspace Check Report

Generated: 2026-11-22 04:36:32 UTC
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
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14/.reports/gates/20261122T043617.725220Z-492/check/f67b306e-735b-454f-9785-de8ce137a6e0/aihub-vkb1j.14/lint.raw.log)
- pyrefly: FAIL (1 issues)
  - src/flext_infra/_utilities/_semantic_cutover/aliases.py:287:17 [bad-argument-type] Argument `FlextInfraProtocolsRopeRuntime.RopeScope | None` is not assignable to parameter `scope` with type `FlextInfraProtocolsRopeRuntime.RopeScope` in function `flext_infra._utilities._rope.runtime_modules.FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol`
  Protocol `RopeScope` requires attribute `parent`
  The declared type does not allow `None`. Consider narrowing the value with an `is not None` check.
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14/.reports/gates/20261122T043617.725220Z-492/check/f67b306e-735b-454f-9785-de8ce137a6e0/aihub-vkb1j.14/pyrefly.raw.log)
