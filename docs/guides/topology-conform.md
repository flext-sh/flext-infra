# Topology and Conform Contract

`flext-infra codegen conform` is the sole owner of repository conformance.
Consumers use the public `u.Infra` accessors and never import workspace detector
implementations directly.

## Effective topology

- Effective Make profiles are `workspace-root`, `workspace-member`, and
  `standalone`.
- A repository is a workspace root only when its live `.gitmodules`, its
  `WorkspaceSpec.members`, and each member's provider URL and
  `ProviderSpec.branch` agree exactly for at least one mutable first-party member.
- An attached governed member retains `WORKSPACE_MEMBER`/`SUBMODULE` relationship
  metadata but owns a standalone Makefile, `.mise.toml`, `.envrc`, `.venv`, lock,
  CI surface, and project runtime.
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
- `u.Infra.serialization_lock_execute(lock_paths, timeout_seconds,`
  `operation, *, timeout_failure, acquisition_failure)`
  `-> Result[TValue]`

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

Pre-venv Make bootstrap consumes only the generated `MAKE_PROFILE` and
`WORKSPACE_ROOT_REL` facts. Missing, invalid, or stale topology facts fail during
Make parsing with a regeneration instruction. Directory walking, parent-shape
guessing, and an implicit standalone mode are not supported.

## Exact Git-source executable releases

`ManagedGitToolRelease` is the generic owner for an executable built from an
official Git repository. Product identity and release policy remain in the
consumer manifest; flext-infra contains no consumer repository, commit, schema,
or installation-path constants.

The manifest declares a credential-free HTTPS source URL, exact full commit
OID, repository-relative source and output paths, an absolute build executable,
explicit build environment, the expected artifact SHA-256, an absolute immutable
artifact store, one absolute activation path, and one or more required runtime
probes. Commands may interpolate only `{source}`, `{output}`, and `{artifact}`.

The release engine performs these stages in order and stops at the first
disagreement:

1. fetch and detach the exact commit with isolated Git configuration;
2. verify source URL, commit object, clean checkout, absence of undeclared nested
   repositories, safe archive members, commit epoch, and archive digest;
3. build in an explicit environment with `SOURCE_DATE_EPOCH` owned by the commit;
4. verify a regular executable with the declared SHA-256 and run every probe
   against the staged artifact;
5. persist the artifact and JSON receipt as one immutable atomic file set;
6. activate an exact verified copy through a sibling temporary file and atomic
   replace, never through a symlink or alternate path.

Dry-run is the default. The canonical consumer surface is
`make release WHAT=managed-git-tool MANIFEST=/absolute/manifest.json`; persistence
and activation require `APPLY=Y`. A repeated release validates the existing
immutable store byte-for-byte and is idempotent. There is no PATH fallback,
implicit latest version, alternate installer, or old/new coexistence.
