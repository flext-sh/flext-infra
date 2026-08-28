# Beads 1.2.2 SSOT rollout ledger

This versioned ledger is the execution record for the FLEXT configuration
cutover. It records only Git, GitHub, static generation, and validation work.
No runtime database, daemon, lifecycle, or issue-tracker command is part of
this rollout.

## Operating state

- Phase: OPEN
- Integration branch: `0.12.0-dev`
- Active branch: `fix/beads-1.2.2-ssot-cutover-20260828`
- Static projection target: Beads `1.2.2`, `127.0.0.1:3307`
- Rope scope: conditional on execution context; any call below a repository
  carrying `.gitmodules` scans that entire workspace, independent of submodule
  declaration membership; a standalone call remains repository-local
- Independent approval: PENDING
- Integrated-SHA verification: PENDING

## Immutable checkpoints

| Time | Repository | Branch | SHA | Evidence |
| --- | --- | --- | --- | --- |
| 2026-08-28T07:45:11-03:00 | `flext-infra` | `fix/mise-beads-canonical` | `54b2ca8ecdc29fc5cdb28629bf3643238fa785a6` | WIP preserved and pushed to `origin` |
| 2026-08-28T07:46:32-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `4b6a6e1be11fc55027304b9a93868f91691a4b3e` | WIP preserved and pushed to `origin` |
| 2026-08-28T07:48:14-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `713d99d8d7d2f352d04335b4a40c76ce62a5bfa8` | Useful lane content consolidated by a two-parent merge and pushed to `origin` |
| 2026-08-28T08:04:46-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `88425ac9eeae9a649b0a335564359ba79951c87b` | Repository-local topology and deterministic public alias gate checkpoint pushed to `origin` |
| 2026-08-28T08:05:17-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `5f318098edf144639cb56255b0ed86ce9f2ee790` | Manual rollout ledger checkpoint pushed to `origin` |
| 2026-08-28T08:07:38-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `15cec463e514ec50af9b1813c2716ca224d3cc84` | Residual canonical distribution pin lane preserved by a two-parent merge and pushed to `origin` |
| 2026-08-28T08:19:35-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `a06217d0885d68d29134f972b017fce8834d92d7` | Topology-local, one-pass-idempotent generation fixes pushed to `origin` |
| 2026-08-28T08:27:37-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `b08c6ffb3c52ae77d9c1a77ea5b69a7646cf1eb7` | Static projections, launchers, 75-entry Mise lock, and owner-driven report/cache cleanup pushed to `origin` |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `fc498bad217ef8f12dbb0def079c10837dc26b78` | Repository-local topology fixture convergence pushed to `origin` |
| 2026-08-28T08:57:35-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `0acb0ba7e9951e63c8324f075569195057735114` | Conditional execution-context Rope scope, standalone isolation, and manual evidence pushed to `origin` |
| 2026-08-28T09:12:58-03:00 | `flext-infra` | `fix/mise-beads-canonical` | `e47da1189e01c432f9ce2154c60c42381a6f9792` | Dirty canonical lane checkpointed in full and pushed before consolidation |
| 2026-08-28T09:16:22-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `8398a4c409e9024e3b94d555135cf48766e61049` | Canonical Mise lane consolidated by a two-parent merge; conflicts resolved to the final repository-local contract and pushed |
| 2026-08-28T09:41:16-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `7d535be725af122fae5c76afb8146957fd9644c3` | Required static endpoint restored from the typed codegen SSOT; obsolete override/workspace fixtures, runtime-hook projection, and tracked backup removed; checkpoint pushed |
| 2026-08-28T09:58:21-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `a9f4b8f2e7b6475797b244163cea932e8e844a00` | Retired facade-inheritance scanners, migrators, transformers, hidden Rope post-hook, models, routes, and obsolete tests removed; generated public exports converged and checkpoint pushed |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `f033fc4bd` | Retired-tooling validation evidence recorded and pushed |
| 2026-08-28T10:22:00-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `97d55739ced18c5a59fa997582de7dc7925b1f11` | Repository-local topology owners, typed `base.mk` validation, static projection convergence, and final active-vocabulary cleanup pushed |
| 2026-08-28T10:26:09-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `584189ddc4fb61e33deff2c3c9432d63ef9acdc0` | Full static-gate defects repaired at their owners and the green checkpoint pushed |
| 2026-08-28T10:32:34-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `3e88c4aadf77674ddf93c7e59226a8c59d213d84` | Standalone Rope discovery bounded to a repository owner while execution anywhere below a `.gitmodules` workspace still scans the complete workspace; checkpoint pushed |
| 2026-08-28T10:48:08-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `e2d595bf4fa862594ca89316ca5992c53e2dcd5e` | Shared typed test authorities replaced copied repository/project/Beads fixtures; 178 lines removed and checkpoint pushed |
| 2026-08-28T10:51:59-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `5fd68fec2412845d9db48ef475c19402403ad5b2` | Conform preserves dependency policy outside the selected owner surface and accepts a baseline already present in an active non-FF merge; checkpoint pushed |
| 2026-08-28T11:04:38-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `9f7b006d1bb16995e7455dff0f666f3d204c60e6` | Setup bootstrap preserves the requested UV selector until Mise exposes the installed executable; fixture duplication reduced and checkpoint pushed |
| 2026-08-28T11:09:57-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `93b42f4b97490b5407c16f73734c2a3907761657` | Pyright include roots and execution environments derive from one repository-local topology owner; 25 net lines removed and checkpoint pushed |
| 2026-08-28T11:15:02-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `d273cb900c03561b19d501a0b134c6b479ab68a4` | Standalone conform fixtures derive from one typed test authority; 10 net lines removed and checkpoint pushed |
| 2026-08-28T11:19:28-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `ec7f3ad6bc7190764436203b1f933b7841416796` | Setup consumers use the shared static Mise lock fixture; all 16 submodule setup cases and both real Make topologies passed before push |
| 2026-08-28T11:29:00-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `eba211f52146e4d137629472b11f7c657c937edc` | Removed a fake public setup action, swallowed bootstrap failure, duplicated Make owner test, and copied default description; 19 net lines removed and checkpoint pushed |
| 2026-08-28T11:34:43-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `ca6972adcd794e0b8ee8c921c9c330a8111f0768` | Standalone lock ownership and conditional Rope workspace fixture aligned with repository-local topology; six net lines removed and checkpoint pushed |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `eefd777d6` | Incremental suite convergence and its remaining defects recorded and pushed |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `c2165b61a` | Green static and byte-idempotent generation evidence recorded and pushed |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `d1126b35c` | Stale generated contract copies removed from tests; 21 net lines removed and checkpoint pushed |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `0ad635785` | Complete green test and coverage evidence recorded and pushed |
| 2026-08-28 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `be442f8f8` | Residual active policy vocabulary removed from comments and checkpoint pushed |
| 2026-08-28T12:11:10-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `0bc446d9f` | Full-suite worker budget reduced at its typed owner after repeated memory exhaustion; seven net lines removed and checkpoint pushed |
| 2026-08-28T12:16:16-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `fc68f07da` | Stable complete-suite evidence recorded and pushed after the typed worker-budget repair |
| 2026-08-28T12:17:59-03:00 | `flext-infra` | `fix/beads-optout-preserve-state-20260827` | `c7a2818e0` | Final static and zero-residue evidence recorded and pushed |
| 2026-08-28T12:19:08-03:00 | `flext-infra` | `fix/beads-1.2.2-ssot-cutover-20260828` | `c7a2818e0` | Neutral replacement lane created at the fully validated tip and pushed without altering the preserved predecessor |
| 2026-08-28T12:20:04-03:00 | `flext-infra` | `fix/beads-1.2.2-ssot-cutover-20260828` | `24688ac22` | Active-lane transition recorded and pushed before opening the replacement pull request |

