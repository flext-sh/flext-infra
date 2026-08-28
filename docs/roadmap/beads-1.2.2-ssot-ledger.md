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

## Validation log

| Time | SHA or worktree | Command/scope | Result | Follow-up |
| --- | --- | --- | --- | --- |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Repair generic configuration member fields altered by the topology vocabulary cutover |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Rewire documentation scope to repository-local project discovery |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Remove the obsolete attached-project selector contract |
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

## GitHub lifecycle

| Repository | Source branch | Pull request | Approval | Merge SHA | Integrated verification |
| --- | --- | --- | --- | --- | --- |
| `flext-infra` | `fix/beads-optout-preserve-state-20260827` | PENDING | PENDING | PENDING | PENDING |

The phase remains OPEN until every required repository has an independently
approved pull request, an explicit merge commit on its integration branch, and
passing validation evidence for that integrated SHA.
