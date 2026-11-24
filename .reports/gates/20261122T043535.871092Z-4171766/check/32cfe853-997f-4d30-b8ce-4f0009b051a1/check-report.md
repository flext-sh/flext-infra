# Workspace Check Report

Generated: 2026-11-22 04:35:49 UTC
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
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14/.reports/gates/20261122T043535.871092Z-4171766/check/32cfe853-997f-4d30-b8ce-4f0009b051a1/aihub-vkb1j.14/lint.raw.log)
- pyrefly: FAIL (1 issues)
  - src/flext_infra/_utilities/_semantic_cutover/aliases.py:280:17 [missing-attribute] Object of class `RopePyObject` has no attribute `get_scope`
  Did you mean `get_type`?
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/aihub-vkb1j.14/.reports/gates/20261122T043535.871092Z-4171766/check/32cfe853-997f-4d30-b8ce-4f0009b051a1/aihub-vkb1j.14/pyrefly.raw.log)