## Validation log

| Time | SHA or worktree | Command/scope | Result | Follow-up |
| --- | --- | --- | --- | --- |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Repair generic configuration member fields altered by the topology vocabulary cutover |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Rewire documentation scope to repository-local project discovery |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Remove the obsolete topology selector contract |
| 2026-08-28 | worktree | Repository test gate | FAIL: 1,112 passed, 264 failed, 1 error | Converge stale topology and mandatory local-override fixtures; remove retired refactor tooling |
| 2026-08-28 | worktree | Repository format gate, apply mode | PASS | Source slice formatted through the public Make surface |
| 2026-08-28 | worktree | Repository-local topology contract | PASS: 14 tests | Own override, own `.gitmodules`, parent isolation, and distinct subproject identities verified |
| 2026-08-28 | worktree | Linked-worktree/static generation contract | PASS: 5 tests | Invalid input fails before writes; lane inputs are preserved; first apply reaches a fixed point |
| 2026-08-28 | worktree | Canonical alias public fix | PASS: 1 focused test | Deterministic rewrite and byte-stable clean file verified without lazy-facade instrumentation |
| 2026-08-28 | worktree | VS Code owner | PASS: 4 tests | Root and standalone render byte-equivalent documents; second render is stable |
| 2026-08-28 | worktree | `make gen WHAT=apply APPLY=Y` | PASS: 12 projections changed; conformance self-check reached a fixed point | Generated static projections and launchers; first lock attempt remained open because unauthenticated GitHub API quota was exhausted |
| 2026-08-28 | worktree | Official clean owner | PASS | Removed tracked `.reports/**`, `.testmondata`, and tool caches without touching substantive or unknown WIP |
| 2026-08-28 | worktree | Second codegen apply | PASS: 0 conformance changes | Confirmed byte-stable codegen before lock resolution |
| 2026-08-28T08:25:59-03:00 | worktree | Authenticated official generation and static Mise lock | PASS: 12 tools, 75 platform entries | Resolved `github:gastownhall/beads@1.2.2` as static metadata only; no Beads executable or runtime command invoked |
| 2026-08-28T08:26:52-03:00 | worktree | `make gen WHAT=check` with isolated launcher and lock scratch | PASS | Fresh independent resolution matched generated projections and `mise.lock` byte-for-byte |
| 2026-08-28 | worktree | Full repository test gate after static-generation checkpoint | FAIL: 2,417 collected; 194 failures and 15 errors observed before hard timeout | Pytest reached the official 600-second wall at 99%; converge mandatory local-identity and retired-topology fixtures, then investigate the non-terminating codegen entry-point worker |
| 2026-08-28 | worktree | Real `.gitmodules` test fixture consumer | PASS: 2 tests | Test topology helper declares only repository-local Git entries |
| 2026-08-28 | worktree | Manifestless existing-repository contract | PASS: 2 tests | Required typed `config/beads.yaml` replaces the removed standalone helper |
| 2026-08-28 | worktree | Documentation scope with repository-local topology | PASS: 5 selected tests | Shared fixtures now carry local identities and own `.gitmodules`; root/child scope selection converges |
| 2026-08-28T08:55:36-03:00 | worktree | `make test WHAT=all FILE=tests/unit/test_infra_rope_service.py` from `flext-infra` | EXPECTED RED: 19 passed, 1 failed | Proved an internal project call incorrectly stayed local before the production owner changed |
| 2026-08-28T08:56:34-03:00 | worktree | `make test WHAT=all FILE=tests/unit/test_infra_rope_service.py` from `flext-infra` | PASS: 20 tests | Workspace-root, internal-project, and internal-package calls all index the full workspace, including an undeclared internal project; standalone remains local |
| 2026-08-28T08:57:13-03:00 | worktree | `make fmt WHAT=apply APPLY=Y` from `flext-infra` | PASS: 1 file reformatted, 887 unchanged | Formatted the current source/test slice through the canonical Make owner |
| 2026-08-28T08:57:50-03:00 | worktree | `make test WHAT=all FILE=tests/unit/discovery/test_infra_discovery_edge_cases.py` from `flext-infra` | PASS: 4 selected, 2 impact-deselected | Repository-local generic pyproject discovery stays isolated from parent and sibling trees |
| 2026-08-28T08:59:11-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_codegen_catalog_extensions.py` from `flext-infra` | PASS: 5 tests | Removed the obsolete second workspace manifest fixture while retaining generic selector, setup/gen ownership, and TOML composition coverage |
| 2026-08-28T08:59:32-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_codegen_ci_matrix.py` from `flext-infra` | FAIL: 20 failed, 2 passed | New-project helper lacked mandatory local Beads identity; three remaining expectations also described divergent current CI policy |
| 2026-08-28T09:00:43-03:00 | worktree | Same CI matrix test gate after typed local Beads fixture repair | FAIL: 19 passed, 3 failed | One matcher defect and the unresolved automatic CI-matrix owner/template contradiction remained |
| 2026-08-28T09:02:24-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_codegen_ci_matrix.py::TestCodegenCiMatrix::test_dependabot_uses_uv_dependency_cooldown` from `flext-infra` | PASS: 1 test | Corrected set equality assertion; two CI auto-run policy tests remain intentionally unresolved pending operator direction |
| 2026-08-28T09:02:54-03:00 | worktree | `make fmt WHAT=apply APPLY=Y` from `flext-infra` | PASS: 888 files unchanged | Current WIP is formatter-clean |
| 2026-08-28T09:17:13-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_codegen_ci_matrix.py` from `flext-infra` | PASS: 21 tests | Removed the automatic-run selector; static dispatch-only CI matrix and generated project consumers are green |
| 2026-08-28T09:18:44-03:00 | worktree | `make fmt WHAT=apply APPLY=Y` from `flext-infra` | PASS: 5 files reformatted, 885 unchanged | Merge-adopted Mise source/tests and the CI policy cut are formatter-clean |
| 2026-08-28T09:41:16-03:00 | worktree | `make gen WHAT=apply APPLY=Y` from `flext-infra` | PASS: final conform apply changed 0 files; fixed-point check and static Mise artifact validation passed | `.beads/config.yaml` and `.beads/metadata.json` project `127.0.0.1:3307` from the required typed endpoint; no Beads executable invoked |
| 2026-08-28T09:41:16-03:00 | worktree | Focused pyproject topology/config gates | PASS: 6 topology-source, 2 gitignore-policy, and 12 pyproject-conform tests | Removed the retired override schema, projected declared versions, and kept standalone/workspace provenance deterministic |
| 2026-08-28T09:41:16-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_codegen_beads_projection.py` | PASS: 3 tests | Local identity plus the codegen-owned endpoint produce static Beads projections without a runtime surface |
| 2026-08-28T09:41:16-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_workspace_root_setup_submodules.py` | PASS: 2 tests | Generated workspace Make syntax is valid and initializes only the declared gitlink before environment provisioning |
| 2026-08-28T09:41:16-03:00 | worktree | `make test WHAT=all FILE=tests/unit/codegen/test_root_artifact_ownership.py` | PASS: 7 tests | Existing-repository fixed point, GitHub ownership bijection, and bounded ancestry fetch are green |
| 2026-08-28T09:41:16-03:00 | worktree | `make fmt WHAT=apply APPLY=Y` from `flext-infra` | PASS: 1 file reformatted, 889 unchanged | Current checkpoint is formatter-clean |
| 2026-08-28T09:53:59-03:00 | worktree | `make gen WHAT=init APPLY=Y` from `flext-infra` | PASS: apply and check each scanned 51 package directories with 0 errors and 0 warnings | Generated lazy public exports removed every retired module and reached a byte-stable point while Rope indexed the containing workspace from the subproject call |
| 2026-08-28T09:57:32-03:00 | worktree | Focused retired-tooling regression gates through typed `FILE=` selectors | PASS: 3 refactor service, 27 census CLI, and 36 namespace-enforcer tests | Surviving composition-based refactor paths remain green after removing hidden migration and inheritance-shape behavior |
| 2026-08-28T09:57:32-03:00 | worktree | Focused Beads/topology gates through typed `FILE=` selectors | PASS: 2 selected static-projection and 14 repository-local topology tests | Static Beads projection and repository-local generic topology remain unchanged by the refactor-tooling cut |
| 2026-08-28T09:58:21-03:00 | worktree | `make fmt` | PASS: 869 files already formatted | Published structural checkpoint is formatter-clean |
| 2026-08-28T10:22:00-03:00 | worktree | Canonical `base.mk` generator plus focused renderer/bootstrap tests | PASS: generated with `--project-name flext-infra`; 8 renderer and 2 foreign-CWD/topology tests passed | Empty defaults have no trailing whitespace; a nested standalone checkout ignores parent workspace markers |
| 2026-08-28T10:22:00-03:00 | worktree | `make test FILE=tests/unit/validate/basemk_validator_tests.py` and real `validate basemk-validate --workspace .` | PASS: 11 tests; real CLI exit 0 | Freshness validation reads `[project].name` from the canonical pyproject owner and accepts the generated `flext-infra` projection |
| 2026-08-28T10:22:00-03:00 | worktree | `make fmt WHAT=apply APPLY=Y`; two `make gen WHAT=apply APPLY=Y`; `make gen WHAT=check` | PASS: 869 files formatter-clean; both applies changed 0 files; all fixed-point and static Mise checks passed with 12 tools/75 entries | Static projections are byte-stable; the Beads distribution was resolved only as lock metadata and no runtime command was invoked |
| 2026-08-28T10:22:00-03:00 | worktree | Tracked-source zero-residue audit plus `git diff --check` | PASS: no retired vocabulary, tracked backups, positive parent inference, or Beads runtime/fallback prose; diff hygiene clean | Removed an orphan codemod rule and retained negative topology tests as behavioral evidence |
| 2026-08-28T10:23:35-03:00 | worktree | First full `make check` after the topology checkpoint | FAIL: 5 lint, 1 Pyright, and 2 Mypy errors; smells, markdown, Pyrefly, and security passed | Removed cutover orphans and corrected typed lock-payload/test boundaries before proceeding |
| 2026-08-28T10:25:57-03:00 | worktree | Full `make check` after owner repairs | PASS: lint, smells, markdown, Pyrefly, Mypy, security, and Pyright all reported 0 errors; 0 skips | Static gate stage is green and the repair was pushed as `584189ddc4fb61e33deff2c3c9432d63ef9acdc0` |
| 2026-08-28T10:28:36-03:00 | `098a074d40e27a864f04561e91ed83eda7f79203` | Full `make test` with the canonical testmon selection | FAIL: 68 failed, 721 passed in 72s | Failures group into stale retired-schema/Make expectations plus Rope adopting an unowned ancestor `src` directory for temporary non-repositories; phase remains RED and no PR is opened |
| 2026-08-28T10:31:09-03:00 | worktree | `make fmt WHAT=apply APPLY=Y`; Rope service, lazy-init, and lazy-map focused gates | PASS: formatter-clean; 21 Rope, 4 lazy-init, and 4 lazy-map tests | A standalone scratch directory no longer inherits an unrelated ancestor `src`; calls at the workspace root, an internal project, or an internal package retain whole-workspace Rope scope, including undeclared internal projects |
| 2026-08-28T10:51:59-03:00 | worktree | Conform focused gate, including three exact owner-boundary regressions | PASS: all 36 cases covered across the impact-selected file run and exact regressions; 0 failures, warnings, or skips | Shared fixtures derive from typed authorities; upstream facets, pending merge ancestry, and dependency-surface ownership are deterministic |
| 2026-08-28T11:04:38-03:00 | worktree | Generated Make environment focused gate | PASS: all 11 cases covered across the two setup variants and the 9 impact-selected cases; 0 failures, warnings, or skips | Real recursive Make/Mise setup, hostile-environment isolation, dependency upgrade, and dispatch behavior are green; no prohibited runtime binary was invoked |
| 2026-08-28T11:04:54-03:00 | `9f7b006d1bb16995e7455dff0f666f3d204c60e6` | `git fetch origin 0.12.0-dev`; integration ancestry | PASS: feature is 0 commits behind and 44 ahead of `origin/0.12.0-dev` | No integration commit is waiting to be merged; explicit non-FF integration remains pending after full green validation and approval |
| 2026-08-28 | worktree | Pyright, conform, hook, setup-submodules, Make owner/scope, and real setup focused gates | PASS: 8 Pyright, all 36 conform cases, 8 hook, all 16 submodule setup cases, 11 generated Make environment cases, and both real setup topologies covered | Shared fixture/config authorities replaced copied defaults while preserving the public Make behavior |
| 2026-08-28 | worktree | Canonical incremental `make test` | FAIL: 2 failed, 621 passed in 57.61s | Remaining defects were an undeclared workspace in one Rope fixture and the obsolete rule that ignored the authoritative standalone `uv.lock` |
| 2026-08-28 | worktree | Rope transitive-parent and standalone lock focused gates through `make test FILE=...` | PASS: 1 test each; Git also reports `uv.lock` as trackable | Empty local `.gitmodules` activates whole-workspace Rope scope; standalone Python/lock projections derive from the same SSOT section with duplicate lock entries removed |
| 2026-08-28 | worktree | `make gen WHAT=apply APPLY=Y` after lock-policy repair | PASS: one `.gitignore` projection changed; conform fixed point and static Mise validation passed with 12 tools/75 entries | Beads was resolved only as static lock provenance; no Beads executable, daemon, database, or endpoint was invoked |
| 2026-08-28 | `eefd777d6` | `make fmt WHAT=apply APPLY=Y`; full `make check` | PASS: 869 files unchanged; lint, smells, markdown, Pyrefly, Mypy, security, and Pyright reported 0 errors and 0 skips | Published source checkpoint is formatter-clean and all seven static gates are green |
| 2026-08-28 | `eefd777d6` | Two consecutive `make gen WHAT=apply APPLY=Y`, then `make gen WHAT=check` | PASS: both applies changed 0 projections; every conform fixed point and static 12-tool/75-entry Mise comparison passed | Independent repeated generation is byte-stable; no runtime Beads, database, daemon, or endpoint command was invoked |
| 2026-08-28 | `c2165b61a` | First complete `COV=Y make test` without testmon | FAIL: 14 failed, 2,374 passed in 116.75s | Ten failures shared one fixture that rewrote unchanged manual inputs; four copied expectations lagged their typed/generated owners; no PR opened while RED |
| 2026-08-28 | `d1126b35c` | Focused owner/consumer regressions through public `make test MATCH=...` | PASS: managed-conflict bootstrap, external Make owner, composed aliases, repository-local identity, and all 9 workspace Make contracts | Removed 21 net lines of stale copied tests and avoided invoking the mutable Mise-lock pipeline in a read-only owner test |
| 2026-08-28 | `d1126b35c` | Complete `COV=Y make test` without testmon, random seed `64059993` | PASS: 2,386 tests in 117.67s; 80.22% coverage against 45% minimum | Zero test failures, errors, skips, or warnings reported; full collection includes generated consumers, integration tests, Rope, topology, setup, and canonical-alias behavior |
| 2026-08-28T12:02:09-03:00 | `be442f8f8` | Full `make check` | PASS: all seven static stages; 0 errors and 0 skips | The final published source/documentation checkpoint is clean across lint, smells, Markdown, Pyrefly, Mypy, security, and Pyright |
| 2026-08-28T12:04:35-03:00 | `be442f8f8` | Two consecutive `make gen WHAT=apply APPLY=Y`, then `make gen WHAT=check` | PASS: both applies changed 0 projections; all fixed-point and 12-tool/75-entry static Mise comparisons passed | Final projections are byte-stable; artifacts were downloaded only for checksum/provenance and no Beads executable or service was invoked |
| 2026-08-28T12:05:10-03:00 | `be442f8f8` | Complete `COV=Y make test` without testmon, random seed `2659627366` | ENVIRONMENTAL RED: 597 passed before an xdist worker raised `MemoryError` while pytest formatted an exception | No functional failure was reported; preserve the RED, verify the named case in isolation, then repeat the complete official gate without changing code |
| 2026-08-28T12:06:37-03:00 | `be442f8f8` | `make test FILE=tests/unit/codegen/test_codegen_ci_matrix.py MATCH=fedora_dockerfile_installs_libatomic_only_for_fedora` | PASS: 1 selected, 20 deselected | The xdist crash item passes through the public Make boundary; the transient worker failure remains recorded rather than hidden |
| 2026-08-28T12:09:10-03:00 | `a5d67d071` | Second complete `COV=Y make test` without testmon, random seed `3720813960` | FAIL: 4 memory-exhausted cases, 2,382 passed in 101.64s | Repetition disproved a one-off worker crash; reduce only the typed fixed-worker owner, retain parallel execution, and regenerate its Make projection |
| 2026-08-28T12:12:36-03:00 | `0bc446d9f` | Focused typed pytest policy/runner gates through `make test FILE=... MATCH=...` | PASS: 1 selected case in each owner test file | The runner consumes the generated worker count and the tooling model round-trips its SSOT; prior testmon-only deselections were not counted as passes |
| 2026-08-28T12:16:00-03:00 | `0bc446d9f` | Complete `COV=Y make test` without testmon, random seed `1650846145` | PASS: 2,386 tests in 179.87s; 80.22% coverage against 45% minimum | Two fixed workers completed every subprocess-heavy case with zero failures, errors, warnings, or skips; no retry, dynamic fallback, or timeout expansion was added |
| 2026-08-28T12:17:25-03:00 | `fc68f07da` | Full `make check` | PASS: all seven static stages; 0 errors and 0 skips | Lint, smells, Markdown, Pyrefly, Mypy, security, and Pyright are green after the worker-budget projection and validation evidence update |
| 2026-08-28T12:17:48-03:00 | `fc68f07da` | Precise tracked-content, filename, runtime-command, topology, and static-projection audit | PASS: zero active retired-contract or prohibited-command matches; projections equal `1.2.2`, `flext`, and `127.0.0.1:3307` | Historical ledger wording and its recorded branch names are evidence, not executable/product contract; production has no parent inference or runtime Beads surface |
| 2026-08-28T12:18:43-03:00 | `c7a2818e0` | `git fetch origin 0.12.0-dev` and integration ancestry | PASS: feature is 0 commits behind and 59 ahead; `origin/0.12.0-dev` is an ancestor | No synchronization merge is needed; the next required graph edge is the explicit non-FF PR merge after operator approval |
| 2026-08-28T12:21:00-03:00 | `24688ac22` | GitHub pull-request lifecycle | OPEN: replacement PR [#444](https://github.com/flext-sh/flext-infra/pull/444) targets `0.12.0-dev`; superseded #441 links to it | Approval and merge remain pending; predecessor branches stay preserved until the integrated SHA proves complete adoption |

## Unresolved boundaries

- Canonical tracking remains suspended by current operator instruction. No
  tracker, daemon, database, lifecycle, or endpoint command is permitted; the
  phase remains OPEN and evidence is recorded in this ledger plus Git/GitHub.
- The checked-out FLEXT command router still names three superseded home-level
  skill paths. Current installed owners were used for this slice; repairing that
  generated governance projection is not yet part of this checkpoint.

## GitHub lifecycle

| Repository | Source branch | Pull request | Approval | Merge SHA | Integrated verification |
| --- | --- | --- | --- | --- | --- |
| `flext-infra` | `fix/beads-1.2.2-ssot-cutover-20260828` | [#444](https://github.com/flext-sh/flext-infra/pull/444) | PENDING | PENDING | PENDING |

The phase remains OPEN until every required repository has an independently
approved pull request, an explicit merge commit on its integration branch, and
passing validation evidence for that integrated SHA.
