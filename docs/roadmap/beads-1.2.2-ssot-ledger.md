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

## Validation log

| Time | SHA or worktree | Command/scope | Result | Follow-up |
| --- | --- | --- | --- | --- |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Repair generic configuration member fields altered by the topology vocabulary cutover |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Rewire documentation scope to repository-local project discovery |
| 2026-08-28 | worktree | Repository test gate | FAIL before collection | Remove the obsolete attached-project selector contract |
| 2026-08-28 | worktree | Repository test gate | FAIL: 1,112 passed, 264 failed, 1 error | Converge stale topology and mandatory local-override fixtures; remove retired refactor tooling |
| 2026-08-28 | worktree | Repository format gate, apply mode | PASS | Source slice formatted through the public Make surface |

## GitHub lifecycle

| Repository | Source branch | Pull request | Approval | Merge SHA | Integrated verification |
| --- | --- | --- | --- | --- | --- |
| `flext-infra` | `fix/beads-optout-preserve-state-20260827` | PENDING | PENDING | PENDING | PENDING |

The phase remains OPEN until every required repository has an independently
approved pull request, an explicit merge commit on its integration branch, and
passing validation evidence for that integrated SHA.
