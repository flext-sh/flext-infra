<!-- AUTO-GENERATED FILE — regenerate through `make gen APPLY=Y` from the workspace root. -->
<!-- Source of truth: `docs/guides/topology-conform.md`; adjust that source, never this projection. -->

# flext-infra - Repository-local topology and conformance

> Project profile: `flext-infra`

<!-- TOC START -->
- [Authorities](#authorities)
- [Validation boundary](#validation-boundary)
- [Makefile bootstrap projection](#makefile-bootstrap-projection)
- [Full refactor workflow](#full-refactor-workflow)
- [Selection and projections](#selection-and-projections)
- [uv project boundaries](#uv-project-boundaries)
<!-- TOC END -->

## Authorities

Each governed repository has exactly two local inputs:

- `.gitmodules` is the read-only authority for its direct topology. Its presence
  selects the `workspace` profile; its absence selects `standalone`.
- `config/beads.yaml` is the mandatory typed Beads identity with `version: 1`,
  `workspace`, `database`, `issue_prefix`, and the optional
  `custom_issue_types` owned by that repository.

Neither input is inferred from a parent checkout, a primary worktree,
`pyproject.toml`, a directory name, or another repository. A linked worktree
loads both files from that lane and every generated write remains in that lane.

## Validation boundary

Conformance validates the complete selected topology before planning writes. A
workspace validates each direct governed path declared by its own `.gitmodules`:

- the checkout exists and remains below the repository root;
- its origin matches the URL declared by `.gitmodules`;
- its branch follows the configured provider contract;
- its own `config/beads.yaml` exists and validates.

- the repository root's `config/beads.yaml` exists and validates.

## Makefile bootstrap projection

`codegen conform --what makefile --scope self` (the route `make setup` uses to
refresh a stale generated dispatcher) plans exactly one artifact from
declarations only. Its complete input set is the repository's own
`config/workspace.yaml` when that manifest exists, otherwise its PEP 621
metadata (`[project].name` plus `[project.urls].Repository` matched against a
declared provider), together with the packaged codegen configuration and
Makefile template and the current destination content needed for the
fixed-point comparison.

It reads nothing else. It does not invoke Git, Beads, `mise`, or `uv`; it does
not inspect `.gitmodules`, branch ancestry, linked worktrees, sibling checkouts,
or an environment manager. Those live-topology validations belong to `--what
all`.

Apply mode plans the projection twice before publication and requires identical
destination, content digest, content and removal intent. A planning failure or
nondeterministic result therefore leaves a pre-existing Makefile byte- and
inode-identical; the validated candidate is then promoted with one atomic write.

The Makefile projection requires a repository-local workspace declaration and
rejects broader scopes. `--what all` remains the operational conformance route:
it validates live topology, Beads, environments, and ancestry in addition to
planning every governed artifact.

## Full refactor workflow

Direct governed submodules have exactly one ledger mode. A checked-in `.beads`
symlink inherits the repository root's ledger and requires a routing-only
`config/beads.yaml` naming the same identity. A real `.beads` directory makes
the declared repository an independent ledger owner and requires its own local
identity. Standalone repositories are ledger owners with their own local
identity. A repository root never copies its identity into a declared repository
and never overwrites a declared repository's source config.
External provider URLs remain read-only dependency paths.

Missing, malformed, duplicate, escaping, or mismatched inputs fail before any
file write. Conformance does not generate, merge, reorder, fan out, or overwrite
`.gitmodules` or `config/beads.yaml` in an existing repository.

## Selection and projections

`codegen conform` accepts `self`, `declared_repositories`, and `all`. `self` always means
the requested checkout. `declared_repositories` and `all` are valid only from a workspace
whose own `.gitmodules` declares governed direct declared_repositories.

The generated `.beads/config.yaml` and `.beads/metadata.json` are projections of
the selected repository's owned Beads identity plus the fleet-owned Gas City
contract. Workspace root owns the shared ledger, direct submodules inherit it,
and standalone repositories own theirs. Rigs declare `inherited_city` and never
copy a city host or port; Gas City owns endpoint resolution and its
compatibility mirror. The custom-type projection preserves project extensions
first and appends the required Gas City baseline. Generation never starts,
stops, initializes, probes, or mutates Dolt.

The generated Makefile preserves the same boundary: workspace orchestration may
fan out to direct local declared_repositories, while standalone repositories and linked
worktrees own their runtime, environment, and writes locally.

## uv project boundaries

Physical repository ownership does not change when a checkout is mounted as a
gitlink. Every generated `pyproject.toml` therefore declares
`[tool.uv.workspace] members = []`: uv discovers that repository as its own
project and writes its lock, environment, and distributions below that root.

The composition root does not turn gitlinks into uv declared repositorys. It keeps
the same empty boundary and projects a local `{ path = ..., editable = true }`
source only for an internal dependency actually declared by the root project or
one of its dependency groups. The obsolete `workspace` dependency group and
topology-wide source list are removed. A present-but-unused gitlink produces no
dependency or source entry.

This layout is intentional: uv workspaces share one lock and environment and
reject a member that owns another `[tool.uv.workspace]` table. Static path
dependencies let the root resolve its real local dependencies without changing
the child revision. A missing declared path fails resolution; conformance never
falls back to a registry or Git source.
