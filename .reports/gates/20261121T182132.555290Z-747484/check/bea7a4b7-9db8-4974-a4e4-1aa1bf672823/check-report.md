# Workspace Check Report

Generated: 2026-11-21 18:21:49 UTC
Check phase: primary
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| setup-admission | FAIL | 1 |

## Details

### setup-admission
Root: `/home/marlonsc/flext/flext-infra/worktrees/setup-admission`
- lint: PASS (0 issues)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/setup-admission/.reports/gates/20261121T182132.555290Z-747484/check/bea7a4b7-9db8-4974-a4e4-1aa1bf672823/setup-admission/lint.raw.log)
- pyrefly: FAIL (1 issues)
  - tests/unit/codegen/project_verb_admission_tests.py:174:38 [bad-assignment] `list[str]` is not assignable to dict value type `bool | dict[str, JsonValue] | float | int | list[JsonValue] | str | None`
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/setup-admission/.reports/gates/20261121T182132.555290Z-747484/check/bea7a4b7-9db8-4974-a4e4-1aa1bf672823/setup-admission/pyrefly.raw.log)
