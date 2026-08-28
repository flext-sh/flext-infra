# Beads 1.2.2 SSOT rollout ledger

This versioned ledger is the execution record for the FLEXT configuration
cutover. It records only Git, GitHub, static generation, and validation work.
No runtime database, daemon, lifecycle, or issue-tracker command is part of
this rollout.

## Operating state

- Phase: OPEN
- Integration branch: `0.12.0-dev`
- Active branch: `fix/beads-optout-preserve-state-20260827`
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
| `flext-infra` | `fix/beads-optout-preserve-state-20260827` | PENDING | PENDING | PENDING | PENDING |

The phase remains OPEN until every required repository has an independently
approved pull request, an explicit merge commit on its integration branch, and
passing validation evidence for that integrated SHA.
