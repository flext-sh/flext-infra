# Workspace Check Report

Generated: 2026-11-22 01:24:13 UTC
Check phase: primary
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| flext-ezljc | FAIL | 1 |

## Details

### flext-ezljc
Root: `/home/marlonsc/flext/flext-infra/worktrees/flext-ezljc`
- lint: FAIL (1 issues)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/src/flext_infra/validate/_pytest_runner/base.py:146:9 [docstring-extraneous-exception] Raised exception is not explicitly raised: `ValueError`
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/.reports/gates/20261122T012351.091236Z-1633439/check/ea0adc00-9a84-4d73-9f71-8e0aa6d3157a/flext-ezljc/lint.raw.log)
- pyrefly: PASS (0 issues)
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/.reports/gates/20261122T012351.091236Z-1633439/check/ea0adc00-9a84-4d73-9f71-8e0aa6d3157a/flext-ezljc/pyrefly.raw.log)
