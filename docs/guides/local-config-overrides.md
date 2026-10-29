# Repository configuration and local overrides

<!-- TOC START -->

- [Mandatory Mypy policy](#mandatory-mypy-policy)
- [Native Ruff Policy](#native-ruff-policy)
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

Private configuration deltas belong in `config/codegen.local.yaml`. Generated
editor settings follow the artifact catalog's tracking policy; portable editor
declarations remain in the repository's own codegen delta.

Workspace composition comes from `.gitmodules`. Documentation URL ownership and
branches derive from native Git origins, declared submodule branches, and the
selected repository's integration contract. There is no provider/member/docs
repository roster to extend when a new member is added.

The shared package contains generic rules. Consumer-specific Sed campaigns and CSV
inputs belong to that consumer's configuration; they are not shipped as library
policy. Dependency resolution preserves real graph edges and never emits a
project exclusion roster to hide incompatible requirements.
Each Mise selector has one owner. A project declaration that duplicates a packaged
selector is an ownership conflict and fails with its source path; generation never
chooses a winner and reports the conflict as a warning.

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

The approved `flext-0029c` cutover replaces runtime supplier selection with native
pyproject sources and locks. Retire `FLEXT_INFRA_EDITABLE_SUPPLIER_ROOT`, additional
supplier settings, persisted selection and synthetic local/standalone/editable
resolver views. Do not recover those mechanisms through a new environment alias,
host-path guess or compatibility reader. The separate `workspace flext-binding`
installation operation and its temporary constraints/pip overlay are also retired;
explicit native sources and locked setup are the single installation route.

The approved root target declares one native uv workspace, derived from `.gitmodules`,
and composes member locks per [ADR-030](../../../docs/architecture/adr/030-member-locks-composition-upg-guard.md)
(member `uv.lock` and `mise.lock` are formed by each member's declarations, the workspace
lock is their composition, and only `make upg` writes locks behind its guard). Root CI
checks out those declared submodules and installs the composed workspace lock noneditable;
member CI installs the member's own committed lock; neither selects a remote-only resolver.
Independent checkouts retain their own native project declarations. Preserve requirement bounds,
extras, groups, markers, portable dependency metadata and authored native source
policy; do not aggregate a second dependency graph or discard native tables during
managed pyproject publication. See uv's official
[dependency sources](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources)
and [workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/) contracts.

Resolve changed native declarations through the explicit upgrade owner, then
install through setup using `uv sync --frozen` into the consumer's owned physical
`.venv`. Attached members share their containing workspace's environment; independent
consumers never borrow a supplier's environment. Native declarations and locked
consistency replace the stronger independent pre-install supplier admission;
post-provision environment/provenance checks and actual authenticated imports remain
distinct runtime concerns. This is the approved target, not implementation or
runtime acceptance. The [execution-context contract](execution-context.md#native-bootstrap-task-route-flext-0029c)
owns the task-only direct-CLI route and final Make integration sequence.

## Generation and recovery

Use canonical `make setup`, `make upg`, and `make gen`. Setup installs existing
locks; upgrade resolves them; generation projects the declared artifacts. Generated
files are changed through their owning renderer and native conform surface.

`Infra.codegen.templates.entries` is one mapping keyed by repository-relative
destination. Each value owns that artifact's applicable profiles, source and
ownership. The same destination key composes through the existing recursive
mapping layers, so a repository changes only its own delta without copying the
catalog. List declarations and duplicated destination fields are invalid.
Every entry declares
`ownership`: `null` seeds an authored file during project creation; an ownership
mapping declares `full` generation or `merge` of owned sections with authored
content. Managed views and native project projections derive from this catalog.
An explicit repository delta can retain a product-owned workflow as an authored
seed with `ownership: null`; its existing Git-managed content is neither rendered
nor retired. Generated GitHub workflows require full ownership and a template
source. The internal tuple of entries derives from this one mapping and is not a
second serialized declaration.
An owner without a template must resolve through its existing specialized
planner. Missing owners, duplicate destinations and invalid paths fail rather
than preserving an unrendered artifact as success. Includes and macros remain
captured template dependencies, not separate output declarations.
Includes resolve relative to the declaring template's directory. A sibling policy
template uses its filename, without repeating the directory in its include path.

Recovery surfaces authorize the same exact dependency cohort that they plan:
`requires_artifacts` expands the selected destination keys for both planning and
publication checks. The `makefile` surface publishes only its currently declared
dependencies, without selecting facade generation or requiring environment activation.
The approved native cutover retires copied Python setup helpers and their dependency
edges; it must not retain a generated admission resource as a cold-start prerequisite.
Undeclared extra destinations and missing required outputs remain publication failures.

New-project generation consumes the destination's own project, integration, kind
and dependency-provenance declarations. Its Git checkout is prepared separately;
generation never initializes a repository, adds a remote or creates a commit.
An unborn symbolic HEAD is represented explicitly as absent commit identity,
while corrupted references still fail. An established repository missing its
project metadata is not a new scaffold. The selected operation owns the coherent
publication of its generated dependencies through the existing shared planner
and publisher; it does not repeat whole-tree lazy planning after publication or
invoke another public verb.

The preferred creation path is a declared new member, with its Git checkout
prepared, consumed by the workspace's `make gen`. A standalone target without a
Makefile uses the internal `codegen init` adapter from an already provisioned
generation tool runtime. After the same detector positively admits its own
declarations and new-tree identity, that adapter selects the existing complete
generation planner and publisher. An existing project retains the bounded
Makefile recovery surface. A project-metadata symlink is an existing input, never
evidence of a new tree.
The cold sequence is `codegen init`, `make upg`, `make setup`, then `make gen`.
The generation tool runtime supplies its own declared native Mise, Python and UV
prerequisites; it is not the destination's product runtime. Upgrade resolves the
generated manifests, setup creates the destination's physical environment from
those locks, and later generation uses that environment. Initialization and
generation never install dependencies, write locks or borrow another checkout's
environment. Beads participation uses the destination's own policy and identity;
the adapter neither invents an identity nor changes those flags.

Private child packages publish their own implementation owners. Their parent
initializer does not widen its authored API by flattening those private exports.
Infrastructure implementation imports therefore name the owning child package;
external projects consume the public facade. Generation resolves class ancestry
against the planned initializer and rejects a consumer of a retired parent export
instead of restoring that export or resolving it through stale installed code.

The source inventory consumes the same native `lazy_export_bindings` reader as
class-base resolution. A lazy route retains its declared provider and exact
attribute; an empty attribute denotes the provider module itself. Inventory
never reconstructs that attribute from the exported name. Ordinary module
bindings remain lexical inventory inputs, and package names such as `tests`
receive no separate lazy-mapping exemption. Unsupported initializer declarations
fail through the canonical reader.

Generation is the sole writer of `.envrc`. Local `make setup` authorizes that
projection with native `direnv allow`; it never renders, replaces, or removes
environment files. `make check` verifies the selected repository's projection
against its current declaration. A fresh clone with a valid committed `.envrc`
needs no local generation journal. A missing or divergent projection fails
without repair; `make gen` owns its regeneration.

The publication owner authenticates each file's captured destination and declared
inputs. A changed dependency rejects its affected file with a causal issue while
independent valid files retain their published gains. Reports preserve original
failures and actual accounting. Publication never rolls back the whole campaign
because an unrelated file changed.

When late byte verification rejects an output, planning retains that output's
original consumption receipt and first exception beside the other candidate
plans. Candidate providers remain observations from the same captured epoch,
not admitted publications: every consuming component must still pass the full
byte, query, absence and native-issuer guards before effects. A partial lazy
failure does not discard independently planned managed files. Tooling
consumption qualifies its actual pyproject output; unrelated templates do not
inherit that receipt. Publication groups follow declared dependencies and
consumed output elections, including separate unchanged components, rather than
one whole-repository group. A projection manifest declares dependencies on the
exact candidate output paths used to derive its entries, so it settles in the
same component as those outputs. The invocation remains failed after those independent
components settle. Structural, issuer and absence failures that prevent planning
still fail closed before effects; this late-byte contract does not certify those
other failure paths or complete runtime acceptance.
The existing planning report retains each outcome's original exception identity,
message and traceback. A later repository failure must remain inspectable even
when an earlier exception owns the process exit; the report does not replace or
reconstruct that first exception.
Execution outcomes and complete generation plans belong to the existing codegen
pipeline model owner, alongside their original consumption receipts. The artifact
configuration owner retains declarations, worker requests and report evidence;
it does not import execution receipts back through a model dependency cycle.

A completed invocation still needs native consumer validation and a repeated
unchanged generation before its fixed point can be accepted.
