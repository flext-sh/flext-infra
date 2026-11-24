# Workspace Check Report

Generated: 2026-11-21 20:52:27 UTC
Check phase: primary
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| flext-ezljc | FAIL | 5 |

## Details

### flext-ezljc
Root: `/home/marlonsc/flext/flext-infra/worktrees/flext-ezljc`
- lint: FAIL (3 issues)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/src/flext_infra/_utilities/_rope/project.py:1232:89 [line-too-long] Line too long (89 > 88)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/src/flext_infra/_utilities/_rope/project.py:1278:89 [line-too-long] Line too long (93 > 88)
  - /home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/src/flext_infra/_utilities/_rope/project.py:1279:89 [line-too-long] Line too long (91 > 88)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/.reports/gates/20261121T205206.362730Z-1676883/check/7e47153b-5892-40bc-93db-36c77ec57f8e/flext-ezljc/lint.raw.log)
- pyrefly: FAIL (2 issues)
  - src/flext_infra/_utilities/_rope/project.py:696:20 [bad-return] Returned type `AbstractModule | BuiltinModule` is not assignable to declared return type `BuiltinModule | PyModule | PyPackage`
  - src/flext_infra/_utilities/_rope/project.py:719:9 [missing-override-decorator] Class member `FlextInfraRopeProject.pycore` overrides a member in a parent class but is missing an `@override` decorator
  - Native output receipt: [pyrefly.raw.log](file:///home/marlonsc/flext/flext-infra/worktrees/flext-ezljc/.reports/gates/20261121T205206.362730Z-1676883/check/7e47153b-5892-40bc-93db-36c77ec57f8e/flext-ezljc/pyrefly.raw.log)
