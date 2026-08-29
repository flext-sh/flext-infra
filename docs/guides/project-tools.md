# Project tools

<!-- TOC START -->
- [Where each binary comes from](#where-each-binary-comes-from)
- [Declaring a tool](#declaring-a-tool)
- [Declaring ignore patterns](#declaring-ignore-patterns)
- [Landing a declaration](#landing-a-declaration)
<!-- TOC END -->

A project declares the external binaries only it needs — a document renderer,
a database client, a build helper — in its own `config/*.yaml`, under
`ManagedArtifacts.Mise.tools`. The fleet toolchain in `config/codegen.yaml`
never grows a field for a single project's requirement.

## Where each binary comes from

| Layer | Declared by | Produced by | Reached through |
|---|---|---|---|
| Fleet toolchain (python, uv, kubectl, helm, kind, taplo, ast-grep, gitleaks, tokei, kubeconform, qlty, go, beads) | `config/codegen.yaml` `toolchain:` | `make gen` → `.mise.toml`, `mise.lock`, `bin/mise` | direnv activation of the project root |
| Project tools | `<project>/config/*.yaml` `ManagedArtifacts.Mise.tools` | the same `make gen`, composed after the fleet template | the same activation |
| Project development dependencies (linters, type checkers, test runners) | `pyproject.toml`, from `dependency_profiles` | `make setup` → `.venv` | `PATH_add .venv/bin` in the activation |
| Host runtime tools shared by every shell and service | the host tool owner's registry, outside this repository | the host tool owner's generator into the user Mise registry | global Mise shims |

`make setup` stays hermetic: it trusts and installs the project `.mise.toml`
inside a scratch Mise home under `.test-tmp/` and writes nothing outside the
project. Propagating a binary to the host is the host tool owner's job, never
this generator's.

## Declaring a tool

```yaml
# config/managed-artifacts.yaml
ManagedArtifacts:
  Mise:
    tools:
      "github:jgm/pandoc":
        version: "3.11"
        platforms: [linux-x64, linux-arm64, macos-x64, macos-arm64, windows-x64]
```

- `version` is exact. `latest` and ranges are rejected by the lock validator.
- `platforms` is optional. Absent means the tool publishes assets for every
  fleet lock platform. A subset records, in the project that owns the tool, the
  platforms its backend cannot lock; the lock validator then expects exactly
  that subset. An explicit empty list (`platforms: []`) declares a backend with
  no per-platform assets — `npm:`, `pipx:`, `cargo:` — so the lock carries no
  platform entry for it. Names must belong to the fleet `mise_lock_platforms`.
- One selector is declared once across all `config/*.yaml` files; a duplicate
  fails the load.
- A selector that collides with a fleet tool fails; an alternate distribution
  of a protected fleet identity (another owner's `beads`, for example) fails
  with the canonical selector named.

## Declaring ignore patterns

The fleet scaffold renders every `.gitignore`; it cannot know a repository's
local caches or generated runtime state. Those patterns live next to the tools,
under `ManagedArtifacts.Gitignore.patterns`, and are appended in declaration
order as one project-owned section of the generated file:

```yaml
# config/managed-artifacts.yaml
ManagedArtifacts:
  Gitignore:
    patterns:
      - .dmypy/
      - mcp/generated/*
      - "!mcp/generated/.gitkeep"
```

Patterns declared in several `config/*.yaml` files compose without duplicates;
an empty pattern fails the load. The generated file is still a projection:
edit the declaration, never `.gitignore`.

## Landing a declaration

```
make gen WHAT=apply APPLY=Y
make gen WHAT=check
make setup
```

The second `gen` must produce no diff. `mise.lock` now carries the tool, and
`mise -C . which <bin>` resolves inside the activated root. Commit the
declaration together with the regenerated `.mise.toml` and `mise.lock`.
