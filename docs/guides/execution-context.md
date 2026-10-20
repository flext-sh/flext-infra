# Execution context

<!-- TOC START -->

- [Runtime is the authority](#runtime-is-the-authority)
- [Canonical architecture checkpoints](#canonical-architecture-checkpoints)
- [Namespace migration](#namespace-migration)
- [New projects](#new-projects)
- [Environment activation](#environment-activation)
- [Dependency locks](#dependency-locks)
- [Runtime environment](#runtime-environment)
- [Mise toolchain](#mise-toolchain)
- [SonarCloud exclusions](#sonarcloud-exclusions)
- [Bootstrap credentials](#bootstrap-credentials)
- [Evidence and checkpoints](#evidence-and-checkpoints)
- [Check gate partitions](#check-gate-partitions)
- [Census consumer evidence](#census-consumer-evidence)
- [Bounded Mypy failure status](#bounded-mypy-failure-status)
- [Abstraction-boundary project identity](#abstraction-boundary-project-identity)
- [Service foundation](#service-foundation)
- [Codemod scanner contract](#codemod-scanner-contract)

<!-- TOC END -->

## Runtime is the authority

The existing `refactor rename-plan` CLI action accepts `SemanticRenameSelections`
JSON through `--decisions`. A selection identifies the introducing class,
callable, or module and its intended name. `consumer_roots` is an optional JSON
array of absolute checkout roots for this invocation, not a persistent rename
catalog. The containing workspace and its declared `.gitmodules` members are
discovered automatically, including invocations from one attached member.
External consumers are explicit typed run inputs, not reverse-dependency guesses
or an implicit host-wide inventory. Standalone invocations retain their own scope
plus those declared consumers.

Native Rope `MultiProjectRefactoring.get_all_changes` computes every elected
project's changes before publication. Module selections use the native nullable
offset and produce authenticated create/retire file effects. Planning does not
move or write source files. The artifact retains the original binding epoch,
consumer scope and candidate updates. `refactor rename-preview` and `make mod`
with the existing rename artifact input rederive that candidate and reject
source drift before publishing through the shared semantic transaction. Each
consumer retains its own native source-folder election, so independently owned
`tests` packages do not compete for one module identity. Provider, receivers and
generated exports form one declared dependency group. Projection planning reads
the original authenticated native overlay, including proposed module retirement;
only the fully composed candidate enters the physical runtime. Preparation and
default staged checks consume that same group before its journal publishes. The
existing CLI `mod --rename-plan=<artifact> --apply` composes the artifact with
target-only AST and semantic planning before that group's publication. Ordinary
`mod` accepts repeated `--consumer-roots <absolute-checkout>` options and builds
the same captured read scope without a manual rename catalog. The request root
remains the syntax/declaration target; elected consumers are reference readers
and receive only proven dependency effects. The common coordinate parent is not
a discovery root. Staged native module destinations retain the captured origin
mode, as does publication. A plan
captured before a producer upgrade is not a portable release migration history;
a changed epoch must be reconciled causally, never by guessing an old name.

Package-directory renames are refused by this file-effect boundary. Native
string payloads and framework registration are not implicitly renamed; they
remain subject to the existing consumer validation and declaration owners.

The AST/semantic candidate is not yet an all-phases atomic guarantee: the legacy
text, CSV and independent loop callbacks still expose effectful operations.
Their existing owners need pure planning ports before those effects can join the
same publication group. Source-only changes are not runtime or gate receipts.

Correct runtime behavior defines the contract; tests verify it. Replace mocks, fake
tools, private-function access, and assertions that only check how code was written
with observable inputs and effects through public interfaces, preserving functional
coverage. First reproduce the real public path and identify the executed artifact. Fix
obsolete tests or fixtures after that proof, never by changing the environment to keep
their expectations. A test result alone does not certify setup, generation, or
consumption at the integrated revision.

Before repeating a broad search, confirm branch, HEAD, local changes, PR, and declared
base. Check the runtime with `make status`: the execution path and installed version
must match the code under validation. An earlier log or an installation from a parent
workspace does not certify a standalone checkout. Work on the freshly fetched
integration tip of every repository involved.

## Canonical architecture checkpoints

The public `mod` handler is inherited by the API from
`services/mod.py`; `FlextInfraCodemodBatchApply` remains its sole execution
engine. The CLI validates the request with `m.Infra.ModCommand`, while consumers
use `p.Infra.ModRequest` and supply an explicit `p.Infra.ModProgress` port. The
API's existing preview and workspace capabilities provide the dependencies by
MRO; there is no second loop in the handler.

Rope workspace sessions are owned by their invocation. Independent opens keep
their logical roots and teardown isolated, even when they read one structural
workspace. Borrowed projects remain owned by their caller. Content snapshots
and their authenticated indexes retain their source epoch; a process-global
registry is not a substitute for the existing invocation-scoped DI.

Persisted semantic plans use the Core contract preset's matching byte encoder
and decoder. Re-derivation compares every persisted field, including exact
payload bytes, rather than comparing excluded per-effect runtime dependencies.
Those dependencies are reconstructed from the authenticated aggregate inputs
before publication; they are not duplicated into the serialized artifact.

For every bounded engine, generation or namespace repair, compose the
branch-matched workspace law, router and skills from the
[canonical governance sources](../index.md#governance-pointer). The canonical
Make guide applies those owners to command admission and acceptance; this
context is not a parallel law.

Before planning, use the router's global search-first/YAGNI/SSOT/SOLID/simplify/DRY
route to identify the existing domain owner, declaration namespace, consumer
closure and necessary removal set. Use canonical global DI, Clean Architecture
and Pydantic skills for concrete dependency/data boundaries. Do not create another
helper, cache, detector or registry when the correct domain owner already exists.

Before publication, apply FLEXT law **Architecture and imports** and **Sources,
generation, and commands**: preserve facade MRO `c -> t -> p -> m -> u`, inward
imports, pure declarations and explicit dependency composition. Config/settings
are layer-zero and import no own namespace. Models resolve at their declaring
owner and payloads cross typed Pydantic boundaries once. Repair cycles at the
declaration/dependency owner, not through local-import demotion, fallback,
compatibility exports or suppressions. Generated surfaces change only through
their source and canonical regeneration.

Shared TOML ingress owns Pydantic mapping validation. Pyproject, documentation and
text-rule consumers reuse its validated output directly.

Family-base import enforcement covers both `from` imports and module imports,
including aliases and imports inside `TYPE_CHECKING`. The semantic import owner
still elects the package, family base and sanctioned compose modules; native
matching preserves the family's declared split-parts imports.

Single-class publication excludes the configured test-suite scopes that forbid
suite exports. Importable source classes still declare their publication; the
same native AST command verifies both contracts.

Rule catalogs, fixture staging and snapshot reconciliation consume YAML streams
through `u.Cli.yaml_parse_documents`. Document separators and literal-block
chomping belong to that shared parser; Infra does not split or normalize their
source text before parsing.

Captured library, project and local configuration layers use the strict YAML
source's list-aware merge. Project tool additions retain the base toolchain.
A projected edit replaces its selected values inside one layer before those
layers are composed, so a replacement does not retain the previous declaration.

Layout planning and `.gitignore` publication load the selected consumer's
codegen layers. Its local declarations supply patterns and file modes; a cohort
does not borrow its root's overrides for members. Publication retains those
configuration snapshots alongside the destination snapshot, including for a
no-op. Workspace rendering also receives the local topology so its member
whitelist agrees with conform; the initial `.gitmodules` snapshot authenticates
that input even when absent. Packaged defaults do not enumerate consumers.

`make fix-toolchain` repairs one explicitly selected native installation through
Mise, using the exact version and checksum authority of the current lock. Set
`FLEXT_INFRA_TOOLCHAIN_REPAIR_TOOL` to a tool name already declared by the project.
Missing or undeclared selections fail before installation. The operation
revalidates its captured configuration and lock, streams the native installer
output, then invokes the existing complete toolchain reality proof. Normal
setup, upgrade and generation do not force reinstallation. The CLI inherits the
shared codegen execution modes: `--dry-run` and `--check` run the complete proof
without replacing an installation.

Before accepting a phase, retain evidence of complete consumer rewiring and
superseded-path removal, domain-correct reuse and net-negative simplification
without functional reduction. Global make-check/verification-loop own runtime,
native gates and receipt requirements. A successful publication is not proof of
lint/type/test success or idempotence: run the applicable gates and repeated
gen/fix/fmt on the unchanged candidate, and report failed or unexecuted scopes.

Security gates reuse the gate-base source discovery (`source_scan.roots`) and
native runner. Explicit file targets and generated Python remain auditable;
owner authorization does not grant a Bandit exemption. Gate diagnostics cross
parser and aggregation boundaries through `p.Infra.Issue`; their JSON and SARIF
schemas remain owned by the canonical Pydantic models. Schema metadata delegates
to those models rather than duplicating them or reconstructing validated issues.

Configuration vocabulary belongs to the bootstrap-safe `_constants/config.py`
owner, exposed through `c.Infra`; schema modules validate that vocabulary rather
than redeclaring it. Configurable values still come from the effective config or
settings spec. Conform surface groups share their canonical declarations, and
already validated request enums pass through planning without reconstruction.
Dependency-only APPLY is rejected before target initialization; CHECK remains an
observation of published evidence. YAML rule streams use the shared CLI parser
so document separators never change multiline fixture contents.

Protected-edit snapshots reobserve the native checker on every call. They do not
reuse Python-level receipts keyed only by source bytes and gate names: those keys
cannot authenticate effective configuration, tool runtime or imported dependencies.
Native checker caches remain owned by their existing runtime/cache owners. Native
execution and malformed-report failures stay separate from diagnostic occurrences;
neither a repeated failure nor an unchanged finding count proves validation success.

Facade projection composes constants, utilities and models from the exports and
base order declared in their configured private family. Protocol projection keeps
its consumer-based ownership resolution. The utility path delegates directly to
the declaration planner. Static and runtime consumer checks retain their own
import-failure verdicts.
Generated protocol and model namespace assignments are derived output, not new
contract declarations. When an assignment resolves to an exact inherited class,
projection removes that binding and inherits the canonical private owners in C3
order, including their declared overrides. A stale renamed alias cannot publish
itself or shadow a different inherited contract. The generated ownership marker
and native class identity are both required; unrelated namespace members remain
unchanged, and contradictory authored class bindings still fail before publication.
Generated Python imports use their absolute native package owner. The planner
selects exports once; rendering groups those declarations without another
name-based exclusion policy. Compact lazy-loader targets remain loader data.
Runtime-base discovery treats supplied planned bytes as authoritative, including
unpublished packages. Original-file reads and package membership checks retain
their native project-tree scope; planned initializer bytes own alias analysis.
Generated Ruff bases retain the qualified import spelling used by the consumer.
The provider's declaration identity remains separate from that reexport spelling.
Rendering a facade returns source only. Package-form imports require publishing
the owning family's initializer through the existing lazy-init planner before a
fresh consumer loads the generated facade.

## Namespace migration

Namespace planning, source iteration and analyzer configuration consume the shared
project discovery owner. Declared scan roots seed discovery; they do not hide active
Python in other owned directories or at the repository root. Foreign repositories,
declared nonparticipants, generated payloads and installed environments retain their
own boundaries. Vendored source is not an installed-environment exclusion.

Class nesting derives one owner from the module's declarations and conventions. It
preserves native symbol identity when moving functions, values and type aliases and
rewires executable and deferred type references without rewriting ordinary string
payloads. Initializers retain their separate export-generation contract. An unresolved
definition-time dependency or framework registration contract fails planning; it is
not a successful exemption from namespace ownership.

Shared pytest fixture modules and enforcement expose class objects through the native
plugin manager. Fixture imports remain deferred until configuration, and the manager
owns registration identity and idempotence. Module-name loading does not discover a
nested plugin automatically: consumers load the installed entry-point declaration.
Registering an auxiliary class is not equivalent to a directory-scoped conftest.

Rule definitions and their generated baselines ship in the same producer artifact.
Refresh them with `make mod-snapshots`; a source-checkout receipt does not validate a
wheel that still contains older baselines. After adopting a new plugin declaration,
reconcile installed metadata through `make setup` before running its consumer tests.
`make test-file` runs incremental and complete selection for the requested file using
the same native testmon owner, without the ordinary incremental invocation deadline.

## New projects

`make project-new` delegates to the same typed `codegen new` service exposed by
the public Infra facade. It consumes explicit `NAME`, `KIND`, `OUTPUT_ROOT`,
`PROVIDER`, `REPOSITORY_URL`, `REPOSITORY_BRANCH`, `FLEXT_REPOSITORY_URL`,
`FLEXT_REPOSITORY_REF`, `LICENSE`, `AUTHOR_NAME`, `AUTHOR_EMAIL`, `UPSTREAM`,
`FLEXT_SOURCE`, and `YEAR` inputs. These are identity declarations for a repository
that does not exist yet; missing or invalid values fail the service's validation.
Make transports their literal values through the environment, preserving spaces
without evaluating the values as shell code.

The generated project owns its declaration, Makefile, CI workflows, package,
examples, and tests. Provision and validate it through its own `make setup`,
`make gen`, `make check`, `make test`, and `make build`. Its physical environment
belongs to the generated repository.

## Environment activation

The `make setup` contract includes approving the `.envrc` with `direnv allow`.
Make verbs declare their activation requirement in `make.verbs`; activation is
required by default before handlers and hooks. Generation and its footprint
inspection consume the declared physical interpreter and verify its environment
directly, so they can repair generated activation inputs. The `gen` handler
delegates to the existing `codegen generate` projection owner, including its
guarded `.envrc` publication. A declared `_custom-gen` replaces that handler.
Each invocation runs its pre hook, handler and post hook once, and a failure
prevents later effects. Initial provisioning remains the responsibility of
`make setup`. Public Make commands own the activation boundary and can be
invoked directly.

Library defaults resolve through the concrete config class's import-package resource,
not its declaration file's depth or the checkout's `config/` directory. Editable and
wheel consumers use the same namespace owner; a missing declared packaged file fails
without borrowing repository or sibling defaults. Target and local overlays remain
explicit repository inputs, separate from the frozen library singleton.

The single-layer schema loader follows that same concrete-package resource contract
through stdlib resource discovery. Parent-depth guesses, worktree paths and fallback
searches are not default owners. Missing required defaults retain their native failure.
Installed-wheel acceptance must identify and exercise the actual distributed artifact;
an editable source read or a prior editable pass cannot retroactively prove wheel
resources, template identity or consumer behavior.

Editable Hatch declarations retain explicit package directories and package remappings
from `tool.hatch.build.targets.wheel.sources`. Every installed `.pth` entry must expose
a declared package at its physical source, and every declared package must be covered.
A distribution containing the application package and an infrastructure namespace does
not lose either declaration merely because it uses `include` and `sources` instead of
`packages`.

Infra owns the full workspace operation receipt and report. CLI's native qualification
receipt and report are non-generic read projections of that original payload; they are
not base classes for domain fields. Original execution, outcome, stage and completion
remain observable when CLI reads the shared native-tool evidence.

Upgrade installs the newly resolved lock through its existing frozen provisioning
owner and verifies its runtime provenance before the next producer. Package election
resolves the current physical import path independently of loaded-module caches;
a retired wheel origin does not
prove the source tree that a new producer will execute. Native provisioning failure
stops that producer without rewriting the resolved lock or undoing published files.

Conformance captures producer identity before request prelude, planning, staging,
or journal effects. Cold package election and loaded function/class provenance must
agree. The retained native file states and physical tree manifests include provider
code, package resources, distribution metadata, editable pointer files, and project
metadata read during ownership election. Distribution names and namespace names are
separate identities; ambiguous ownership is a failure. Lexical entrypoints retain
the physical executable sources they consume and the metadata proving their elected
providers. Explicit module inventories and declared resource trees retain their
membership checks; unrelated files do not become lexical producer inputs.

The captured cold module election is retained with the same native manifests in
phase inputs, journal transitions, and publication receipts. Revalidation uses the
same registered-provider selector and compares the complete election, not only
facade ancestors. Newly imported providers and changed physical bindings require
fresh pre-planning authentication. Distinct metadata directory identities remain
distinct even when their declared distribution names match. A Git-locked rendering
engine is checked by the typed environment provenance owner against both URL and
commit; absent PEP 610 provenance never becomes a version-only success.
Registered distribution metadata and physical provider ownership remain the producer
selection authority. Loaded declaration authentication has no separate first-party
package inventory: elected third-party providers retain the same source, descriptor,
and executed-code requirements. Namespace spelling or a `site-packages` path never
authorizes omitting a declaration or accepting an otherwise unproven factory.
Selecting writable editable members authenticates the installed PEP 610 receipt,
editable pointer inventory, and declared Git checkout association. This election
does not import member code or certify its execution. The normal environment
verification separately authenticates the loaded code; producer capture also
retains its own code and resource proof before generation.
Loaded-code checks bind physical declarations, function code, executable wrapper
links, property accessors, and MRO suppliers. They do not require operational class
variables, initialized settings singletons, or config data to equal class-body literals;
the actual consumer captures typed config and resource inputs separately.

Class cache writes require an unchanged classmethod receiver or an exact global class
receiver whose native method writes the declared field. Receiver rebinding prevents
that classification. The writer's executable code remains part of the proof, and
changes to ordinary constants remain violations. Supplier functions are identified
and ordered only after native receiver and field writes prove their relevance;
unrelated generated functions do not participate in class-state writer capture.
Declared staging-path mappings apply
to wrapper storage and nested code units as well as direct function evidence; a
filename change outside those mappings remains observable.

Producer authentication starts with a passive observation of the original process.
Source preflight elects providers and pins their physical source, resource, metadata
and runtime inputs. It accepts source-backed generated functions without interpreting
their factory grammar or replaying imports, decorators, class bodies or callbacks in
that process. An authored-code mismatch proved directly from pinned source can fail
before the child import.

Provider election includes the installed runtime dependency closure of the
observer SDK and the selected producers. Active installed requirements determine
that closure. Native distribution metadata supplies import names; editable
providers retain their PEP 610 and project-declaration proof. The same physical
ownership and source checks apply to these providers before the isolated import
loads their package initializers.

Full authentication imports the elected sources in an isolated native interpreter.
The child records the physical source receipts used by that import and passively
observes the resulting code and bindings. The owner verifies the executed receipts,
compares the original and cold observations, and rechecks source and runtime inputs
before returning the authenticated reference. This proof creates no source preview
or publication journal. The child retains the real effects of its import; the
original process retains its pre-observation state.

Generated functions use that real import as their independent construction proof.
Comparison retains code, source positions, globals, builtins, annotations, defaults,
closure values, descriptors and dataclass or attrs metadata. Dynamic factory inputs
remain valid when the authenticated import produces the same native behavior and
bindings. A generated filename, advertised module name, serialized model or cached
field table alone supplies no authority.

Bootstrap pins capture resident standard-library files whose physical origin
agrees with their native loader. That file election supplies bytes for the atomic
reader bootstrap; it does not nominate a module as an executable producer.
Producer observation still requires the native module registration and the
complete independent import comparison to authenticate executable bindings.

The original reference remains an immutable expectation throughout the operation.
Its in-process birth is recorded only after full authentication. JSON round-trips,
model validation and copied references preserve a data shape; they do not establish
that birth or grant publication authority. Every effect reobserves the loaded code,
physical inputs, module election and declared tree membership. Authenticated receipts
from the operation's actual earlier publications account for its own source changes.
These barriers compare the running original epoch with its original expectation;
they do not cold-import already updated generator files as a replacement epoch.
Candidate publication still owns its staged source view, journal and real consumer
checks.

Read-only conformance authenticates its current checker before acquiring the
publication lease. That checker compares historical receipt data with current
physical states and passive native observations. Historical references and outcomes
retain their role as expectations; checking them does not establish an in-process
birth. Write admission requires the exact original outcomes from actual earlier
publications and reobserves their producer epochs and effects. Operation completion
uses those original receipts without cold-importing the updated generator again.

Source-declared descriptor aliases authenticate the receiver's physical lexical
declaration and the exact imported supplier binding. Relative imports resolve from
the declaring module's package; class attributes are read as raw descriptors through
the native MRO without invoking descriptor callbacks. The receiver alias must retain
that descriptor identity, and the actual supplier declaration and executed function
must match physical source. Replacing either side, its source, or its code fails;
membership of the supplier in the receiver's MRO does not waive alias authentication.
An alias assigned after a method declaration in the same class resolves from
that class's physical namespace before the module namespace. An assignment
before that declaration retains its source-bound module reference. A later
class-local name never changes an earlier binding. An absent binding remains a
failure; authentication never manufactures an operand from a path or a missing
name.
Native class attribute access preserves method/property identity, exposes a
staticmethod's exact function, and binds a classmethod to the exact accessed class.
Alias checks verify those source-declared forms against raw receiver storage without
calling descriptor hooks. Bound methods enter the same supplier/source/code checks;
matching functions with a different bound class are not equivalent. An alias mismatch
retains its failure and reports bounded receiver/module/attribute, source identifier,
supplier owner, and raw binding-kind metadata, never operand representations.
Class and static method wrappers retain their kind and route their underlying target
through the same class or function admission. Callable operands retain constructor
state and dictionary insertion order. CPython operator intrinsics use their exact
native reduction descriptors after supplier, importer and partial-constructor
authentication; GC references alone cannot prove hidden C scalar state. Python
callable instances require a source-authenticated effective call implementation and
native storage observation. Unsupported native state, including an unproved bound
builtin receiver, fails admission before authored callbacks run.
An unresolved factory binding reports bounded, escaped identifier, module/package
registration, receiver/declaration, physical source path, and supplier-kind context.
Diagnostics never render the operand, its material values, or a source excerpt; they
preserve the failed admission rather than authorizing an unknown factory.
Module-level source aliases may follow one unambiguous runtime declaration through
an imported name or raw provider attribute. A typing-only shadow is excluded only
when its guard is an authenticated import of native `typing.TYPE_CHECKING` (including
import aliases, module-qualified access, and native boolean negation). The runtime
flag must match its freshly read physical declaration. Unknown conditions, competing
active declarations, alias cycles, or replaced runtime/supplier bindings fail without
executing either branch, decorators, or class bodies. The selected metaclass retains
the same physical supplier/source/code authentication as an unconditional import.
Native observations preserve the class's actual bases and declared descriptors.
Inherited and explicitly declared constructors remain distinct. Full authentication
compares these identities with the isolated import while passive capture preserves
the original class body, decorator, metaclass and construction-hook effects.
Defaults, annotation operands and dataclass ancestry retain their native storage and
supplier identities. Value comparison uses native storage without invoking authored
equality, hashing, formatting or attribute access. Module hooks do not supply absent
members. Native regex receivers retain the pattern, flags and actual callable
topology in both observations.
Source bindings retain null literals inside a typed value; a null annotation or
default never becomes a successful null `FlextResult` payload or a substituted type.
Generated methods retain the native filenames and source positions produced by the
real import, including batch positions and closure bindings. Authored functions
retain exact native source positions.

Every phase binds that same captured context to its staged consumer inputs. Journal
transitions preserve it instead of rediscovering loaded origins after publication.
Derived interpreter bytecode is not a source input. Changed consumed bytes, retired
provider roots, changed import election, and membership changes in declared trees
invalidate admission. Exact journal output or staging receipts authorize candidate
membership changes. Independent file work outside a lexical producer's consumed
inputs does not invalidate its proof. Publication still authenticates each
participant's relevant inputs and effects. None of this proves an earlier process
whose source context was not captured.

Documentation targets and the executing producer can have different roots.
Programmatic preparation receives the original authenticated producer explicitly
when the target does not own the executing environment. Both single-bundle and
per-scope preparation verify the actual entrypoints and current producer before
consuming inputs; a target directory never supplies an implicit borrowed runtime.

Native callback identity follows the elected supplier's actual registrations.
Conditional attribute references record native absence as binding evidence;
the cold comparison detects later appearance instead of rejecting an untaken
platform-specific branch. Explicitly selected entrypoints must still exist.
An extension can export a callback at module level while its qualified name
describes a class. Observation checks those native namespaces by object identity;
the qualified name alone does not establish or invalidate registration.
Bound interpreter methods are checked against the registered receiver type and
its native descriptor, and their evidence retains the receiver value.
Instance storage follows effective MRO ownership. The observation distinguishes
an uninitialized native slot from a slot shadowed by a derived declaration;
neither state supplies a fabricated field value or executes the derived accessor.
Optional native reads require the standard attribute reader and no custom missing
attribute hook.
Native callable observations retain both interpreter-exposed descriptor and slot
values and their native argument referents. Neither storage form replaces the
other, so changed callable arguments remain detectable.
Native type-family selection uses identity comparisons and remains passive for
metaclasses with hashing or equality hooks.
Operand observations share one recursive encoder, parameterized by construction
mode, and retain structured JSON values until the transport boundary.
Recursive JSON strings are prohibited: re-encoding their escapes amplifies memory
with nesting depth. Compiler locations compare as a flat structure containing
the root and every nested code unit's position in `co_consts`, without JSON
conversion or repeated root checks. Full operand evidence remains required.
Code observations carry one Pydantic-validated JSON payload with the filename,
unit identity, flat locations and complete native compiler witness bytes.
CPython marshal format 2 encodes the witness without reference or string-interning
flags; Pydantic owns its base64 transport. Witnesses are compared without code
deserialization, hashes or inferred locals layouts. This compiler identity is
stricter than `CodeType.__eq__`: it also retains stack size and locals kinds.
Exact native constants are elected before relocation and encoding. NaN, mutable
constants and buffers retain explicit nonportable markers and cannot compare
equal, even to another rejected observation. Unknown constant types fail before
authored iteration, hashing or buffer conversion. Physical source receipts and
authenticated cold import remain necessary to establish the witness's birth.
Import dependency discovery uses the shared import maps; class-lineage validation remains
with the queries that request class information. Namespace packages contribute
their physical portions to source authority without requiring an executable
initializer.

When the checkout owns the distributed configuration file, its project declaration
uses the derived `<stem>.project.yaml` file beside that default. The local layer
remains `<stem>.local.yaml`. This keeps project editor declarations separate from
the library defaults while preserving the same ordered configuration layers.

VS Code's `.vscode/settings.json` is a versioned projection of those declarations,
regenerated by `make gen`. `make gen-editor` publishes the editor settings,
`[tool.pyright]` configuration and Git ignores through the same guarded file
publisher, without generating Python facades or resolving dependencies.
Its `${workspaceFolder}` environment tokens remain
unchanged in workspace members, independent checkouts and linked worktrees.
Opening the workspace selects its environment; opening an independent project
selects that project's environment. Setup does not rewrite or untrack editor files.
The workspace uses one analyzer program and its opened interpreter. Its generated
`[tool.pyright]` includes every declared member's Python roots and assigns specific
execution environments to each member's source, tests and other consumer trees.
Member-local import paths disambiguate packages such as `tests` and `examples`;
their roots are never added to global import paths. A final environment per member
owns top-level modules such as `conftest.py`. Independent checkouts retain their
own equivalent analyzer configuration. Nested virtual workspaces and separate
per-project interpreters are disabled: creating an analyzer for every manifest
duplicates dependency programs and exhausts memory in a large editable workspace.
Diagnostic severity and strict checking remain owned by `[tool.pyright]`.

Editor diagnostics use `Pylance + Pyright` with `pyrightVersion: fromEnvironment`.
The selected environment's Pyright distribution elects the diagnostic engine
version. Acceptance verifies the launched version, inferred types, definitions
and published diagnostics through the running editor; a serialized setting is
not runtime evidence. Indexing covers all owned source files, while dependency
sources remain available for import typing without becoming workspace symbols.
The artifact catalog produces file patterns for file artifacts and recursive
patterns for directories across editor watchers and analyzer exclusions. Git's
native ignore semantics govern Explorer and search, including negations.

Native tool options and editor overrides use ordered `settings` pairs in YAML.
For example, `- [python.analysis.indexing, true]` declares an editor option;
values may contain any JSON-compatible scalar, array or object. Adding an option
does not add a Python model field. Later configuration layers replace the complete
value of an earlier pair, including arrays. `map_union_settings` explicitly merges
editor objects; `stripped_keys` explicitly removes inherited or retired settings.
Generated object keys are sorted recursively, while arrays retain their declared
order. In particular, specific Pyright execution environments precede broad roots;
alphabetically sorting that array changes import resolution and is prohibited.
`Infra.tooling.settings` groups native pairs by table path, such as `ruff.format`,
`pytest.ini_options` or `coverage.run`. One elected document drives modernization,
templates and runtime consumers. The full pyproject template consumes its native
TOML serialization rather than reconstructing tool options through model fields.
Markdown rules use the same pair contract in their Markdown owner.
Native JSON values preserve whitespace and nulls during validation. Unsupported
target values, such as TOML nulls, fail at serialization. Option names must satisfy
their declared grammar without trimming invalid input.
Single-option readers validate the elected value directly. Mutable tables are
detached when handed to projection consumers, keeping the canonical document
unchanged without copying every table for each option lookup.
Serialization builds its owned TOML document directly and uses native key sorting,
preserving source tables and array order without a JSON serialization round trip.

Models retain execution budgets, topology and justified rule policy. Derived
options belong to those owners; native pairs cannot shadow protected policy keys.
Python versions come from `Infra.codegen.toolchain.python_version`, translated
to each tool's native spelling. Project layers declare only their differences.
Publication retains the original configuration snapshots, including absent local
layers, and rejects a changed source before publishing its projections.

Upgrade projects the declared Python requirements before resolving dependency
locks. This keeps workspace members on one declared source identity when a Git
dependency changes; installing from conflicting stale projections is a failure.
`make initialize` publishes the canonical Make bootstrap when the checked-in
dispatcher predates that lifecycle.

The `flext_core.lazy` loader imports its implementation from root-level source
modules, never through a generated child initializer. This keeps generation's
own loader available before child projections are repaired. Recovery uses the
same guarded `make gen` transaction and its post-generation runtime provenance
check; it does not disable the environment guard or replace the generator.

Activation loads the native `mise env --shell bash` output, which puts the
installed tool directories ahead of the host's shared shims. This includes the
self-managed Mise executable: a shim named `mise` otherwise invokes the host
release instead of the project release. Activation does not install tools or
write locks. The `.envrc` watches `.mise.toml` and `mise.lock` to reload after
`make upg`. Audit reports a missing pin; only `make upg` may resolve and write it.
A runtime that is not yet installed requires `make setup`, whose provisioning
happens before activation.
Both setup and upgrade resolve the executable through `mise which python` at the
shared environment-sync boundary and pass that exact path to uv. Recursive Make
calls do not require a caller-provided `SETUP_PYTHON` environment variable.
Make provisioning and the shared workspace reader restrict global and system
configuration discovery to the elected runtime's `.mise` directory; unrelated
host tool declarations never belong to project provisioning. Direnv activation
also exposes operator-owned host tools, without installing or resolving them.

Setup provisions the available frozen toolchain without writing `mise.lock`;
audit owns its pin and completeness verdicts. `make upg` resolves the declared
manifest, provisions the recorded release from its verified asset and requalifies
Mise before continuing. `mise-config` conformance repairs the generated tool
declaration without resolving a lock or regenerating unrelated project files.

When Beads tracking is configured, the generated `.envrc.local` carries its environment:
`AGENTS_GAS_CITY_ROOT` selects the Gas City root, the Gas City runtime publication
provides the port, and the rig metadata provides its database in `server` mode. The
`.envrc` loads that file last. The environment source declared in
`BeadsWorkspaceEnvironmentSpec.environment_sources` provides the city identity; the
template fixes neither its location nor a port. JSON reads must succeed before any
variable is exported. If generation drops the server selection, fix the model or
template and regenerate; never initialize an embedded database or write host and port
by hand.

## Dependency locks

Installed interpreter and distribution fingerprints belong to workspace
environment provenance. Gate receipts and testmon consume that same identity;
reading a gate identity does not load the pytest execution or collection owners.
The producer declares the Markdown collection plugin as a runtime dependency
because its shipped pytest collection implementation imports that plugin.

An associated project inherits the locks and physical environment of its
authenticated Git or native UV workspace. Its `make setup` and `make upg`
delegate full toolchain provisioning and dependency resolution to that root.
A standalone checkout owns those
operations itself. Only `upg` resolves moving Git branches; `setup` installs the
exact committed lock without changing it.

`help` and `.envrc` only observe association and never install its reader.
Before native association is known, public `setup` and `upg` may provision
exclusively the UV reader from the existing lock of the authenticated containing
Git scope. This uses the same Mise release qualifier, checksum verification and
staging cleanup as full bootstrap. It neither resolves nor upgrades an ancestral
lock. Native UV then elects the runtime owner before normal delegation proceeds.
The hosted-provider branch selects standalone execution before this reader
provisioning or ancestor discovery.

Every repository runs independently in remote CI, including a superproject.
Remote checkout never initializes members. The CI gate token does not change
physical Git attachment or local hook environment ownership.
`Infra.codegen.make.uv_resolution` declares the local and standalone native UV
project directories relative to the physical runtime owner. Its hosted runner
variable selects the standalone view; the gate partition never selects a view
or a different environment. Both views use the runtime owner's physical `.venv`.
`FlextInfraWorkspaceDetector.resolution_context` exposes that single election to
bootstrap consumers without loading member metadata, and the public project
context carries the same typed runtime context.
The existing native editable policy remains unchanged: local workspace source
entries retain each member's declared `path` and `editable` values; CI installs
with `--no-editable`. There is no second installer or post-install editable
overlay. Shared lock ownership does not change those source declarations.

The project's authored dependency categories retain their identity. Native
resolver views derive from those declarations without promoting dev or examples
requirements to runtime dependencies. Sources, overrides and Make routing come
from the generator and are never repaired in their projections.
In particular, Infra consumes Tests through its development requirements; Core
consumes Infra and Tests through development and example requirements. These
reciprocal development requirements remain resolver inputs and do not create
runtime dependency cycles. Tests' runtime use of Infra keeps its declared
category.

Fleet execution consumes the canonical runtime dependency waves, with names
ordered within each wave. It invokes each selected member's public Makefile
serially from the workspace root and stops at the first failure. Development
and example dependencies remain resolver inputs rather than runtime ordering
edges. Required member metadata and Makefiles are checked before any member
executes; reports distinguish the declared scope from attempted commands.

Configuration declares `latest`. `make upg` is the only verb that resolves newer
releases and writes the committed `uv.lock` and `mise.lock`. `make setup` installs
from committed locks; `make gen` and `make fmt` neither install nor upgrade tools.
Conformance, member propagation and release version stamping preserve existing
locks and do not create missing ones. External consumer propagation runs its
declared generation and repair verbs; dependency resolution requires a separate,
explicit `make upg` at the selected workspace or standalone owner.
Git dependencies follow their declared integration branches, and `APPLY` stays removed.

The toolchain elects the native `github:direnv/direnv` backend for Direnv's
official release assets. This keeps platform selection with Mise and the
publisher rather than an intermediate Aqua descriptor that omits the Windows
executable suffix. The `latest` selector, release cooldown and platform matrix
remain declared by the same toolchain owner. Qualify changes through native
generation, `make upg` and the locked-install checks.

One `make upg` run provisions the frozen producer before corrective pyproject
projection, without requiring final runtime admission. The elected runtime
owner resolves both native views; attached members delegate that operation
to their workspace. After projecting the declared pyprojects, Mise configurations
and Makefiles, the same upgrade owner resolves each writable FLEXT member's tool
lock and both UV view locks serially. Each member's own Makefile supplies its
configured view paths while the workspace supplies the UV binary and Python
runtime. Final convergence reconciles those locks without advancing dependency
references again. Only the elected workspace runtime receives an installation;
member runtimes are not provisioned separately.
Editable-supplier upgrades use that same member-lock stage without bumping or
provisioning the root supplier's tools. Preserving the shared runtime's pins does
not exempt a writable member's standalone lock from its declared tool manifest.
It runs generation's producer half, relocks the projected manifests, reinstalls
and verifies the resulting runtime before generation's activation half. A
requirement or Mise self-management release that only the upgraded generator
declares therefore reaches the lock and environment in the same run. The declared
lock platforms and release cooldown come from the typed toolchain; never edit
native lock payloads or substitute manual installation commands.

`codegen.scaffold.project.retired_dev` declares development distributions that
must no longer reach managed `dev` or `codegen` groups. Conformance filters them
from existing groups and member contributions;
declaring the same distribution as a required development floor fails. Retire
obsolete typing stubs here when their runtime SDK supplies inline typing, then
regenerate and run `make upg` to reconcile locks and the installed environment.
Member contributions include the requirements parsed from captured declarations;
the composed development group uses the same retirement filter.
Do not uninstall packages manually or weaken the type checker.

`make typings` discovers missing third-party typing information independently of
Mypy's normal untyped-import traversal policy. Published stub requirements enter
the development group through UV. For unmapped modules, the generator uses the
installed implementation and native Pyright to publish an owned PEP 561 package.
The generation directory and distribution prefix come from the dependency limits
policy. Generated packages record implementation provenance and a content-derived
version, and expose an entry point so subsequent runs refresh them.

The detector declares these requirements without resolving or installing them.
Make then regenerates the owning runtime manifest, reconciles native locks,
installs the environment and verifies its provenance. Dependency findings remain
failures throughout this sequence. Reports pass as validated models between
stages and serialize directly through Pydantic.

PEP 621 optional extras and PEP 735 dependency groups retain their separate
categories, including when both declare a name such as `dev` or `codegen`.
Conformance preserves each extra's requirement strings, bounds, markers and
origins; a matching group name does not authorize moving or deleting the extra.

Member contributions carry per-occurrence provenance in both managed development
groups. CUSTOM entries retain their full constraints and origins; removing a
member removes only its generated contributions. The public conform and overlay
paths use canonical resolver-key ordering and preserve these ownership comments
so repeated generation reaches a byte-identical fixed point.

Each internal `flext-*` requirement declares its integration line in `pyproject.toml`,
never a commit: the resolved commit exists only in `uv.lock`, and only `make upg` moves
it to the line tip. The manifest does not pin revisions. A commit left in the
`pyproject.toml` projection is residue: `make gen` re-renders it on the detected line.
When the projection carries no line, a hand-written `project.flext_source` in the
manifest declares it, and a commit in a hand-written source fails. Fix the setup or
`upg` owner and regenerate through `make gen`; manual installs do not replace the cycle.

A workspace root preserves declared Git requirements and binds its package members
through `[tool.uv.sources]` entries containing their declared local `path` and
`editable` values. No repository declares a native `[tool.uv.workspace]`: each
repository owns its lock independently. Publishable members retain the same inline
Git provenance whether attached or standalone; only the containing root owns the
local source overlay and the shared runtime environment. Regenerate that root with
`make gen` and reconcile its lock with `make upg` when the local binding changes.
Every package checkout also overrides transitive requirements for its own
distribution with its local project identity. A dependency that refers back to
the checkout through Git must resolve to that checkout rather than introduce a
second source for the same distribution. Generation derives this identity from
the repository declaration in both workspace and standalone contexts.

A package preserves its declared Git requirements and authored native UV policy.
Generation places local package bindings in the configured resolution views.
Each view has a distinct non-package identity; the real root's runtime requirements
come from its package, while development groups, included groups, extras and
markers remain represented from their declarations. Workspace package selection
has its own binding group and does not turn those packages into runtime dependencies
of the actual root.

This distinction is required when a development dependency refers back to the
root package. Replacing UV's synthetic root requirement with a global self
override loses that requirement's groups and extras. The non-package resolution
owner binds the actual root and its Git backedges without replacing a synthetic
requirement for that root's group selection. For example, Infra's development
dependency on Tests remains development-only even though Tests consumes Infra at
runtime. Core's development and example dependencies remain in their declared
categories as well.

Both manifests are generated transactionally; their native locks are written
only by `make upg`. The standalone view resolves Git dependencies without
materialized workspace members. The local view binds declared package members
with their existing editable policy. Authored native workspace declarations and
custom sources are preserved rather than erased by a generic FLEXT rewrite.
Regenerate the owner with `make gen` and update its locks with `make upg` when
the declared composition changes.

Resolver-wide source election is explicit policy in
`Infra.codegen.toolchain.uv_override_dependencies`, not inferred from an installed
SDK or a direct requirement. The strict library, project and local config layers
append their declarations in that order. Rendering elects the last global override
for each normalized distribution and marker, preserving other marker variants and
native scoped tables. An editable supplier cannot replace the resolution root's
global policy for a distribution. The same elected policy reaches package metadata
and every native resolution view; no repository-specific resolver branch is needed.
Unconfigured conflicting direct and transitive sources remain native UV failures.

Runtime requirements are calculated from the target's import use through the native
dependency analysis. Generation consumes the target's authenticated PEP 621
projection; neither a project-name catalog nor an upstream dependency profile may
inject runtime requirements. The typed `required_flext_dev` policy adds the shared
development suppliers only to `internal_flext` targets and excludes their own
distribution. Dependency-floor updates rewrite only the selected target's PEP 621
requirements and dependency groups, retaining markers, extras, direct sources and
comments. They never write the installed generator's configuration or another
checkout's declarations.

Deptry checking and dependency detection consume one capture owner. It records the
exact settings, native process outcome, fresh report and one physical production
tree per scanned root. Every directory the settings' wheel target ships, through
its `only-include` entries and `sources` prefixes, contributes one root: a source
remapped to its own trailing name (`"src/<pkg>" = "<pkg>"`) roots at `src`, and a
namespace or relocated data directory roots at itself. A target declaring neither
keeps `src`. A changed tree, reused report, missing tool or contradictory exit
status fails.
The import extractor's own coverage receipt must report a positive, unambiguous
executed file count over all roots. Empty source trees and exclusions that prevent
all execution therefore remain failures even when the native findings array is
empty.
Repairs receive the elected interpreter's import suppliers and its native lock
through typed injection. Missing or ambiguous suppliers remain native findings;
installed package names never establish applicability. Metadata election uses the
distribution's native installation location; vendored `.dist-info` payloads do not
compete with its own metadata identity. The existing requirement strings retain
their markers, extras and sources when promoted from development.
The target's explicit contract also identifies development-only suppliers. Their
metadata remains in the index and their native findings stay visible; an illegal
production import requires a consumer rewire instead of a runtime declaration.

Deptry's generated optional-group setting uses `optional_dependencies_dev_groups`;
the deprecated key is removed by the declaration phase in the same projection.
The fixer holds the repository mutation lease, revalidates every metadata, source,
lock and report input, publishes only `project.dependencies` through the guarded
TOML owner, then scans again. A residual `FINDINGS` repair receipt describes the
operation; the subsequent check remains red and provides no green acceptance.
`make initialize KIND=internal_flext` supplies a declaration value to the native
`codegen init` owner for that Makefile's target only. The owner plans the target's
`config/codegen.yaml` through the existing guarded declaration transaction before
rendering its Makefile. It rejects a conflicting existing kind and never broadcasts
the root's value to members. Each member receives a separate explicit request from
the invoking root. Omitting `KIND` consumes the target's own declaration; it never
authorizes classification by project name or installed dependencies.
Setup and audit verify the environment's installed PEP 610 and RECORD-owned editable
paths against that same topology; a frozen Git artifact is not a live local source.

Operational Make prerequisites also verify that provenance before dispatch. An
executable interpreter alone does not establish a valid development runtime.
Submodule provisioning reads the selected checkout's actual `.gitmodules` in both
workspace and standalone modes. A generated member projection cannot omit a newly
declared checkout. An absent management flag inherits participation; explicit values
are parsed by Git's native boolean GET operation. A malformed value fails before
provisioning and preserves Git's diagnostic; it never becomes an exclusion.
Run runtime actions through the root Make dispatcher. Its recipes use the
setup-owned interpreter without selecting a member's lock for synchronization. Only
setup and upgrade provision dependencies. A stale Git binding requires canonical
generation and `make upg`, then setup; never a manual installer or source override.

## Runtime environment

Code in a checkout runs in the environment of its `RUNTIME_ROOT`. The generated Makefile
exports `RUNTIME_ROOT`, and flext-infra reads it as a typed declaration: the
`fresh-import` validation runs its probes with the platform-specific
Python interpreter in the derived `RUNTIME_VENV`, never
with the interpreter hosting the tool. Without a declaration, the owner derives the
checkout's Git root; a declaration without an interpreter fails.

The environment belongs to the `RUNTIME_ROOT`. A member attached as a submodule uses
its containing Git superproject's environment. A standalone checkout or linked Git
worktree owns its physical `<RUNTIME_ROOT>/.venv`; it never resolves an environment
from the primary checkout or Git common directory. The generated Makefile, generated
`.envrc`, and `runtime_environment_dir` derive the same path. Neither a caller
variable nor a checkout-local symlink may redirect the environment.

Authenticated source previews keep their staged source root separate from this runtime
owner. Candidate validation uses the same typed `RUNTIME_ROOT` selection as fresh-import;
an explicitly declared root is not re-elected through Git attachment. Managed base
interpreter symlinks inside a physical environment are valid, but the candidate process
must retain that environment's `sys.prefix`. A symlinked environment or an interpreter
borrowed from another checkout fails before candidate checks or publication.

The conflict-marker gate consumes the explicit `GateContext.candidate_files` inventory
of an authenticated candidate when its runtime owner is explicit. A staged source tree
does not contain a Git index. Ordinary checkout checks retain the tracked and
unpublished Git inventory; both routes reject an empty inventory and use the same
marker scanner.

Tracked Pyright configurations contain analysis policy and import roots, without
`venv` or `venvPath` bindings to the checkout that generated them. The native gate
passes the runtime owner's interpreter explicitly. Pylance uses the editor-selected
environment. Attached members share the workspace environment; independent
checkouts and worktrees own their physical environment.

## Mise toolchain

Mise manages itself: the generated `.mise.toml` declares the `toolchain.mise_selector`
release as a `[tools]` entry, and `mise.lock` pins it like every other tool. Setup
provisions its recorded release asset and verifies the checksum before entering
the recursive Make lifecycle. A complete self-pin does not require a host Mise.
Without that pin, setup stops before provisioning; `make upg` can establish it
using an available native Mise. Upgrade qualifies the final self-pin again
before installing tools and entering the lifecycle. Every later `mise` resolved
through the release's own shims is the pinned release, and `make audit`
(`codegen mise-proof`) fails when the running Mise differs from the lock.

The runtime's `.mise.toml` remains a native project configuration. The optional
global configuration has the distinct path `.mise/config.toml` under that same
runtime owner; its absence does not select the operator's global configuration.
Project resolution writes the project lock in project scope. It never classifies
the project manifest as global or updates unrelated host tools.

`make upg` publishes the Makefile through the producer half of `gen`. When that
publication changes the Makefile, the running recipe stops naming its own
targets and hands off to a fresh `make upg` on the published file; a second
change inside the hand-off fails loud as a `gen` fixed-point defect. A
Makefile committed by an earlier generator still runs its own recipe once, so
generate it with the current generator (`make gen`) before its first `make upg`.
Separate `mise.version`, bootstrap launchers and staged lock-convergence scripts
are not lifecycle owners.

`toolchain.tools` in the packaged `config/codegen.yaml` owns native tool declarations;
the toolchain model rejects a Mise `npm:` selector (ADR-025). A tool whose upstream
release metadata publishes no checksum declares `lock_checksum: false`.
ADR-025's October 9 amendment requires distributed JavaScript tools, including
FLEXT's, to use one owned Bun project, `package.json` and a frozen lock. It does not
restore Mise npm backends or retire native Node wrappers where used. Source-owner
implementation and real installed-consumer proof are required before claiming this
cutover complete; the amendment itself is not a runtime receipt.

`make setup` and `make upg` pass the explicit declared key list
(`toolchain.mise_install_keys`) to `mise install`. A bare `mise install` would also
provision every tool of the operator's global Mise registry, so no generated recipe
runs one. After setup provisions the environment, `make audit` runs the reality proof
(`flext-infra codegen mise-proof`). For each declared tool, in
order, it stops at the first defect:

1. the `mise.lock` entry exists, names a version the toolchain selector accepts, and
   carries a checksum for the current platform when `lock_checksum` requires one;
2. `mise where <key>@<version>` names the install root;
3. `mise which <binary> --tool <key>@<version>`, and every symlink hop it resolves
   through, stays inside that root;
4. the tool's declared `version_probe` reports the locked version.

The proof has no fallback, retry, or warning-only mode.
Executable resolution selects the declared tool explicitly. A binary bundled by
another tool, such as UV inside a Python installation, cannot replace the declared
producer. The proof also checks the executable the Make consumer actually invokes.

A project `bin/` never enters PATH (shell, `BASH_ENV`, or CI `GITHUB_PATH`): Mise binds
the shared shims to the first `mise` on PATH. Caches and installations stay out of Git.

Mise reaches GitHub to install a tool missing from its cache and to resolve
releases during `make upg`. Only `make upg` writes `mise.lock` and `uv.lock`;
`make setup` never writes either. Setup provisions current committed locks without
resolving them; audit owns missing, stale or incomplete lock verdicts, and CI runs
audit after setup. Functional installation failures remain red with their original
diagnostic and exit status, without disabling lockfiles or retrying. Setup installs
`uv.lock` with `--frozen`, without an audit verdict or rewrite. Audit judges manifest
satisfaction and lock integrity; drift remains red until canonical upgrade repairs
it. A failed native resolver or installer
retains its original failure; no downgrade, retry or disabled lock policy masks it.
Only successful resolution, installation and generation establish alignment.
The platforms declared by `toolchain.mise_lockfile_platforms` compose the lock
together with the platform of the machine running the upgrade, which Mise always
includes.

The default `make gen` handler passes explicit `--scope all` to conform at
`PROJECT_ROOT`: a workspace invocation covers its root and every declared member,
while a standalone repository has only itself. The request model's default remains
`SELF` for callers that do not select a scope, including file-only surfaces.
Generation publishes ordinary projections, Mise artifacts, lazy exports and docs
independently through the existing atomic file owner. Immediately before each write,
the publisher reads that destination's current state; an external edit before the
write is input rather than a campaign-wide failure. The atomic write still protects
a race during that individual operation. Every target is attempted and failed targets
are reported alongside successfully published paths.
The journal authorizes temporary staging cleanup. It never restores destination
preimages or deletes generated directories after a later phase fails. Accepted changes
and unrelated external edits remain intact. Phase diagnostics accumulate into the
publication report, and the final error verdict retains the original causal exception.
A planned deletion has no staged replacement, but its successful result still
carries a journal receipt: absence belongs inside the typed receipt, never in
`r.ok(None)`. Repeated unchanged generation must converge before publication.

An exception-only repository outcome is a failed plan even when it has no diagnostic
message yet. Planning progress and persisted evidence must agree on that failure;
an `OK` planning row never attests publication. The managed executor settles the
independent bootstrap, lazy-init and documentation targets through their own input
and dependency guards before returning the aggregate failure. A logical rejection
does not replace a later first native exception, and secondary failures do not
replace an earlier native cause. Incomplete operation receipts retain planning and
publication issues alongside successful batches and cannot qualify as complete.

Input dependency evidence remains fail-closed. In particular, the current lazy-init
binder retains a repository-wide source snapshot; the executor does not drop those
guards or exempt `conftest.py` to tolerate concurrent edits. Narrower per-artifact
provenance requires original-epoch read attribution, negative discovery witnesses
and cache-dependency replay at the existing Rope capture owner. Until those are
available, a rejected dependent component remains rejected, while authenticated
independent components keep their published gains. A fresh canonical invocation
after repairing the causal input renders from fresh inputs rather than retrying a
stale candidate inside the failed invocation.

Dependency modernization and conformance both consume the project's typed
`config/workspace.yaml` declaration for distribution roots and packaged data.
Modernization must retain those declarations when rebuilding Hatch targets;
an empty topology cannot replace a declared one. Wheel and source-distribution
templates use the same bounded `only-include` selection as modernization, with
the declared wheel source mappings and explicit file inclusions.

## SonarCloud exclusions

The committed-lock contract also removes the former SonarCloud exclusion for a missing
lock. `codegen.sonarcloud.issue_exclusions` remains the single source of the server
configuration. With `SONAR_TOKEN` in the environment, `make sonarcloud-sync` sends a
non-empty list through the `settings/set` API; an empty list uses
[`settings/reset`](https://sonarcloud.io/web_api/api/settings/reset) with `component`
and `keys`. The command rereads `settings/values` and requires the exact effective
value, including inherited exclusions. If the reset reveals an exclusion from a higher
level, the divergence remains a failure.

## Bootstrap credentials

The GitHub credential is selected in the generated Makefile preamble, for every
Make entry: the first non-empty of the caller's `GITHUB_TOKEN`, `GH_TOKEN`,
`MISE_GITHUB_TOKEN`, then the existing `gh auth token` producer in the declared
local or unset CI context. Make exports that one value as `GITHUB_TOKEN`, `GH_TOKEN`,
and `MISE_GITHUB_TOKEN`, so gh, uv, and mise read the same credential and no inherited
alias can shadow it; `GITHUB_API_TOKEN` is unexported. Native Mise inherits those
exports. The generated Make and direnv owners isolate global/system configuration
discovery, not all process variables; other caller environment values remain
inherited. `status` reports the selected source, extraction exit status, credential
presence, and CI classification without printing the value or credential-command
stderr. Its initial entry reports the producer; a recursive entry can report the
normalized inherited `GITHUB_TOKEN` instead. Caller credentials report extraction
as `not-selected`, not as a successful credential-command invocation.

Optional credentials do not block offline verbs. In `setup` and `upg`, a selected
gh producer's failure is reported and its exit status propagated before the first
Mise lock or install; success with an empty credential also fails before provisioning.
CI classification and caller precedence are unchanged. An invalid supplied token
preserves the backend's native error, without an
anonymous retry or source switch. CI jobs inject `GITHUB_TOKEN`; containers receive
the variable or a BuildKit secret explicitly.

## Evidence and checkpoints

Each piece of evidence identifies command, directory, observed revision, exit code, and
decisive result. A run that is in progress, interrupted, or missing its exit code is not
green. Concurrent changes require a fresh read before writing and revalidation of the
affected paths. A published work-in-progress commit preserves work and enables review;
completion requires integration and runtime measured at the integrated SHA.

Generation publication receipts identify their transaction and retain immutable
digest-addressed history before updating the latest report. Their effect targets
come from the journal's physical destination resolver. Written, retained and failed
targets account for attempted effects; remaining targets stay pending. Final
accounting cannot mark an invocation complete while any authorized effect is
pending. This inventory covers publication effects, not unchanged files or a
repository's unexecuted checks.

The operation receipt separately records its requested surface, elected repository
roots, and the actual completed transaction batches, including unchanged outputs.
`initialize` qualifies only its Makefile bootstrap; its read-only verification does
not require or certify complete generation. Complete generation qualifies its
managed and documentation batches after each has settled. A complete `all` scope
can verify the `self` subset only when that repository root is in its recorded
coverage. Checks authenticate source, generator, output and physical identities
without planning, rendering, repairing or replacing the receipt. Missing coverage
and changed identities remain failures.

Workspace Make bootstrap composes the root and eligible members' actual receipts
after each has published once. A member failure prevents completed aggregate
coverage. Member eligibility reads PEP 610 metadata, editable path inventory and
package resolution from the elected physical Python environment. A foreign API
caller does not lend its installed packages to that decision. Resolution observed
in that Python is distinguished from loaded-code execution; loaded-code provenance
remains checked when the caller is the elected interpreter. Hosted topology uses
the declared hosted-provider flag independently of the local CI gate partition.

Installed metadata comes from that Python's physical `purelib` and `platlib`
directories. Its `sys.path` supplies separate import-resolution observations.
Editable source-tree `egg-info` stays outside the installed inventory; duplicate
installed metadata and directories outside the elected prefix remain failures.

PEP 735 dependency groups retain string requirements and `include-group` tables
in order, including repeated occurrences. Group references are local to their
declaring project; absent references, cycles and normalized name collisions fail.
Runtime and optional dependency metadata retain PEP 508 strings. Development
groups remain groups and are never promoted into distribution runtime metadata.

The pytest runner retains the native exit code when startup fails before a final
JUnit report is produced. Its process-outcome receipt and raw log remain available,
but no completed-suite summary or run accounting is published. A graceful failing
suite with JUnit still follows the normal diagnostics and accounting path; neither
an interruption nor a missing report is evidence that tests passed.

Suite profiles are bound only after successful execution or a completed failing
suite with its final JUnit report. An interrupted profiling child keeps its native
process outcome and raw log without attempting to read an unfinished profile.
A missing profile from a completed suite remains an artifact failure.
Startup instrumentation, the pytest launcher and the profiling entrypoint share
one process-local profiler. Nested profiling subprocesses retain their own profiles
and still execute the original site customization.
Tests that need sample pstats reuse `native_cprofile`, whose stdlib workload runs
in a separate process so it cannot compete with the worker's active profiler.

The typed run context is published before waiting for the Testmon lease and
records whether that lease was acquired. An interrupted wait therefore retains
its parent profile and authenticated invocation identity without inventing a
child process outcome. A context with an unacquired lease rejects any selection,
inventory or suite artifact; it proves no test execution.

Profile reports select the nearest project manifest owning the profile artifact.
This keeps member reports confined to their member when Make starts at the
workspace root. Profiling imports the runner through its published validation
package.

Each authenticated parent, collection and worker profile retains its own full
view and repository-source view. Source filtering uses the configured scan roots
and direct repository Python modules, with full filenames preserved. The native
filter runs before the row limit so startup and waiting functions cannot consume
the source view's budget. These views expose the captured calls and timings;
they do not combine independent processes or prove that a timed-out operation
completed.

Distributed stop requests validate the initialized native controller through
`p.Infra.PytestStopController` at report time, not during session startup. The
runner requests a stop through its real `shouldstop` field and leaves shutdown
to xdist. A present incompatible controller fails instead of taking the serial
session path. Plugin autoload and enforcement remain active.

For namespace automation, investigate catalog, classifier, transformation, publication,
and consumers in that order. The namespace laws are codemod catalog rules, so the
codemod gate is their one verdict. Preserve mutability, inheritance, imports, and
collection; validate the transformation through the public interface before widening
the batch. Structural refactors go through `make mod`.

Follow the [canonical governance sources](../index.md#governance-pointer):
workspace law, FLEXT law, ADR-005, ADR-014 as amended by ADR-018, ADR-015 and
ADR-024. Read their linked universal skills; this checklist is an execution
checkpoint, not another architecture SSOT:

1. Elect one domain/namespace/location owner from live declarations. Preserve
   `c → t → p → m → u`, layer-0 config/settings and pure declaration layers.
2. Consume facade exports through MRO; use typed Pydantic ingress/egress and `t`/`p`
   contracts. Inject dependencies explicitly at the sole `api.py` composition root.
3. Reuse the existing correct-domain helpers under SSOT/YAGNI/DRY/SOLID/DI/CA.
   Rewire every producer/export/consumer and remove superseded routes together,
   without losing functionality or weakening runtime contracts.
4. Repair canonical sources, not projections; regenerate and prove repeated gen/fix/fmt
   idempotent. Generalize recurring causes at the existing rule/semantic owner.
5. Use the existing custom `refactor ast` and `refactor violations-sweep` CLI owners,
   verifying their current help. Record per-rule before/after and full-catalog collateral
   evidence for the root and every declared member (currently 32 projects), including
   zero, applicability, failed and unexecuted rows. Changed detectors require a new
   baseline; lower totals never excuse introduced findings.
6. Prove global lint/type/test/coverage/docs/build and real public runtime over the
   declared scope, including tests/scripts/examples; retain command/cwd/candidate/exit
   and decisive output. Missing coverage or prerequisite skips do not prove fleet green.

Private approved plans remain local execution context. Do not collect, project, copy
or link them into published documentation without explicit publication authorization.

`make mod-rules` inspects the full governed source inventory without rewriting it.
Native `isinstance` and None assertions retain Python's type narrowing. Assertions
with a message retain its evaluation on failure. Their automatic matcher rewrites
are retired: unused return values lose narrowing, while generated conditionals
duplicate language behavior. Explicit matcher calls remain available for observations.
The text catalog composes Infra's shared rules with each project's local
`config/rules/mod/sed.yaml`. A domain-specific rule belongs to that project's
catalog; copying it into the shared catalog creates an ambiguous owner and blocks
the scan. Rule IDs remain unique across the composed catalogs.

AST planning elects rules separately for each governed project's declared
distribution and runtime dependencies. The workspace scans the union of shared
catalogs once, then admits each occurrence against its nearest project's election
and semantic facts. A library owner's imports remain within its domain; the same
imports in a consumer remain violations. Reports retain zero counts for every
governed repository and elected rule.
The native scanner takes one `selection`: rule identifiers or an already composed
rule plan. A composed plan must govern the requested root and remains the only
selection authority for that invocation.
Catalog election and staging share the same YAML ingress. Validated streams are
memoized by their exact text as immutable JSON; each caller receives fresh mappings.
Current file reads and canonical rule digests still detect drift before publication.

Generated facades compose declarations published by their current private family.
Rope resolves existing bases before composition: upstream bases remain, while an
own provider moved outside that family leaves its MRO and unused imports.
Unresolved providers fail before publication. Class-move previews and immutable
plans leave absent destination directories absent; only an authorized apply
creates them after source and identifier validation.
Snapshot resources derive existence, children and observer indicators from the
authenticated source inventory. External providers keep their native Rope
identity through a snapshot-owned external project and read the captured bytes.
Physical file changes remain inputs to publication CAS, rather than changing
the source graph while a plan is being computed.
Rope owns module, regular-package and namespace precedence; Infra validates the
native resource it returns without maintaining another election algorithm.
Absolute and relative lookups share one native-folder validation boundary.
Absent relative context remains `None`: resource lookup reports absence and
module lookup raises Rope's native missing-module exception.
Restructuring overrides use the SDK's native input types. The existing module
admission exposes semantic capabilities to filters, and identity alternatives
share one injected default matcher.
Import capture retains one typed lookup keyed by native root, module and relative
level; it does not transport unused copies of the SDK's search roots.

Rope owns loaded frozen stdlib aliases through its existing extension cache and
`import_dynload_stdmods` preference. Its native module election preserves explicit
extension precedence and searches source resources, including the supplied folder,
before returning a frozen alias. A cached alias cannot shadow a source created
later. Live and captured projects consume that same SDK contract without copying
loaded module names into extension preferences.
Blocked-import sentinels in `sys.modules` remain blocked.

Import normalization treats exception targets and structural pattern captures
as local bindings. These names do not load a package facade or reintroduce an
unused import removed by `make fix`.
Static facade imports group symbols and module reexports by their emitted
absolute owner. Module reexports retain their explicit same-name binding;
ordinary symbols keep their published names. The rename rule distinguishes
that static reexport from a changed local name in both runtime and
`TYPE_CHECKING` imports.
Imports with the same bound name but different lexical providers cannot be
hoisted into one global binding. Normalization rejects that collision before
publishing the candidate.

Layer-zero config/settings obey their own-namespace boundary in every lexical
scope, including `TYPE_CHECKING`. Private family assembly retains its declared
role and import-layer contract. Defaults, decorators and a comprehension's first
iterable resolve in their enclosing scope; a local capture cannot hide a provider
needed by another scope.

Binding snapshots elect providers from rules actually found by the scan.
Resolved-symbol and same-binding captures authenticate their complete consumer
source and carry requested member paths through local dependencies, reexports,
lazy publications and class ancestry. Module operations derive requested imports
from their authenticated source bytes through the same capture owner.
Unrestricted snapshot requests retain the complete closure, including inactive
import suites. Both scan and check use the same typed admissions and
authenticated snapshots.

Lazy-init planners keep native semantic objects and ancestry-receipt caches local
to each publication consumer. The authenticated structural index can be shared
with its original selection receipt, but an observation scope alone does not
isolate native caches. Each read-only consumer uses the existing `frozen_layout`
context to resolve its elected source and Python-path folders once during that
consumer's lifetime; source-consumption receipts and epoch validation remain active.
Declaration ancestry reads each class header from Rope's existing cached logical-line
index. It does not rebuild the module's complete statement models for each class;
payload-body admission still checks the full declaration body.
Decorator admission compares native names, preserving imported aliases and
rejecting shadowed declarations. Builtin descriptor wrappers compare their
underlying Python object by identity because Rope's lexical and imported builtin
modules can hold different wrappers for the same object.
Cross-consumer ancestry reuse requires an independently
captured complete dependency closure: sealing a scope after native resolution has
already warmed does not recover its earlier provider or negative-query reads.
Builtin classes have no source scope and are traversed without a source-receipt
cache key. A newly built package decision is not propagated as sealed evidence
before its consumption receipt has been issued.

Within one package decision, module export policies receive the already elected
package layout. An authenticated empty export inventory terminates that module's
export planning before policy resolution; it does not synthesize aliases or omit
the original source observation that proved the inventory empty.

Native source-folder enumeration excludes runtime cache artifacts already
classified outside the source epoch. Otherwise an authenticated directory listing
can retain a bytecode-cache name after the physical cache disappears, and Rope's
child-resource lookup fails before source verification can run. The physical
directory-membership receipt remains strict: cache removal still invalidates that
receipt and is handled as source-epoch drift, not silently accepted.

Directory-query receipt unions retain the elected immutable observation when no
selector is added. Identity, query, membership and physical-alias checks still
precede this reuse. The optimization avoids replacement-model allocation; it does
not extend the lifetime of physical observations or excuse a later conflicting
fragment.

The census refreshes its Rope inventory after constant-consumer publication and
declaration removal, before collecting the resulting report. Deleted or added
initializer projections must be reflected in the source inventory it reads.

Typing-alias relocation plans the declaration, destination and consumer changes
before one protected publication. Explicit imports retain their lexical scopes
and local bindings. Unsupported references, ambiguous bindings and uncertain
star exports reject the entire move before publication, including creation of a
previously absent destination. Quoted type expressions participate in semantic
identity checks; ordinary strings, `Literal` values and `Annotated` metadata do not.

Lazy initializer planning keeps facade exports lazy. A version metadata export
whose name collides with its child module uses the existing eager-dunder contract:
the scalar is bound before lazy installation and omitted from the lazy map. Public
export traversal must not replace that scalar with the imported child module.
Initializer ownership is elected from actual content and the accepted generator
markers. Absent or empty initializers and explicitly marked projections may be
generated. A nonempty authored initializer is retained in full, including executable
loaders, declarations and constants; its public exports remain part of discovery.
The lazy planning report records `ownership=authored`, `disposition=retained` and the
existing RETAIN action. Publication reelects ownership from the current target before
its single write, so a later authored replacement is retained and is not counted as
a generated file. No directory-name exemption list selects this behavior.
Shared input snapshots document the planner's inputs; later source edits do not
invalidate an entire generation. Directed validation checks the actual generated
targets rather than comparing every source with an earlier workspace snapshot.

Repository generation plans treat malformed source as a failed input. The
planning report at `.reports/codegen-plan.json` records each selected repository's
outcome, exception type and original traceback. Generation reports failures at
their affected files and retains successfully generated files. Changes made
outside the generator do not authorize restoration of earlier workspace bytes.
Transaction recovery and public `abort_locked` consume native `p.FailureLike` values,
not error strings. A successful result is rejected before journal inspection or cleanup;
an empty failure remains a failure. The initiating exception, error code and metadata
survive recovery, while `cleanup_error`, `recovery_context` and exception notes record
secondary diagnostics. A validator's `ok(False)` is an explicit publication rejection,
not a native failure whose metadata may be reconstructed from its message.
Lazy binding discovery parses package initializers only, so unrelated malformed
consumer code cannot invalidate an otherwise valid declaration projection.

Text codemods validate replacement Python before publishing any planned writes.
An invalid replacement returns a failed result carrying the original `SyntaxError`,
including its filename and source text. The complete batch remains unchanged.

## Check gate partitions

`make file-gate FILE=<repository-relative path>` delegates to the existing
`check run --file` owner, never bare analyzers or a second gate engine. The raw
Make value travels through an exported environment value, not interpolated shell
source. Selection rejects empty, absolute, traversal, missing, non-Python and
symlink-component paths before creating reports or invoking tools. Only the literal
file reaches each gate's existing `check_files`; no mutation is permitted.
The Make pre-gate explicitly selects registered lint, format, Pyrefly, Mypy,
Pyright and codemod gates through the existing typed `RunCommand.gates` owner and
`resolve_gates`; no separate gate vocabulary or configuration is introduced.
The public `check run --file` requires explicit `--gates`, never silently falls
back to whole-project gates, and rejects unknown names before scanner execution.
Every selected gate retains its native diagnostics and verdict; failures, missing
tools/configuration and malformed reports remain blocking.
Codemod uses its elected, staged provider configurations and native report owner.

The former bare `typos` hook existed only in the Make recipe, help and tests,
always under `|| true`. This branch declares no canonical typos runner,
configuration or provisioned toolchain capability. Removing that ownerless
best-effort advertisement removes no supported acceptance capability: it never
contributed a truthful verdict. Registered rule diagnostics remain unchanged;
no dictionary, installation, provider or suppression replaces the hook.
The pre-gate remains bounded; full `make check` is still required acceptance.

Trailing comma layout has one owner: Ruff's formatter. The tooling SSOT records
the removal of redundant `missing-trailing-comma` (COM812) lint enforcement using
its official rule name and rationale. This must be regenerated before runtime
validation; changing the SSOT alone does not update existing projections.

Selected functional gates remain blocking. `make check` fails when the selection
contains no projects or when a selected project has no `pyproject.toml`; no project is
skipped silently.

`make check-pyright` runs the selected project's complete Pyright configuration
through the native gate capture service and retains its raw report and exit status.
From a workspace root, `make -f <member>/Makefile check-pyright` selects that
member's declared configuration and the containing workspace's physical environment.
It is a diagnosis verb; full `make check` remains the acceptance boundary.

`make mod-types` applies the AST migrations declared by
`make.type_contract_rules` to the complete selected project. The native AST engine
verifies rule fixtures, resolves bindings, and repeats safe rewrites to its fixed
point. Source models and protocols own the resulting contracts: consumers pass
declared state models directly, and field defaults remain visible to both Pydantic
and synthesized constructors. Required private attributes use their annotations;
attributes with actual defaults or factories retain those declarations.

Local runs, CI, and hooks derive their gates from the same active set: `CI=N make check`
and `make check` without `CI` run the complete active set. `CI=Y make check` excludes
only the declared `make.ci.local_check_gates` (Pyrefly remains in CI). The
configuration keeps Mypy, Pyright, codemod and smells out of CI. Every gate blocks in
every context that runs it; there is no informative or advisory gate. The `check`
pre-push hook drops the inherited `CI` to run every active gate, so Mypy and Pyright
block at pre-push. The pre-commit hook runs the same gate partition as CI and
the same incremental `make test` operation with the configured CI exclusions.
Conflict detection uses the canonical Git inventory, including unpublished files,
and the shared merge-control classifier. It reads literal source-link targets without
following them. Every finding, including a native warning, blocks approval while its
original severity remains in the receipt.

Every workspace and standalone projection exposes `make pre-commit` for the CI validation
workflow. CI invokes the separate approval verbs declared by `make.workflow`, in their
declared order, and closes with `verify-clean`; it never substitutes the fast hook for
approval. The configured CI token selects the blocking CI gate partition. Audit is
read-only conformance and installed-lock provenance, not generation or a dirty-tree
check; legitimate staged changes are not rejected simply for being staged.

CI setup always reconciles the owned physical environment through locked,
noneditable installation, including an existing venv. It does not initialize,
activate or operate on members, and uses root-declared topology rather than reading
sibling manifests. Local setup without the CI token retains local source routing.
Only local upgrade resolves or writes locks; setup preserves the first install error
without retrying under a different lock mode.

After installation, setup validates Mise declarations and synchronizes environment
files through two in-process batch calls. Local workspaces select `all`; attached
members, standalone repositories and CI select `self`. Git declarations own discovery
order, and each operation runs serially through its original validator or writer.
Missing required roots remain failed inventory entries. Explicit Git management,
repository code-generation and read-only policies determine applicability; inapplicable
entries retain their reason and receive no successful native outcome. Independent roots
continue after a returned failure, and the original first failure remains the command
result. The typed receipts in `.reports/setup-operations/` record actual roots, execution,
native outcomes, returned paths and central issues; CI preserves those reports.

The original tool bootstrap also publishes the elected operation report before
Python or the installed Infra CLI is available. Its shell EXIT handler records
the observed Git candidate, native exit status, reached bootstrap stage and
explicit completion. The rendered report schema comes from the same Pydantic
model; the runtime substitutes only validated scalar facts. Root and scope `.` in
this early receipt resolve against the repository containing the report, rather
than the invoking workspace's current directory. An interrupted bootstrap reports
only that attempted root, with no invented member inventory or effect paths.
Report transport errors preserve an earlier native failure and turn an otherwise
successful operation into a reporting failure. CI uploads this structured receipt
on every outcome without exporting command payloads, environment values or logs.
Authentication admission runs inside this same bootstrap after its report
handler is installed. The original credential failure therefore publishes its
native exit status and `network-auth` stage before tool provisioning starts.
Source archives without Git metadata retain a null candidate and the original
Git read status separately; metadata absence does not add an installation
prerequisite or confer eligibility for a candidate attestation.

Explicit Git reference migration precedes a consumer's dependency resolution.
Run the current tool owner's root Make operation with all four explicit inputs:

```bash
make -f "$TOOL_MAKEFILE" upg-sources \
  SOURCE_ROOT="$CONSUMER_ROOT" SOURCE_URL_PREFIX="$GIT_SCOPE_PREFIX" \
  SOURCE_REF_FROM="$RETIRED_REF" SOURCE_REF_TO="$INTEGRATED_REF"
```

The dispatcher uses the current elected tool environment and passes the typed
reference triplet to the existing `deps modernize` owner. It does not depend on
the consumer installing a newer Infra before repairing its own references.
Missing inputs fail rather than selecting an implicit target. The URL directory
prefix selects the authorized source owner; the old reference selects only the
retired explicit reference. This mode preserves original URL transport,
subdirectories, extras, markers and unrelated version constraints, including
native UV and Poetry source selectors. It retains the consumer's TOML layout,
integration branch and build backend, without running FLEXT architecture or
runtime-floor phases. A partial request fails before writing; `--check` audits
the same transition without mutation. The consumer's own `make upg` then owns
resolution and lock publication.

Normal test verbs remain incremental testmon only and omit the configured slow
markers. The filesystem cache lives at the typed XDG/HOME-derived project path.
The explicit single-file operation runs incremental selection followed by complete
execution of that file, including its declared slow tests, on the same database.
No empty marker phase is invoked or converted to success. Zero execution is accepted
only as an integrity-checked cache hit with complete inventory/deselection accounting.
Actions restores only that project database. Keys separate project, operating system,
architecture, Python runtime and branch; generation IDs remain immutable. Restore first
prefers matching lock/config inputs, then earlier generations in the branch, then the
PR base or repository default branch seed within GitHub's cache visibility rules.
Testmon revalidates restored inputs rather than discarding history on every lock change.
Branch pushes and same-origin PRs may save with a fresh completed-run
path/digest/saveability receipt. Fork PRs and other events remain restore-only. The
SQLite owner checkpoints and checks integrity before the runner releases its lease
and exports the receipt. Cancelled, corrupt or incomplete runs cannot publish;
a completed failing test run may save without changing its failing status, including
when a later step fails. Publication never depends on a branch-name allowlist.

Toolchain caches retain a separate immutable generation for each Actions run and
attempt. Restore prefers the current lock and manifest inputs, then an earlier
OS/Python generation within GitHub's repository and ref visibility rules. Save
consumes the restore action's primary key and remains eligible after a completed
failure or warm restore. Branch pushes, explicit dispatch and same-origin PRs may
request publication; fork requests and cancelled runs do not. The native cache
action's effective access mode still governs whether upload occurs. A successful
save step alone proves no generation was stored: acceptance requires the actual
saved key or cache record, including when a reserve collision was reported.
Each workflow declares whether the shared save fragment may emit PR payload
accesses. Docs accepts push and dispatch only, so its save conditions contain no
PR payload references. The dispatch-only matrix groups runs by workflow, event
and ref without accessing a PR number.

CI uploads the reports that the original operations produced on every job outcome,
including successful checks, completed failures and interrupted runs. The upload also
runs when no test workflow row is selected, preserving the check reports independently.
Its allowlist includes structured check summaries, coverage and JUnit artifacts, original
suite/selection/inventory process outcomes, selection manifests, run context and
accounting, cache integrity decisions and Markdown reconciliation. Raw process and test
logs remain outside that artifact. Generation publication receipts include the latest
receipt and immutable transaction history, retaining written, retained, attempted and
pending targets without source snapshots. Planning evidence records candidate HEAD
and dirty state when the selected root owns a Git repository, otherwise an explicit
unversioned candidate, plus destination identities, planned modes and content digests,
counts and native failures. It excludes desired source bytes, captured file state and
environment command payloads. Original plan objects remain local to execution.
An early failure publishes only the receipts reached
by the operation; a missing report remains an artifact error, never a manufactured
complete execution. Uploading reports does not change the native command status or
authorize cache publication from an incomplete run.

The SSH gate-attestation owner consumes an original producer receipt and verifies its
candidate, context, policy and report digests before signing. It does not invoke Make.
Schema v2 addresses each immutable proof by repository, commit, effective runtime/policy
context and stage. Repeated publication verifies the existing signed object and its
original artifacts before reusing it. Signed public facts retain the actual process
outcome, portable operation intent and diagnostic classification. The original public
receipt binds the exact argv digest; command bytes and the working directory remain in
private execution checkpoints, outside the CI artifact allowlist.

Admission derives from the original typed reports rather than caller success flags.
Checks require complete target and requested-gate coverage in SARIF. Tests require
original process, accounting and diagnostics reports with complete positive execution.
Timeouts, signals, collection errors, operational failures, missing artifacts and changed
digests remain failures. The complete-execution policy may admit finished findings while
preserving their nonzero status; the clean-quality policy rejects them. Bare `make check`
uses the existing workspace capture route to execute the original checker once. It
preserves that producer's native process outcome and owns an exclusive report base,
then writes an immutable receipt only when the candidate and original reports remain
eligible. Dirty, changed or unversioned candidates still execute and retain a capture
result without claiming reusable evidence. The native pytest runner captures its
candidate immediately before the original suite process and publishes original receipts
after accounting and diagnostics are written. It retains its existing deadline and
testmon execution. Both producers share the same capture and report-binding owner.
CI preserves the public original receipts and their required structured reports, while
omitting private checkpoints, commands and capture errors. The Make policy and receipt
directory come from the typed codegen specification. CI signing/restore wiring,
zero-execution cache evidence and other
stage adapters remain required integration work. Verifying a setup proof never
provisions a fresh runner.

Capture receives the selected repository's full `CodegenInputs` through the canonical
layer loader. Its policy and report directory come from that typed target specification.
The context binds the effective specification, ordered input filename/content digests,
portable operation intent and actual runtime. Tests also bind their existing native
`testmon_environment` identity. Completion reloads the same target loader and rejects
configuration or runtime drift while preserving the original process outcome. Config
payloads and machine paths are not exported with these fingerprints.

`make status` also reads the selected repository's native Git signing configuration
through the existing workspace CLI. The report names the declared signing format,
file references and each setting's effective origin/scope and native process outcome.
It does not read key/trust files, invoke signing/default-key commands or consult a
keyring. Undeclared settings preserve Git's absent-key outcome (`1`, with no stdout
or stderr) and nullable references, not an empty path. Empty declarations, unsupported
signing formats and native query failures remain errors. File references can point to
unavailable files; discovery does not claim verified trust or an observed fingerprint.
For SSH, Git's `key::` form and its accepted deprecated raw `ssh-` form are literal
public declarations, never paths. Their base64 envelope and encoded key-type agreement
are checked without reading files or contacting an agent; malformed declarations fail
without exporting their payload. Algorithm usability and trust still require the
selected native signing or verification action, not this observation.
The CLI emits the typed report as JSON, excluding native values. Neither `status` nor
original check/test capture selects signing: capture binds the typed target policy and
producer evidence. Direct `u.Infra.git_create_gate_attestation` and
`u.Infra.git_verify_gate_attestation` select signing/publication or signature verification;
their required trust input and native key/signature failures remain fail-loud. A valid
observation is never signed proof, and absent signing material does not gate unrelated
offline producers.

`smells` is not part of the `make check` partitions. The selector-free `make smells`
verb runs only the qlty smell scan and fails when it finds defects. The
`runtime-census` gate stays in `make check` and grades every runtime enforcement
finding, including rules that qlty also classifies as smells. An empty or
malformed qlty SARIF response is a failed scan, not a zero-finding receipt.
Native primary source spans and all `relatedLocations` pass through the typed issue
and SARIF report contracts without dropping comparison locations outside the primary
project. Coordinates are emitted only when the scanner supplies them, including explicit
zeros; line-only and regionless native locations do not acquire invented coordinates.
Point-only diagnostics from other gates remain point-only. The Markdown summary still
uses the primary location, while the SARIF artifact carries the comparison evidence.

## Census consumer evidence

Family classification uses the facade catalog and the semantic module's owning
package. An exported declaration's full class name does not replace its family
suffix. A containing family directory takes precedence over a facade filename;
the filename is considered only outside a family directory. Conflicting family
directories fail before classification instead of selecting by catalog order.
Package-relative filenames alone cannot identify a nested family.

The public refactor census report retains `Object.all_reference_sites` separately
from `runtime_reference_sites` and `script_reference_sites`. Each evidence site
includes the Rope character offset, path, line and surface. Exact path/offset
identities are deduplicated and sorted deterministically; distinct references on
the same line remain distinct. Every hit's absolute path and nonnegative character
offset are validated before definition filtering. Evidence excludes a definition only by
its exact normalized path/offset; the older line/path fallback remains confined
to reachability counts. Indexed source, script, test and example consumers and
static `__init__.py` reexports are retained,
including occurrences of private names and facade members.

This is report-only migration evidence, not a change to production reachability.
The existing reachability resource eligibility, line-level deduplication, private
and facade exclusions, test/example exclusions and reexport exclusions still own
the old counts and unused/removal classification. All-surface evidence must never
be interpreted as permission to delete a helper or as a dynamic closure proof.

`reference_evidence_collected` distinguishes an empty collected result from a
disabled search (`include_references=False`, or census rule selection without
`unused`). Evidence covers only the active Rope workspace's indexed files and its
existing name-index candidate selection. Untracked files in indexed wrapper
surfaces participate; ignored paths, nested ungoverned repositories, files outside
the workspace, alias-only downstream files without the original identifier, and
reflection/dynamic imports are not proven covered. Lazy export strings are not
semantic reexport occurrences. Source and reference-resolution failures propagate;
definition-token candidates are checked against the inventoried Rope binding using
the existing Rope identity comparator, not selected by spelling order. Separate
function/parameter bindings on a declaration line remain separate. If multiple
tokens on that line resolve to the same binding (for example, a one-line declaration
and use), the search fails with explicit ambiguity instead of guessing the
definition. An unlocatable definition identifier or occurrence without an absolute
path/valid offset fails instead of producing an apparently complete empty report.
A collected result is therefore bounded static evidence, never a whole-program
absence proof. Collecting
private/facade evidence expands reference-resolution work but adds no scanner or
registry.

## Bounded Mypy failure status

The Linux Mypy command applies `prlimit` before launching the checker. In the observed
Mypy 2.3.1 run, an exhausted plugin allocation produced `INTERNAL ERROR` and exit status
2;
[the tagged Mypy source](https://github.com/python/mypy/blob/v2.3.1/mypy/main.py#L167-L174)
assigns status 2 to blocking internal errors. This is version-specific behavior, not a
fixed expectation for later Mypy releases. The resource test requires the workload to
start, then a nonzero raw status and a diagnostic without a timeout; it never rewrites
the result into a synthetic `MemoryError` or success. The Darwin supervisor can instead
terminate a process whose resident memory exceeds its limit.

The Mypy gate validates every nonempty report line as JSON, except native `LOG:`
progress lines. Indentation and a `Deferral trace` prefix do not exempt plugin
output from validation. A malformed report remains a failed gate with its original
stdout, stderr, and exit code retained; it is never evidence that analysis passed.

## Abstraction-boundary project identity

The boundary gate reads the declared project identity through
`u.Infra.read_project_metadata_result`. Owner exemptions and TOML allowances use that
typed identity, so renaming a checkout or creating a linked worktree does not change its
policy. A consumer placed in an owner's named directory remains a consumer. Missing or
malformed project metadata blocks the gate and preserves the metadata reader's
diagnostic; directory names are never identity fallbacks.

## Service foundation

The project service foundation must preserve the local service and its canonical
command-context inheritance through the public `s` export. Rebinding an imported
type alias to another class can retain the upstream identity in static consumers.
Command fields remain declared once in the canonical model owner; duplicate fields,
casts and suppressed diagnostics are not repairs. The local service-import law is
authoritative: a conflicting named-import candidate requires explicit contract
resolution rather than silently substituting an import or inventing undeclared exports.

## Codemod scanner contract

Source-file discovery uses one pruned traversal per selected project, without a
preliminary walk to elect directories or repeated ancestor checks for every file.
The same walker handles filesystem and authenticated Rope reads. Nested repositories,
ignored trees and declared non-participants are pruned before descent; top-level
exclusions remain relative to the selected project, not matching nested tier names.
Semantic migration consumes the root scanner's complete governed inventory directly;
it does not rediscover import-provider roots and recursively rescan each member.

Every codemod policy finding blocks the gate, whatever its rule severity. Failed rule
discovery, failed scanner execution, incomplete output, and invalid diagnostic payloads
block as native failures with their own diagnostics.

The gate consumes the complete native `ast-grep scan --json=compact` array. The
[documented scan contract](https://ast-grep.github.io/reference/cli/scan.html) and
[native diagnostic schema](https://ast-grep.github.io/guide/tools/json) distinguish a
completed scan with error-severity findings (exit 1) from a completed scan without
error-severity findings (exit 0). Exit 1 must carry only ast-grep's complete terminal
diagnostic, whose count equals the validated error-severity findings. Additional
traversal diagnostics remain blocking: ast-grep can continue after an unreadable path
and still return exit 1 because another file contains a finding. The scanner boundary
checks the
[native terminal diagnostic](https://github.com/ast-grep/ast-grep/blob/0.45.3/crates/cli/src/utils/error_context.rs#L200)
and rejects extra output from the
[native path worker](https://github.com/ast-grep/ast-grep/blob/0.45.3/crates/cli/src/utils/worker.rs#L92).
Timeouts, forwarded signals, other exit codes, malformed JSON, and disagreement between
exit code and diagnostic severities remain failures, even when stdout exists. Both
whole-project checks and `check_files` scan every elected provider rule.

Binding inference captures the source files and symbol owners required by
rules with actual occurrences. Syntax-only findings need no import closure.
The check gate and the mod scanner share this input election, deduplicating
source reads without reducing the rule inventory or its diagnostic evidence.
Native module queries use the shared parsed and semantic module admission
owners, retaining SDK object identity while exposing their declared protocols.
Rejected semantic providers report their native type. Qualified identity lookup adds
the requested module and identity as an exception note, retaining the original
exception and traceback; neither failed admission nor a rule is silently skipped.
Matcher patterns give captured expressions a parenthesized grammar context;
their authenticated source bytes and original coordinate checks stay intact.

Facade consumer discovery resolves each native Rope `ImportedModule` once within
the current source file. Repeated occurrences retain their binding and owner checks;
the resolution map holds the native import objects, not a separate name registry.
Rope's line tables convert AST byte columns to character offsets before resolving
each binding. Each receiver is already a native AST `Name`: the same parsed
module supplies its lexical scope at that offset, and Rope resolves the existing
node without tokenizing and parsing its text again. Local shadows and native
import identity remain checked. The resolution map does not persist across source
observations or replace source, producer, or publication proof.

Rule `files` and `ignores` globs are relative to the elected `sgconfig.yml`,
not the consumer's working directory. A source-only rule must therefore cover
`**/src/**/*.py` for standalone and workspace members outside the provider's
configuration directory. Single-class export repair derives publication from
the declared project stem, source shape and governed scanner scope, including
internal Python tiers; a different file stem does not
justify renaming the class or adding exports by hand.

An admitted AST report carries its source inventory, rule-plan digest and policy
inputs. Reuse requires unchanged membership and authenticated states before
publication; the transaction checks those inputs under its lock and validates
membership again before accepting the published candidate. Parsing associates
findings with captured states between complete physical verification barriers.
AST replacements publish through the authenticated file-plan boundary, then reuse
the import normalizer on only the rewritten files. Unused imports and formatting
are normalized before the next mod check; normalization failures remain blocking.
Failed AST or semantic passes retain accepted writes for fix-forward. They propagate
the operation's failure or first exception without restoring an earlier repository
inventory. Each publication still validates its planned files and expected source
identities before writing; a stale later batch cannot replace newer independent edits
or undo an earlier accepted batch.

Source previews use the mandatory `p.Infra.SourcePreview` capability composed by
the public API. Census, accessor migration and codemod services receive that capability;
they do not construct a generation transaction inside their execution. The existing
transaction owner materializes authenticated candidate bytes and removes only its
staging after validation. Parser or validator exceptions retain their original cause
and leave live source bytes and modification times unchanged. Native Ruff uses the
declared external project cache so its cache files never enter the authenticated
source view.

A nonempty admitted file phase with no required byte, permission, or directory
effects publishes a fresh observation under the same root lease. It still verifies
its producer, input and output identities, and rejects pending journals or foreign
residue. It does not materialize a publication staging tree. Mandatory runtime
admission still consumes the sealed candidate in its read-only view, including
unchanged Python proposals. Equal desired bytes alone do not authorize this path.

Generation seals the exact bytes proposed by its renderer, without running source
repairs or the full workspace checker. Its physical runtime authentication, sealed
import origins and runtime census remain mandatory; a negative census report is
rejected even when the subprocess itself succeeded. Semantic publication explicitly
selects normalization before sealing and adds every native default check inside
the guarded candidate consumer. Reusing a sealed receipt never removes that
operation's selected preparation or admission policy. Both operations retain
source, membership, inode, candidate-tree, lease and journal verification. The
independent `make check` surface continues to own its complete configured gates.

Journal footprint inspection and authorization hold the same root journal lease
as publication. Authorization observes the current journal under that lease;
an earlier read-only snapshot does not become a global generation precondition.
The public footprint diagnostic authorizes the recorded effects against current
physical participant policy, then returns that current observation with its journal
identity and pending-effect fields. It never invokes prospective conform planning,
source scans or report publication; its root-only request has no generation
selectors. The native journal lease retains its persistent lock identity, but no
participant lease or recovery is acquired. Recovery and publication retain their
own exact journal receipts and physical-state guards. Generation planning reports
continue to use the compact `CodegenPlanningReport` evidence projection rather than
serializing native file-plan authorization snapshots.

Documentation generation publishes one scope batch before capturing and rendering
the next scope. A member batch captures its own sources, the shared root guides and
configuration, and the renderer templates; the aggregate root captures its complete
workspace inputs. File plans carry those authenticated inputs to the existing guarded
journal writer. Changed current-batch inputs reject the affected publication without
discarding accepted earlier batches. Generation does not re-render the full workspace
at commit or run formatting, linting, or test gates; the corresponding Make verbs own
those operations.

Plan collection uses its own `docs-collection` phase and source topology rather
than the renderer's input inventory. Publication passes the same durable journal
to the existing source-state verifier. An absent file's parent identity can change
only when that journal proves directory creation; published file receipts then
replace their authenticated preimages. Directory receipts are captured once per
batch and shared across targets.

Read-only Make verbs never invoke conform, generation, repairs, formatting, or
codemod application. Audit checks installed dependency and environment provenance;
verify-clean checks the documentation and Git state without rendering replacements.
Installation provenance binds the locked source, installed origin, declared physical
checkout and committed gitlink; unrelated worktree changes do not invalidate that
identity. Operation admission separately authenticates the content and epoch of its
consumed sources and accepts changed inputs only through its actual publisher's
effects. Persisted publication reports never authorize those changes. The final
`verify-clean` gate still rejects staged, unstaged and untracked files, including
generated artifacts, until their integration is complete.
Generation retains the setup-owned environment policy: local workspace setup binds
the declared subprojects as editable, and local generation may publish their managed
artifacts. CI setup installs its locked noneditable dependencies, and generation in
that context publishes only the invoked repository. The dependency and editable
declarations remain owned by the established setup and provenance contracts.

Protected compilation and pytest validation use the same environment boundary as
lint validation: the child keeps its project's working directory and configured
plugins while removing the orchestrator's `PYTHONPATH` and forced-color setting.
An importing parent cannot supply source modules or startup hooks to that child.
When canonical child profiling is selected, pytest runs through the existing
explicit profiler launcher and records a unique artifact in the run's child
profile directory. Profiling does not reintroduce the parent's import path or
change plugin selection, native arguments, or validation deadlines.
The shared profiler clock checkpoints measured progress on SIGTERM, then restores
and delegates the previous native termination handling. Timed-out or signalled
children therefore remain failures with their original outcomes; a partial profile
does not become execution-completion evidence.
All profiler output paths use one stdlib-only atomic publisher: native marshal
data is staged on the destination filesystem, flushed and replaced atomically.
An interrupted write preserves the previous readable profile. Corruption still
fails the report reader explicitly; neither profiling nor reporting skips it.
The infrastructure CLI profiler starts before importing its public CLI facade.
Each completed invocation retains a uniquely named raw profile beside the latest
profile through that same publisher. It also retains the previous completed
artifact before replacing the latest path, including profiles from older launchers
that did not yet retain per-invocation artifacts. Termination checkpoints have their own
invocation-owned artifact and never overwrite the last completed profile.
Make parsing, guards, hooks and subprocess internals remain outside that Python
window, so comparable generation measurements also record external elapsed time.

The root facade export rule preserves literal tuple values and order while removing
an unnecessary type-only annotation dependency. It does not change classes, aliases
or inheritance, and it does not rewrite initializer projections.

`GateExecution.issues` retains each finding's original file, position, rule, message,
and severity. SARIF reports each finding at its native level. Raw scanner output
remains available on the live execution and is published verbatim once at
`raw_receipt`; serialized execution summaries retain that receipt and all issues
without embedding the native output again. Receipt consumers read the original
file when they need its bytes. This prevents large native source excerpts from
being duplicated during SARIF publication and consumption. A passing gate
therefore proves both the scanner contract and zero rule findings.

The same repair validates projected Ruff first-party namespaces strictly: a malformed
value cannot be replaced with discovered namespaces. A declared empty list remains
empty; namespace discovery applies only when the list is absent. A bare Python
annotation does not replace an existing facade binding. Mypy's module-specific
`follow_untyped_imports` policy analyzes Rope's installed source without suppressing
`import-untyped`; the typed tooling policy owns both template and dependency-modernizer
projections. See the
[Mypy option contract](https://mypy.readthedocs.io/en/stable/config_file.html#follow-untyped-imports).
