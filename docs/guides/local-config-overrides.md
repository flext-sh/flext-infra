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

Diagnostic suspension catalogs are forbidden. The typed policy rejects the retired
`disable-error-code` and `facade-rebind-error-codes` fields. Generated modules and
facade rebindings receive no `ignore_errors` override. All reported native diagnostics
remain blocking. Overrides that broaden analysis, such as `follow_untyped_imports`,
retain their declared behavior.

Generic Mypy options cannot replace `plugins`, `disable_error_code`, `python_version`,
`overrides`, or generated `mypy_path`. Reserved aliases and duplicate declarations
within or between the boolean and string maps fail validation. A string-valued
`enable_error_code` may enable diagnostics without masking any other finding.
Boolean enabling is invalid.
Generic keys must be plain option identifiers, not quoted TOML keys or statements.
Global `ignore_errors = true` is forbidden; an explicit false boolean remains valid.
Dependency profiles in `config/codegen.yaml` restrict Pydantic to major version 2;
dependency locks and project manifests are regenerated through `make upg` and
`make gen`, respectively.

Regenerate consumers through canonical `make gen` after changing the source owner;
never patch generated pyprojects. Validate the public consumer with the plugin active
and a negative diagnostic, then run the applicable native gates. A source
inspection, generation receipt, or merged PR alone is not proof of green delivery.

## Native Ruff Policy

Ruff rule selection and native conventions come from the shared typed tooling owner.
Neither shared policy nor project-local managed artifacts accepts exemption catalogs,
free-form ignores, per-file ignores, or informative-only rule maps. The required
`rule-owners` mapping declares rules enforced by another canonical checking gate.
The existing gate registry rejects self-owned, unknown, missing, non-repairing, or
unelected owners before a projection derives Ruff's native ignore from that mapping.
The owner must participate in the complete default check and the existing repair or
format contract. `missing-trailing-comma` delegates layout to the native `format`
gate; it is not a waived rule. Paired lint/format validation checks the final bytes.
Modernization removes stale exemption tables without narrowing rule selection.
`unfixable` remains a repair-safety policy: it prevents destructive automatic changes,
not detection or a failed verdict. Repair completion requires the same native owner's
read-only verification of the repaired targets.

## Local dependency binding

Canonical setup can opt into an external supplier workspace through the consumer's
untracked `config/codegen.local.yaml`:

```yaml
Infra:
  codegen:
    make:
      uv_resolution:
        editable_supplier_root: /absolute/path/to/workspace
```

Configure the physical runtime root, not an attached member. The existing consumer
environment supplies the authenticated interpreter used for marker selection.
Run `make gen` to project the isolated editable resolution view, then `make upg`
to reconcile its development lock, and `make setup` to replay that lock frozen.
This opt-in never resolves the root or default view locks and does not request
version upgrades. Hosted setup continues selecting the standalone view. The
supplier root is explicit; no home directory or package roster is shared policy.
Only active declared dependencies supplied by that workspace are rebound; supplier
development groups are not added to the consumer environment. The consumer keeps
its own physical environment. Removing the opt-in returns setup to its default view.

The explicit `workspace flext-binding` CLI accepts `--repository-root`, `--flext-root`,
and `--python`. It changes only the provisioned consumer environment; it never edits the
consumer's dependency declarations. Canonical setup restores the declared resolution.
Workspace setup installs its declared local editable sources through `uv sync`; it
does not invoke the external-consumer binding service on itself.
The workspace root owns local path sources and source-replacement overrides. A
transitive Git requirement for the same distribution is replaced by that local
identity, not deleted from the dependency graph. Declared version bounds remain in
constraints, and requested extras remain on the replacement requirement. Member
metadata keeps its portable Git provenance and renders identically when detached.
Conformance removes dependency-edge exclusions; no reverse-edge exclusion catalog
or project-routing declaration is required. See the official UV
[override semantics](https://docs.astral.sh/uv/concepts/resolution/#dependency-overrides)
and [development sources](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources).
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
