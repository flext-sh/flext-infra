# Repository configuration and local overrides

<!-- TOC START -->

- [Mandatory Mypy policy](#mandatory-mypy-policy)
- [Local dependency binding](#local-dependency-binding)
- [Generation and recovery](#generation-and-recovery)

<!-- TOC END -->

Each configuration family has one ordered source contract:

1. Packaged `flext_infra/config/F.yaml` supplies generic library defaults.
2. The selected repository's `config/F.yaml` supplies its committed deltas.
3. Its optional, untracked `config/F.local.yaml` supplies local deltas.

The caller supplies the repository root. Ambient working directories, organization
catalogs, and user-directory overlays do not select consumer configuration.
`load_codegen_inputs(root)` returns the effective typed codegen policy and exact
consulted file snapshots. Consumers receive that resolution explicitly.

Mappings merge recursively, lists concatenate, and later scalars replace earlier
scalars. Unknown fields fail typed validation. Codegen captures current file bytes
on each load and verifies them before publication. Exact successful YAML content
may reuse parsing; cached values are isolated and never replace physical snapshots.
Malformed content retains its original exception.

For example, a consumer may declare its own integration contract:

```yaml
Infra:
  codegen:
    repository:
      integration:
        provider: github
        branch: feature/integration
```

Private local adjustments belong in `config/codegen.local.yaml`. Generated
`.vscode/settings.json` is a runtime-local binding: portable editor declarations
remain in the repository's own codegen delta, while setup projects the interpreter
for its actual workspace or standalone environment.

Workspace composition comes from `.gitmodules`. Documentation URL ownership and
branches derive from native Git origins, declared submodule branches, and the
selected repository's integration contract. There is no provider/member/docs
repository roster to extend when a new member is added.

The shared package contains generic rules. Consumer-specific Sed campaigns and CSV
inputs belong to that consumer's configuration; they are not shipped as library
policy. Dependency resolution preserves real graph edges and never emits a
project exclusion roster to hide incompatible requirements.

## Mandatory Mypy policy

`config/tooling.yaml` owns the declared Mypy policy and both projection paths consume
that same typed configuration. The project's Pydantic 2 contract requires the
`pydantic.mypy` plugin; missing, empty, or v1 resolved plugin declarations fail validation
rather than receiving a silent default.

The operator contract globally suspends only `prop-decorator` and `call-arg`. A complete
policy payload must declare both and cannot add another global suspension. The model
does not supply configuration-owned values through declaration defaults. Empty local
lists retain the tracked policy because the YAML loader concatenates lists. Pyright
call diagnostics and other unsuspended diagnostics remain active.

Generic Mypy options cannot replace `plugins`, `disable_error_code`, `python_version`,
`overrides`, or generated `mypy_path`. Reserved aliases and duplicate declarations
within or between the boolean and string maps fail validation. A string-valued
`enable_error_code` may enable unrelated diagnostics, but cannot re-enable any
suspended code, including within a comma-separated list. Boolean enabling is invalid.
Generic keys must be plain option identifiers, not quoted TOML keys or statements.
Global `ignore_errors = true` is forbidden; an explicit false boolean remains valid.
Dependency profiles in `config/codegen.yaml` restrict Pydantic to major version 2;
dependency locks and project manifests are regenerated through `make upg` and
`make gen`, respectively.

Regenerate consumers through canonical `make gen` after changing the source owner;
never patch generated pyprojects. Validate the public consumer with the plugin active
and an unsuspended negative diagnostic, then run the applicable native gates. A source
inspection, generation receipt, or merged PR alone is not proof of green delivery.

## Local dependency binding

The explicit `workspace flext-binding` CLI accepts `--repository-root`, `--flext-root`,
and `--python`. It changes only the provisioned consumer environment; it never edits the
consumer's dependency declarations. Canonical setup restores the declared resolution.
Workspace setup installs its declared local editable sources through `uv sync`; it
does not invoke the external-consumer binding service on itself.
The interpreter must belong to the consumer's physical environment as determined by the
workspace topology. A symlinked environment or a foreign interpreter is rejected.

Binding evaluates dependency markers with that interpreter's facts and matches
normalized distribution names against the supplier root and its package members. Like
canonical setup, it includes all declared extras and dependency groups. Selected extras,
version bounds, declared constraints, and unrelated source overrides remain effective.
An empty active selection fails. CI rejects binding before accessing the consumer, using
the configured CI variable and value.

The public service's `plan_targets` method also requires the consumer `python` path;
planning must use the same interpreter as installation. Its in-repository callers use
that explicit contract, avoiding host-interpreter marker evaluation.

## Generation and recovery

Use canonical `make setup`, `make upg`, and `make gen`. Setup installs existing
locks; upgrade resolves them; generation projects the declared artifacts. Generated
files are changed through their owning renderer and native conform surface.

The publication owner authenticates each file's captured destination and declared
inputs. A changed dependency rejects its affected file with a causal issue while
independent valid files retain their published gains. Reports preserve original
failures and actual accounting. Publication never rolls back the whole campaign
because an unrelated file changed.

A completed invocation still needs native consumer validation and a repeated
unchanged generation before its fixed point can be accepted.
