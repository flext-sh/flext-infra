# Repository-local topology and conformance

Topology is derived from two independent local facts:

- a repository containing `.gitmodules` is a workspace;
- a repository without `.gitmodules` is standalone.

A project is managed only when its own `pyproject.toml` declares FLEXT. Managed
status neither changes topology nor grants cross-repository execution.

Conformance reads and writes only the selected repository. It does not infer
state from directory names, remotes, providers, parents, sibling checkouts, or
configuration mappings. A malformed local declaration fails before any write.

`.gitmodules` remains repository-owned input. Generation preserves workflows
without `[MANAGED]` provenance and projects only declared managed artifacts.
Tool extensions belong to each consumer's `config/*.yaml` `ManagedArtifacts`
declaration; duplicate selectors and collisions with fleet-owned identities
fail.

Beads support is limited to `.beads/config.yaml`, `.beads/metadata.json`, and
the fleet-owned Mise binary pin. Generation and Make own no Beads runtime,
policy, hooks, commands, database lifecycle, or execution rules.
