# Workspace Check Report

Generated: 2026-11-20 02:14:19 UTC
Check phase: primary
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| flext-0in0k.32 | FAIL | 1 |

## Details

### flext-0in0k.32
Root: `/home/marlonsc/flext/worktrees/flext-0in0k.32`
- lint: PASS (0 issues)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/worktrees/flext-0in0k.32/.reports/gates/20261120T021352.757693Z-3877199/check/1ef65c37-a2f1-4fc3-b8ea-fee8ca965cc5/flext-0in0k.32/lint.raw.log)
- pyrefly: FAIL (1 issues)
  - src/flext_infra/_utilities/facade_components.py:32:5 [missing-module-attribute] Could not import `FlextInfraUtilitiesFacadeNamespace` from `flext_infra._utilities`
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/worktrees/flext-0in0k.32/.reports/gates/20261120T021352.757693Z-3877199/check/1ef65c37-a2f1-4fc3-b8ea-fee8ca965cc5/flext-0in0k.32/pyrefly.raw.log)
