# Topology and Conform Contract

<!-- TOC START -->
- [Effective topology](#effective-topology)
- [Full refactor workflow](#full-refactor-workflow)
- [Synchronization and setup](#synchronization-and-setup)
- [MCP / CRG identity (out of scope for conform)](#mcp-crg-identity-out-of-scope-for-conform)
<!-- TOC END -->

`flext-infra codegen conform` is the sole owner of repository conformance.
Consumers use the public `u.Infra` accessors and never import workspace detector
implementations directly.

## Effective topology

- Effective Make profiles are only `workspace-root` and `standalone`.
- A repository is a workspace root only when its live `.gitmodules`, its
  `WorkspaceSpec.members`, and each member's provider URL and
  `ProviderSpec.branch` agree exactly for at least one mutable first-party member.
- An attached governed member retains `WORKSPACE_MEMBER`/`SUBMODULE` relationship
  metadata but owns a standalone Makefile, `.mise.toml`, `.envrc`, `.venv`, lock,
  CI surface, and project runtime.
- A development lane owns a real lane-local `.venv`. START invokes `make setup`
  from the lane, with the lane as both project and runtime root; it never links to
  or mutates another checkout's environment.
- Generated `.envrc` files derive `PROJECT_ROOT` from the nearest
  `pyproject.toml` through direnv's documented `find_up` stdlib function. They
  do not depend on undocumented `DIRENV_*` variables, so strict evaluation is
  valid both at a repository root and under `direnv exec` from a subdirectory.
- External and fork Git links are observed from live Git metadata. Conform
  preserves their `.gitmodules` blocks but never initializes, updates, checks
  out, lints, type-checks, provisions, or otherwise manages them.
- `ProviderSpec.branch` is the only integration-baseline owner. Every governed
  local branch, `origin/*` branch, and registered worktree must descend from it;
  only the exact configured technical patterns are excluded.

Public accessors:

- `u.Infra.workspace_spec_load(repository_root: Path) -> Result[m.Infra.WorkspaceSpec]`
- `u.Infra.repository_conform_target(repository_root: Path,`
  `workspace: m.Infra.WorkspaceSpec | None = None)`
  `-> Result[m.Infra.RepositoryConformTarget]`
- `u.Infra.repository_provider(repository, providers) -> Result[m.Infra.ProviderSpec]`
- `u.Infra.repository_baseline_branch(repository, providers) -> Result[str]`

## Full refactor workflow

1. Add the new typed canonical owner and expose it through `m.Infra`, `p.Infra`,
   or `u.Infra` as appropriate.
2. Use ast-grep plus repository-wide search to enumerate every consumer,
   generated projection, template, fixture, and executable snippet.
3. Migrate all consumers atomically, then delete the old owner and its routes,
   templates, models, protocols, and tests. Old and new paths never coexist.
4. Exercise the real runtime contract before encoding confirmation in tests.
5. Run canonical Make tests, global lint/format/static gates, changed-scope
   Pyright/Mypy, generated-surface regeneration, and an idempotence pass.

## Synchronization and setup

The operator updates the current root through the repository's GitFlow before
starting conform; conform never guesses a merge or mutates root history.
Generated root setup handles only governed member paths: it fetches the
provider-owned branch and performs `git pull --ff-only` before validating the
recorded gitlink ancestry. Divergence fails closed with the exact command, exit
status, and stderr.

flext-infra has a projection-only Beads boundary. It writes the configured
selector/version to `.mise.toml` and, for selected projects, renders
`.beads/config.yaml` and `.beads/metadata.json`. It does not invoke the CLI,
inspect or initialize storage, install hooks, enforce tracking policy, or own
any tracker lifecycle.

## MCP / CRG identity (out of scope for conform)

The two `.beads/` files consume `ledger_id`, `ledger_prefix`, and optional server
values from `config/workspace.yaml`, with fleet defaults from
`config/codegen.yaml`. Runtime behavior belongs to each consuming project. MCP
gateway routing, CRG graph paths, memory `project_id` stores, and activation
inventory remain outside conform.
