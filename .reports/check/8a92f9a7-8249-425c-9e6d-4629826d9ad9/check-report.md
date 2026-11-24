# Workspace Check Report

Generated: 2026-11-17 22:20:57 UTC
Check phase: complete
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| flext-infra | FAIL | 3 |

## Details

### flext-infra
Root: `/home/marlonsc/flext-wip-flext-0in0k.32/flext-infra`
- lint: FAIL (3 issues)
  - /home/marlonsc/flext-wip-flext-0in0k.32/flext-infra/src/flext_infra/_utilities/facade_components.py:25:23 [redefined-while-unused] Redefinition of unused `ast` from line 15: `ast` redefined here
  - /home/marlonsc/flext-wip-flext-0in0k.32/flext-infra/src/flext_infra/_utilities/facade_components.py:786:9 [complex-structure] `_canonical_facade_source` is too complex (18 > 10)
  - /home/marlonsc/flext-wip-flext-0in0k.32/flext-infra/src/flext_infra/_utilities/facade_components.py:786:9 [too-many-branches] Too many branches (18 > 12)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext-wip-flext-0in0k.32/flext-infra/.reports/check/8a92f9a7-8249-425c-9e6d-4629826d9ad9/flext-infra/lint.raw.log)
- markdown: PASS (0 issues)
  - Native output receipt: [markdown.raw.log](file:///home/marlonsc/flext-wip-flext-0in0k.32/flext-infra/.reports/check/8a92f9a7-8249-425c-9e6d-4629826d9ad9/flext-infra/markdown.raw.log)
- deps: PASS (0 issues)
  - Native output receipt: [deps.raw.log](file:///home/marlonsc/flext-wip-flext-0in0k.32/flext-infra/.reports/check/8a92f9a7-8249-425c-9e6d-4629826d9ad9/flext-infra/deps.raw.log)
