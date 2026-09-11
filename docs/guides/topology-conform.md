# Repository-local topology and conformance

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

- the checkout exists and remains below the workspace root;
- its origin matches the URL declared by `.gitmodules`;
- its branch follows the configured provider contract;
- its own `config/beads.yaml` exists and validates.

Subprojects keep independent Beads identities. A workspace never copies its
identity into a subproject and never overwrites a subproject's source config.
External provider URLs remain read-only dependency paths.

Missing, malformed, duplicate, escaping, or mismatched inputs fail before any
file write. Conformance does not generate, merge, reorder, fan out, or overwrite
`.gitmodules` or `config/beads.yaml` in an existing repository.

## Selection and projections

`codegen conform` accepts `self`, `subprojects`, and `all`. `self` always means
the requested checkout. `subprojects` and `all` are valid only from a workspace
whose own `.gitmodules` declares governed direct subprojects.

The generated `.beads/config.yaml` and `.beads/metadata.json` are projections of
the selected repository's local Beads identity plus the fleet-owned Gas City
contract. Rigs declare `inherited_city` and never copy a city host or port;
Gas City owns endpoint resolution and its compatibility mirror. The custom-type
projection preserves project extensions first and appends the required Gas City
baseline. Generation never starts, stops, initializes, probes, or mutates Dolt.

The generated Makefile preserves the same boundary: workspace orchestration may
fan out to direct local subprojects, while standalone repositories and linked
worktrees own their runtime, environment, and writes locally.
