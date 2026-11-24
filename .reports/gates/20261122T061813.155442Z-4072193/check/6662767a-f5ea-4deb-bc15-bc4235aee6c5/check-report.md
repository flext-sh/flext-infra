# Workspace Check Report

Generated: 2026-11-22 06:18:28 UTC
Check phase: primary
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| flext-qfvdj | FAIL | 5 |

## Details

### flext-qfvdj
Root: `/home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj`
- lint: FAIL (5 issues)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/src/flext_infra/_utilities/_rope/native_project.py:79:13 [docstring-missing-exception] Raised exception `TypeError` missing from docstring
  - /home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/src/flext_infra/_utilities/_rope/native_project.py:94:89 [line-too-long] Line too long (89 > 88)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/src/flext_infra/_utilities/_rope/native_project.py:113:89 [line-too-long] Line too long (92 > 88)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/src/flext_infra/_utilities/_rope/native_project.py:206:26 [os-listdir] Use `pathlib.Path.iterdir()` instead.
  - /home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/src/flext_infra/_utilities/facade_components.py:619:9 [too-many-return-statements] Too many return statements (7 > 6)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/.reports/gates/20261122T061813.155442Z-4072193/check/6662767a-f5ea-4deb-bc15-bc4235aee6c5/flext-qfvdj/lint.raw.log)
- pyrefly: PASS (0 issues)
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-qfvdj/.reports/gates/20261122T061813.155442Z-4072193/check/6662767a-f5ea-4deb-bc15-bc4235aee6c5/flext-qfvdj/pyrefly.raw.log)
