# Workspace Check Report

Generated: 2026-11-21 18:18:25 UTC
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
- lint: PASS (0 issues)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/.reports/gates/20261121T181808.655477Z-714392/check/736ab7c7-612a-4029-93cf-4173d6d98223/flext-ezljc/lint.raw.log)
- pyrefly: FAIL (1 issues)
  - src/flext_infra/codegen/consolidator.py:201:28 [bad-argument-type] Argument `Generator[tuple[FlextInfraProtocolsRopeRuntime.RopeScope, tuple[str]]]` is not assignable to parameter `iterable` with type `Iterable[tuple[FlextInfraProtocolsRopeRuntime.RopeScope, tuple[()]]]` in function `list.extend`
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/.reports/gates/20261121T181808.655477Z-714392/check/736ab7c7-612a-4029-93cf-4173d6d98223/flext-ezljc/pyrefly.raw.log)
