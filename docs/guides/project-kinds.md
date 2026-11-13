# Project kinds

The FLEXT toolchain governs a repository by its kind. Generation, the gates and the Make
verbs follow it. A project declaration that omits `package_name` derives the `consumer`
kind; every other kind owns its package.

| Kind               | Owns a `src` package | Use it for                                                |
| ------------------ | -------------------- | --------------------------------------------------------- |
| `internal_flext`   | yes                  | A FLEXT library, service or application (the default).    |
| `consumer`         | no                   | A deployment or client repository over a pinned engine.   |
| `internal`         | yes                  | A first-party repository outside the FLEXT facade family. |
| `third_party_fork` | external             | A fork that keeps its upstream contracts.                 |

## Consumer repositories

A `consumer` repository has no code of its own. It pins the distribution it consumes,
which provides the CLI and the public API, and carries only configuration,
documentation and tests that exercise that distribution. A client incident repository
that runs an engine against the client's databases is the model case.

Use `consumer` when every behavior lives in the consumed distribution. A repository that
owns Python modules under `src/` is an `internal_flext` project: a consumer rejects an
authored `src` tree when it is scaffolded.

### What it may contain

- `config/` for the declaration, the tooling overlay and the consumed engine's inputs.
- `docs/` for authored documentation; the generated portal and guides index are added.
- `tests/` for pytest suites over the installed distribution's public API, with the
  FLEXT test conventions: one test class per module and imports through the generated
  `tests` namespace.
- `scripts/` for thin command surfaces declared as Make verbs.

### Declaration

The consumed distribution is a runtime requirement of the declaration. A private source
is pinned by commit, so the lock and every checkout resolve the same engine. The
`project` block declares no `package_name`: that omission is what makes the repository a
consumer. `upstream` names the import package whose public facades (`c`, `m`, `p`, `t`,
`u`) the test facades compose.

```yaml
Infra:
  codegen:
    repository:
      project:
        class_stem: ClientIncident
        namespace: ClientIncident
        constant_name: client-incident
        namespace_attribute: incident
        alias: incident
        environment_prefix: CLIENT_INCIDENT_
        description: Client incident repository over the dc-recon engine
        license: MIT
        author_name: Author Name
        author_email: author@example.com
        upstream: dc_recon
        flext_source: flext-infra @ git+https://github.com/flext-sh/flext-infra.git@0.12.0-dev
        runtime_dependency_overlay:
        - dc-recon @ git+ssh://git@github.com/example/cosmos-recon.git@<commit-sha>
        namespace_scan_dirs: []
        homepage: https://github.com/example/client-incident
        documentation: https://github.com/example/client-incident/blob/main/README.md
        repository_root_rel: .
        year: 2026
      integration:
        provider: example
        branch: main
      namespace_scan_dirs: [tests]
```

The declaration is validated once: a consumer declares its `project`, and ships no
package, module, data or console script. Every other kind declares its `package_name`.

### What is generated

`make gen` projects the same governed surface as for any project, without the package
parts:

- `pyproject.toml` is an unpackaged uv project: no `[build-system]`, no Hatch targets,
  `[tool.uv] package = false`, and the consumed distribution under `dependencies`. uv
  locks it as a virtual project and installs the dependency with its console scripts,
  so the engine's CLI is on the project's `.venv/bin`.
- `Makefile`, `.mise.toml`, `.gitignore`, `.envrc`, CI workflows, the README and the
  documentation portal. The README and portal omit the module map and the public
  surface, which a repository without a package does not have.
- `tests/__init__.py`, the generated `tests` namespace.
- Nothing under `src/`: the scaffold seeds no package family and no `_config.py`,
  `_settings.py` or protocol model projection.

### Gates

Each gate selects itself from the repository's own facts, so `make check` runs every
gate on what the repository has: lint, format, the type checkers, security, markdown,
duplication, layout, direnv, the lock and environment proofs and the codemod catalog run
over `tests/`, `config/` and `docs/`. Two gates are not applicable because they judge a
package's own source: the fresh-process import gate imports the checkout's package, and
the dependency scan compares the imports of production source with the declaration. A
consumer owns neither; its tests prove the consumed distribution is importable and
usable.

### Bootstrap

A new consumer starts from its declaration, its documentation and its tests. Copy the
governed `.mise.toml` and `mise.lock` from a governed checkout, then:

```bash
flext-infra codegen init --repository-root .   # generate the project surface
make upg                                       # first lock and toolchain
make setup                                     # install the locked environment
flext-infra codegen scaffold --repository-root .   # seed the test facades
make gen
make mod
make fix
make fmt
make check
```

`codegen init` runs before the consumed distribution is installed, so it does not seed
test facades: those compose the distribution's facades and are seeded by
`codegen scaffold` once `make setup` installed it.

### Adding a dependency

Declare the new requirement in the repository declaration and run `make lock`. It
resolves the new requirement into the locks and keeps every pin the locks already hold;
`make upg` is the only verb that moves a pin. Both verbs end with the frozen
installation.
