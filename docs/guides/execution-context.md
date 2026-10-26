# Execution context

<!-- TOC START -->

- [Runtime is the authority](#runtime-is-the-authority)
  - [Post-install cold atomic resource ownership](#post-install-cold-atomic-resource-ownership)
  - [Native-bootstrap task route: flext-0029c](#native-bootstrap-task-route-flext-0029c)
- [Canonical architecture checkpoints](#canonical-architecture-checkpoints)
- [Namespace migration](#namespace-migration)
- [New projects](#new-projects)
- [Environment activation](#environment-activation)
- [Dependency locks](#dependency-locks)
- [Runtime environment](#runtime-environment)
  - [Check engine contract](#check-engine-contract)
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
- [Workspace snapshot and analysis engine](#workspace-snapshot-and-analysis-engine)
  - [Profiling a root verb](#profiling-a-root-verb)

<!-- TOC END -->

## Runtime is the authority

### Post-install cold atomic resource ownership

The SDK CLI owns atomic IO. The post-install authenticated import guard consumes
its existing native `atomic_file_state` implementation before framework imports,
not an Infra-local reader. The declared stdlib closure comprises `atomic_file_state`,
`atomic_file_read`, `atomic_file_descriptor`, `atomic_parent_descriptor`,
`atomic_parent_failure` and `atomic_file_path`. Public SDK wrappers construct typed
states and receipts from the original native capture without rereading it.

Resource declarations explicitly identify their package owner and source closure.
Resolve that package through the existing `declared_package_dir` source boundary,
without importing package initializers, parent-root traversal or checkout discovery.
Rendering captures every original source state, and publication retains the closure
beside the primary resource witness. A cold projection may use its own explicit
bootstrap namespace and the original relative-import sources; it must not fabricate
an initialized SDK package or duplicate the IO implementation. Ordinary SDK import
semantics and backend descriptor identity remain unchanged.

The approved `flext-0029c` cutover below supersedes the `flext-2e7wy.1`
pre-install resource proposal and its HOLD. Do not enroll
`validate/native_bootstrap.py`, a copied bootstrap destination or supplemental
setup dependency group to restore that admission path. Original captured bytes,
source currentness and atomic-reader handoff remain obligations of the actual
post-install guard and its consumer. They do not authorize an authored operation
before native provisioning or authenticate a preceding installation. This ownership
contract is not implementation or runtime acceptance evidence.

### Native-bootstrap task route: flext-0029c

For `flext-0029c` only, diagnosis, real runtime, refactoring and applicable gates
use the **direct public `flext-infra` CLI**. Make integration comes **last**, after
the native public path is proven. This overrides older Make-only instructions for
this task, not the command policy for other projects or work. The
[local FLEXT law](../../../.agents/skills/flext-law/SKILL.md#sources-generation-and-commands)
records this bounded exception; [parent ADR-010](../../../docs/architecture/adr/010-unified-project-standardization-via-codegen.md#2-common-verb-surface-for-every-project)
retains the common lifecycle contract. Reuse existing public operations and their
typed owners, not raw tools, private-module execution or a second dispatcher.

The direct native lock-writing operation is
`flext-infra deps upgrade-lock --repository-root <root>` at the dependency composition
root. It delegates to managed uv without generation, installation or another resolver.
Installed `workspace verify-lock` delegates freshness and closure checks to native
`uv lock --check`, not an Infra marker evaluator or graph walker. These commands remove
inherited project/interpreter selectors through `make.native_environment_unset` and
pass the elected root and interpreter explicitly. Verification does not rewrite locks.
The new upgrade route remains a target until native help and execution prove it.

Bootstrap rollout uses the existing declared `codegen generate` surfaces for makefile,
pyproject, mise-config, envrc and workflows. Each retains normal native admission and
publication. Component publication does not replace full generation acceptance or
justify a speed claim against a larger workload. The input-stage log includes its
native PID so profile/process evidence is bound to that invocation, not a shared
latest-artifact filename.

The operator approved one narrow pre-proof QA change: expose a named prerequisite-only
stage at the existing Docker proof template owner. It contains the declared operating
system packages and runtime user, without Python, Mise, uv or warmed project caches.
Native Docker may select that stage to run the real generated Makefile against an
isolated candidate. Do not change test cases, assertions or expected results until the
direct subsystem and cold-bootstrap executions have succeeded. This stage is a host
prerequisite, not a second installer or an exception to runtime-first acceptance.

Before worker coding, align the affected authored documentation and local route
with canonical `~/agents/rules/architecture/engineering-core.md`,
`~/agents/rules/testing/observable-runtime.md` and the canonical `make-check` and
`verification-loop` skill sources. Do not edit installed `~/.agents/` copies or
duplicate universal rule bodies. Establish the actual public runtime contract,
repair its existing owner and prove the real consumer before changing tests;
tests and gates confirm behavior rather than define it.

**Approved native cutover (`flext-0029c`).** Provisioning uses native Mise and uv,
not a custom Python bootstrap or its translation into AWK, shell, Taplo or another
lock/installer parser. Acquire Mise through its official installation mechanism;
Mise interprets its own configuration and lock and provisions Python and uv.
Native uv project/workspace discovery then runs `uv sync --frozen` into the
runtime owner's physical `.venv`. No authored Python script, inline admission,
copied bootstrap resource or installed FLEXT operation runs before provisioning
succeeds. Python executed by uv's native build backend is package installation,
not an authored bootstrap. Make sequences native operations and preserves failures.
`mise exec` owns the lifecycle's tool environment and `PATH`; Make must not replace
that result with the caller's pre-execution path. UV owns creation of `.venv`.
The shared native environment boundary removes an inherited
`MISE_PYTHON_UV_VENV_AUTO` request so executable discovery cannot start a second
environment creator. Acquisition passes only options supported by the official
installer; its native temporary-file defaults remain tool-owned.

Native executable discovery uses `mise which <binary>` in the authenticated
configuration root with locked mode retained. It must not turn the resolved active
version into `--tool <selector>@<version>`: that is a new command-line request,
not the original configured request and its lock binding. In particular, a tool
declared `latest` and already installed from its lock must remain discoverable
before upgrade advances that lock. Make, its shared runtime reader, setup and
direnv consume the same configured native selection without a host-PATH fallback,
custom lock parser or second resolver. Setup always bootstraps and never fails on
lock drift (operator order 2026-10-24): `uv sync --frozen` installs the committed
`uv.lock` without re-resolving or rewriting it, and plain `mise install` honors
every `mise.lock` entry and records only missing ones. Check reports drift through
`uv lock --check`; upgrade alone advances versions and writes the native locks.
`deps upgrade-lock` also owns the Mise half, in the same single pass over the
runtime root and every declared member: each governed repository renders its own
`.mise.toml` and commits its own `mise.lock`, and Mise resolves a member's tools
from the member's lock. For each of them, native `mise lock --bump --dry-run
--json` resolves the moving requests and names the tools whose locked version
would change, without downloading artifacts. Only those tools, plus any locked
tool missing a declared platform, are passed to `mise lock --bump <tool>…`, which
locks and verifies their provenance for every declared platform. An unchanged
upgrade fetches nothing beyond version resolution. Plain `mise lock` with no tool
arguments would refresh every locked entry and re-download each provenance
artifact, so it is never used. Neither command installs tools; setup consumes
the resulting lock.
An owning facade composes a declared component from its source module, not a stale
generated package export that prevents the generator itself from importing. Keep
the public facade and component behavior unchanged; regenerate package exports
through their owner rather than hand-editing a generated initializer.

The root has one native uv workspace and lock. Root CI checks out its declared
submodules and installs that same workspace noneditable; `--no-editable` changes
installation mode, not dependency origins. Independent checkouts retain their own
native project contracts. Their locks pin the FLEXT distributions they consume.
To develop against a FLEXT checkout, a standalone member or external consumer runs
`make setup FLEXT=<path>` (operator ruling 2026-10-24, tracker memory
`operator-ruling-2026-10-24-setup-flext-editable-param`). After the frozen sync,
setup reinstalls as editable, into that repository's own physical environment,
every FLEXT distribution it installed from its lock and that the workspace at
`<path>` provides (its root and each `.gitmodules` member). The typed owner
`flext-infra workspace flext-editable` performs that selection and records it in
`.reports/setup-operations/flext-editable-selection.json` under the runtime root.
The environment provenance gate admits an editable FLEXT distribution only when
that receipt names it and the run is not CI. A plain `make setup` restores the
locked installs and removes the receipt, and CI rejects the input. This replaces
`FLEXT_INFRA_EDITABLE_SUPPLIER_ROOT`, persisted supplier selection and the synthetic
local/standalone/editable resolver, which are retired without a compatibility route.

Native source declarations and locked consistency are the approved provisioning
trust boundary. The stronger independently selected-supplier pre-install admission
is explicitly retired, not claimed equivalent to uv's lock check. Ordinary installed
Infra environment, lock and provenance checks run only after provision; they cannot
retroactively authenticate the preceding installation. Keep the real authenticated
import guard as a separate runtime concern: preserve original captured source bytes,
stale-pyc rejection, changed-source refusal, atomic-reader handoff and original
tracebacks through its actual producer consumer, not a warm import smoke alone.

The independently consumed post-install stdlib guard hands off as soon as safe to
the existing typed `workspace/environment_provenance`, `lock_completeness`,
`detector` and `environment` owners. Coordinate wider generated Make/direnv
installer integration with `flext-itpd1.4.13`. Repeat bounded native runtime QA
after causal repairs and for convergence; never retry an unchanged failure.
Prove real subsystem behavior and cold native bootstrap before changing tests,
then run applicable gates and revalidate final Make integration on that candidate.
No mocks, fakes, tautologies, policy hardcodes, fallback or duplicate owner are
admitted. Splitting a god component into files alone does not repair ownership.

**Approved public QA target — not yet runtime-proven:**
`flext-infra validate producer --repository-root ROOT` is a thin read-only
diagnostic that calls the existing `FlextInfraValidateFreshImport.capture_producer`
with the real bound `FlextInfraSemanticPublication.publish_semantic_analyses` as
data; it never invokes publication. Reuse `WorkspaceRequest`,
`CodegenPhaseAnalysis` and their existing capture, currentness and native original
payload contracts. Exercise isolated bootstrap, producer capture, original-source
receipts and JSON, the cold worker and `producer_current`, preserving authenticated
original bytes and letting original failures escape. Accept no caller-authored
receipts or maps, synthetic rename, fake candidate or new proof algorithm. This
target is not a warm-import smoke, setup or native Mise/uv installation, lock
resolution, actual publication, race coverage or full-fleet proof. It remains an
approved target until the parent executes the real public command successfully;
documentation alignment alone claims neither implementation nor diagnostic success.
Native receiver admission failures may add a callback-free ownership breadcrumb from
the already recorded incoming edge, binding, supplier, source and first-visit alias
chain. This diagnostic metadata is not source authority or native-state admission.
An exception note preserves the original exception type, arguments, cause and
traceback; it never renders the receiver or invokes its callbacks.

Implementation is approved, with documentation aligned before worker code and real
public runtime before test changes. This documentation slice changes no production
Python, templates, configuration or tests and executes no Make, runtime or publisher.
The coordinator owns serialized runtime/gates and final Make integration. Generated
README and installed governance projections remain unchanged here; their owners are
identified below. Historical plan reconciliation remains a later serial activity;
this slice deletes no plan. This contract records the target, not implemented or
validated provisioning, delivered governance, or Bead closure.

Shared defaults own ordinary FLEXT dependency declarations; a project's codegen
input retains only its identity and genuine dependency/tool deltas. Live editable
source selection does not require clean, committed, or stationary worktrees.
Release builds instead resolve the selected project's committed `HEAD` once and
extract that exact SHA through `git archive`; the build receipt records the SHA
and commit epoch. Shared working-tree, index, and untracked changes remain in place
and never become source inputs. In particular, checkout `dist/` files are not
copied into the audited stage. Required build assets must belong to the committed
source or be produced by its build backend inside the isolated build, not injected
from unauthenticated checkout outputs. Release metadata and snapshotted build
policy retain their existing explicit rendering and attestation boundaries.
Release-version ownership is selected by `LANE_CHECKPOINT_REF`, an existing
dedicated Git checkpoint reference, not caller-authored receipt JSON. The public
`workspace lane-ownership` command reconstructs its original metadata and index
parent, verifies the full repository scope, live remote retention, and inclusion
in the current integration tip, then emits the typed receipt. The generated Make
recipe passes only the checkpoint selector to the release API composition root,
which resolves that same producer and passes its validated receipt by reference;
complete checkpoint metadata never travels in a command-line argument.
It never captures, publishes, integrates, switches branches, or modifies current
staged, unstaged, or untracked work. A checkpoint from a different repository
identity, an unpublished capture, or an unintegrated capture is refused. Receipt
production does not waive the separate lane-creation or produced-path admission
contracts; shared-WIP publication still requires authenticated producer outputs.
The scoped Git API separates `prepare_publication`, `publication_scope`, and
`commit_publications`. Its live admission binds the prior ownership, integration
tip, caller ref and exact original index. Native producers retain their original
`CodegenPhaseOutcome` objects; the existing publication authority verifies their
before/after lineage before the Git owner consumes any output. Only declared
effects enter the alternate index. A versioned target whose original file or
staged entry differs from the selected base is an affected-path conflict, not
permission to publish the whole pre-existing file. Runtime-local index retirement
also uses the scoped index and an explicit native `index_before` witness; it does
not ignore a path by name or modify the shared index. The owned ref is published
through a native ref transaction after hook, original-index and fresh-tip checks,
without switching the caller's checkout. New or copied admission/receipt models
cannot replace the original live authority.
The release workflow dispatch selects exactly one `tag` or `checkpoint_ref`.
Tag dispatch retains the existing publication path. Checkpoint dispatch validates
the event's exact SHA through canonical CI, then runs versioning only, with the
selector transported as environment data. Push versioning selects an explicit
repository `LANE_CHECKPOINT_REF` variable; a no-op needs no ownership mutation.
The lifecycle separates three explicit operations: generation projects native
declarations from their owners, explicit upgrade resolves and writes locks, and
setup installs them without rewriting manifests, locks, source pins or versions.
Ship the native declarations and locks required by a fresh checkout: setup must
not require Python generation of a copied admission resource or synthetic resolver.
It neither generates missing inputs nor relocks stale ones. Missing members,
invalid sources, stale locks and native acquisition failures retain their original
cause and stop the operation without source substitution, retry or later success.
Direnv activates the provisioned native environment; it does not decode or persist
an external supplier selection or run setup admission.

Generation retains the first failed native phase even when that failure is a
structured diagnostic rather than a raised exception. A later docs or receipt
exception cannot replace it. Documentation for a newly admitted project depends
on its authenticated published metadata: when that metadata was not published,
the docs node is blocked by the original failure, not executed against an absent
project and reported as an unrelated selector error.
Each independent consumer keeps its own physical `.venv`; attached members share
their containing workspace's environment. Native source declarations never lend a
supplier's environment. Refuse symlinked or foreign environments and serialize
effects on the same physical runtime without requiring unrelated WIP to stop.

Required consumer TOML is read through the canonical typed document reader. A
syntax failure retains the native parser exception and exact declaration path;
it never becomes an optional missing document, an empty mapping or a generic
pathless validation message. Diagnostics identify the physical failing input
before attributing it to a merge, source epoch or supplier. Never repair an
unrelated active merge or select another parser to make that observation pass.

These are the required boundaries for the in-progress lifecycle cutover; the active
Bead owns current implementation and acceptance receipts. Their documentation is
not a claim that every existing generated consumer already enforces them. Consult
and reconcile the applicable guide, ADR, instructions and canonical skills before
each code change. Only after implementing the real runtime behavior are tests
updated and run to validate it, without mocks, tautologies or policy hardcodes.

Resolve the test entry from the selected repository's current native help. The
current generated catalog declares `make tests`, without file or match inputs;
it executes its applicable persistent-testmon selection once. Historical commands
are receipts for their own source epochs, not aliases or executable instructions
for this catalog. An undeclared old target is corrected at the documentation
owner, never bypassed through raw pytest or another dispatcher.

The Make catalog owns public builtin names, descriptions, profile applicability and
named inputs. General help and builtin `OPTIONS=Y`/`HELP=Y` views project those inputs
without invoking the operation. Profiling and reports belong to their existing
operation engines, not additional public lifecycle aliases. Domain selectors remain
supported only where explicitly declared by the domain command registry.
The catalog/help cutover is tracked in `algar-723.1.3`; runtime and gate receipts,
not this required contract, establish which generated consumers have adopted it.

Generated README quality guidance is owned by `DocumentationText.QUALITY_BODY`
in `src/flext_infra/_constants/docs.py`, consumed by the `quality_gates` macro in
`templates/docs/_macros.md.j2`. Both languages point to `make help` for the current
command surface rather than copying a verb list. Each verb performs only its
declared operation; `make check` validates without applying repairs. Change this
authored contract before its presentation text, then publish through the docs owner,
never by editing a generated README.

The public `FlextInfraDocGenerator.prepare_bundle()` and `plan_files(bundle)`
surfaces expose the captured render and destination plans before publication.
Inspect the entire inventory: `docs generate` also plans documentation indexes,
guides, MkDocs configuration, presentation metadata and stale generated API removal;
`--output-dir` is not a README destination filter. A README-only authorization does
not admit that complete bundle. If the declared public operation cannot isolate
the authorized destinations, leave projections unchanged and return the planned
scope for an owner-level decision; do not invent a CLI selector or another renderer.

Workflow admission errors report the rejected rows' declared input names and
profile coverage against the typed required profile universe. A verb name alone
does not identify an operation selector or a missing profile. Preserve the strict
predicate and inspect its actual inputs rather than disabling admission to proceed.

For a declared script dispatcher, Make transports `WHAT` as literal environment
data and invokes that dispatcher exactly once. The dispatcher owns discovery,
selection, validation and its original exit status. Make does not interpolate the
selector into shell source, scan script roots, select an `all.sh` substitute or
probe selector-named private targets. Explicit verb-level custom handlers retain
their declared hook contract; they are not a second selector registry.

Facade planning preserves the complete import identity elected by the project
discovery owner, including nested and namespace packages. A directory basename is
not a module identity: declarations, proposed imports, C3 references and codemod
contexts must use the same qualified package. Generation must not create package
initializers or relax Rope's class boundary to compensate for a truncated name.

Type-facade admission evaluates the class, exports and alias bindings from one
parsed view of the planned source. Node identity from a different parse cannot
establish that the owner class is an unsupported declaration. Rebinding imports
must keep both the source text and its syntax-node offsets consistent.

Generation, structural modification, dependency resolution and authored repairs
have separate operation owners. The retired `codegen pipeline` route must not
combine those operations. `gen` and `mod` use the existing semantic planners and
publisher for their own complete changes, including dependent generated exports;
neither invokes another public lifecycle verb. Their canonical components remain
available through their respective owners, without a second orchestration route.
All declared checking gates belong to `check`; a separate public-verb exclusion
map must not remove gates from that operation. Pytest's existing typed runner owns
its process deadline. The Make projection passes that policy once, without an
additional outer timeout or independent profiling-report location.

The existing `refactor rename-plan` CLI action accepts `SemanticRenameSelections`
JSON through `--decisions`. A selection identifies the introducing class,
callable, or module and its intended name. `consumer_roots` is an optional JSON
array of absolute checkout roots for this invocation, not a persistent rename
catalog. The containing workspace and its declared `.gitmodules` members are
discovered automatically, including invocations from one attached member. An
invocation at a workspace root elects every declared member; a requested path that
the election ignores (outside every declared member, or excluded by the governed
inventory) fails with an error naming that path instead of being dropped silently.
External consumers are explicit typed run inputs, not reverse-dependency guesses
or an implicit host-wide inventory. Standalone invocations retain their own scope
plus those declared consumers.

The analysis engine's native multi-project refactoring, reached only through the
`u.Infra` refactoring owner, computes every elected project's changes before
publication. Module selections use the native nullable
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

For exact file relocation, the public immutable SDK call is
`u.Infra.plan_module_move(project, source_file, destination_file=target_file,
sources=sources, source_states=states)`. Supply the complete authenticated Python
inventory from the elected project and its original atomic states. Exactly one
destination form is required. The existing positional directory form remains
class-only; the exact-file form uses native resource changes for complete mixed
modules, preserving functions, constants, aliases, class bodies and inheritance.
Quoted type positions are selected by original native module identity and the
existing quoted-type owner, with native import binding election. Ordinary
string payloads are not filename replacements.

No directory, module or Rope metadata is created while planning. Native rename
intermediates are lookup-only and never published; an occupied intermediate is
an explicit rejection, not overwritten or assigned an arbitrary alternate name.
The returned `CodegenFilePlan` effects join the existing semantic publication
candidate together with lazy-facade projections. A new package initializer is
only a virtual lookup resource here, not an authored competing export owner.
The existing public `flext-infra refactor move-module` operation exposes this
path with `--repository-root`, `--source-file` and `--destination-file`. Exactly
one of `--destination-file` and the existing `--destination-directory` is required.
The directory mode retains its existing mutable contract. Exact-file mode reads
the native project's complete Python inventory through atomic file states, rejects
foreign owners/effects, and delegates to the public semantic publisher with the
declared root as its projection scope and the semantic dependency group. That
declared root must also match the native Rope repository root, never an
implicitly elected ancestor of a narrower caller scope. The
publisher plans lazy/facade outputs against the proposed graph, then prepares,
validates and publishes the complete group. No raw Rope effects or handwritten
initializers are applied in this mode. Its typed receipt is the existing
`p.Result[tuple[Path, ...]]` published-path result; the CLI preserves its successful
boolean result and plain absolute destination-path output after acceptance.
Neither overload automatically discovers a fleet layout migration or adds a new
Make selector; `make mod` consumers still elect their semantic destinations.

Class relocation derives module names without a leading underscore, including
when the original module or class is private. Family destinations retain their
declared private facade directory; privacy belongs to that directory, not the
Python module filename.

The exact-file relocation overload does not move package directories. Native
string payloads and framework registration are not implicitly renamed; they
remain subject to the existing consumer validation and declaration owners.

Facade composition retains direct imports of discovered component declarations;
the renderer does not redirect them through private-family package exports.
Existing behavioral base chains retain their native C3 ordering. This is not a
class-only export cutover: qualifying component consumers through the facade
class and retiring module/package exports must join the same authenticated
semantic candidate, including lazy-init projections, before publication. Removing
barrels or behavioral bases independently would break existing consumers.

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
base. Verify the selected executable and installed identity through the documented
workspace runtime operations; both must match the code under validation. An earlier
log or an installation from a parent
workspace does not certify a standalone checkout. Work on the freshly fetched
integration tip of every repository involved.

## Canonical architecture checkpoints

The public `mod` handler is inherited by the API from
`services/mod.py`; `FlextInfraCodemodBatchApply` remains its sole execution
engine. The CLI validates the request with `m.Infra.ModCommand`, while consumers
use `p.Infra.ModRequest` and supply an explicit `p.Infra.ModProgress` port. The
API's existing preview and workspace capabilities provide the dependencies by
MRO; there is no second loop in the handler.

A refactoring workspace session is a view over the bound workspace snapshot's
analysis engine and its file listing (see
[Workspace snapshot and analysis engine](#workspace-snapshot-and-analysis-engine));
it opens no project of its own while a snapshot is bound. Sessions are owned by
their invocation and keep their logical roots and teardown isolated, even when they
read one structural workspace. Borrowed projects remain owned by their caller. Content snapshots
and their authenticated indexes retain their source epoch; a process-global
registry is not a substitute for the existing invocation-scoped DI.

Publication verification admits the complete cohort of original receipt identities
at its authenticated Rope read owner before observing current sources. Only that
owner allocates fresh directory and topology observations for one verification
boundary. Each receipt retains its full input, negative-query, membership, ancestry
and consumed-effect comparisons, in native file-CAS/query/declaration order.
Caller-supplied observations, copied receipts, foreign issuers and reuse across
proposed overlays or verification boundaries are not admitted. Replay attributes
the same issuer's original closure; verification does not reseal or copy receipts.

A successfully completed consumption scope that only replays one identical, already
admitted original receipt may retain that receipt and its unchanged effect closure
by reference. It does not rebuild snapshots, revalidate the same model graph, or issue
that identity again. Admission still precedes attribution, and an active consumer is
required. Any independent observation, different receipt, added effect, changed overlay
or changed issuance context uses the existing complete accumulation/sealing path.
Failed scopes publish no successful receipt, and physical freshness verification at
publication remains mandatory. This removes duplicate materialization, not validation
at an untrusted boundary or the source/negative-query checks.

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
base order declared in their configured private family. Protocol facade projection
composes authored consumer-owned `p` contracts through the same native declaration
and MRO owners; it never copies model fields or public signatures into a second
typing surface. A dependency port declares only capabilities its consumers use.
Existing-project conformance and new-project scaffolding generate ordinary facades
and lazy exports. The one exception is the model→protocol stage, which the operator
ordered restored and run on every `make gen` (2026-10-24: "fazer os protocolos de
forma automática por flext-infra (já existe e tem que estar ativo e sempre rodar no
make)"). Its generated `p.*` protocols are projections of the declared models, not
authored mirrors. Restoration is tracked by bead `flext-vjj1s.8`; until it lands, no
such stage exists. The utility path delegates
directly to the declaration planner. Static and runtime consumer checks retain
their own import-failure verdicts.
Generated protocol and model namespace assignments are derived output, not new
contract declarations. When an assignment resolves to an exact inherited class,
projection removes that binding and inherits the canonical private owners in C3
order, including their declared overrides. A stale renamed alias cannot publish
itself or shadow a different inherited contract. The generated ownership marker
and native class identity are both required; unrelated namespace members remain
unchanged, and contradictory authored class bindings still fail before publication.
This also applies to a generated, declaration-only subclass alias whose name is
already supplied by a canonical inherited class. The inherited declaring owner
wins even when the old alias names a retired top-level model; the generator
removes the obsolete alias instead of turning the facade into another model.
An alias in a generated namespace is also obsolete when its receiver is an exact
inherited owner and that owner no longer provides the referenced attribute. Remove
that proven-invalid projection instead of retaining it or adding a compatibility
declaration; an unrelated unresolved receiver is not evidence for deletion.
For mixed constants namespaces, publishing an owner as a named child does not
replace composition of its members alongside other namespace providers. Preserve
both access paths; enum declarations remain whole-class publications, not bases.
Whole-class publications also retain the upstream namespace inherited by their
facade; publishing local owners must not shadow its existing methods or domains.
Retained class-field expressions are source projected by that same facade renderer.
An absent intermediate attribute may be removed only when its name uniquely elects
an inherited native class owner and the following member has the identical native
declaration binding on that owner and the receiving namespace. Existing nested
publications, ambiguous owners, overrides and unrelated unresolved attributes stay
unchanged; their failures are not suppressed. This operation resolves identifier
chains only, never arbitrary RHS evaluation, and leaves generated-source exclusions
and the existing publication path unchanged.
The existing per-identity UP040 exemption authenticates the facade through its
explicitly exported family alias and local class identity, using the same native
publication owner as namespace discovery, not a canonical module filename. Only
PEP 613 class publications on that elected facade or its nested namespace qualify;
the TypeAlias import, reported location and native RHS class checks remain required.
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
`make tests` uses the persistent Testmon owner's native incremental selection over
the complete applicable population. The 2026-10-26 operator order supersedes the
forced complete-run behavior: unchanged tests are not rerun merely because the
verb was invoked again. Selection and execution share one persistent database and
aggregate deadline, with no second execution pass. Every execution retains the
same-scope green-check prerequisite. The common catalog has no manual file selector
or separate complete-suite alias. Fleet acceptance requires global Ruff, Pyrefly
and pytest evidence; a member-only receipt never claims fleet completion.

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
`make gen`, `make check`, `make tests`, and `make build`. Its physical environment
belongs to the generated repository.

First generation authenticates the staged scaffold through the explicitly declared
executor repository's provisioned physical runtime. The executor owns generation
tools before the destination exists; this does not provision, link, or lend its
environment to the generated checkout. The destination's own runtime is provisioned
after generation by its `make setup`. Existing-project conformance continues to
authenticate each consumer through that consumer's native runtime owner. Both
paths require a physical environment and retain interpreter, directory-identity,
and sealed-source authentication.

## Environment activation

The `make setup` contract includes approving the `.envrc` with `direnv allow`.
Make verbs declare their activation requirement in `make.verbs`; activation is
required by default before handlers and hooks. Generation and its footprint
inspection consume the declared physical interpreter and verify its environment
directly, so they can repair generated activation inputs. The `gen` contract requires
passing its validated `CodegenGenerateRequest` by reference directly to the single
projection executor, including guarded `.envrc` publication. It must not construct
a `CodegenConformRequest` in `APPLY` mode or use a `generation_only` flag. Planning,
publication, physical CAS and staged validation retain one shared implementation.
Only Conform owns mode, declaration migration, conformance observation, Beads
identity seeding and routes, and direnv authorization. Preserve the existing family
names; this contract does not establish implementation or runtime acceptance.
A declared `_custom-gen` replaces the generation handler.
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

The packaging owner never force-includes a file at an import package's installed
location. Hatch copies forced files into editable wheels too, which installs a
stale namespace portion beside the editable source: static resolvers see it and
runtime resource lookups read the copy instead of the live tree. A package's
`config/` defaults live in `src/<pkg>/config/` and ship once through the ordinary
`only-include` selection of `src/<pkg>`; editable installs read that source
directly. Declared repository data paths ship through `sources` remapping into the
package. The producer `pyproject.toml` ships as wheel `extra-metadata`, installed
at `<dist>.dist-info/extra_metadata/pyproject.toml` in standard and editable wheels
alike. The sdist retains every original source. Configuration values remain owned
by the YAML sources, not by the manifest.

`tool.hatch.build` and `tool.uv.cache-keys` are generator-owned pyproject tables,
declared once in the pyproject ownership `conflict_sections`. Generation and the
modernizer read that same declaration and replace both tables from the packaging
declarations, so a retired or authored entry leaves on the next `make gen` or
`deps modernize`.
Migration validates these inputs before publishing its declaration. A legacy
manifest explicitly selected as distribution data retains its original bytes;
retaining that resource does not make it a runtime configuration source again.
Scaffold directory preparation applies only before a project's `pyproject.toml`
exists, never to an existing repository's prospective template directories.

Rope qualification reads a receipt only after its consumption context closes,
while the source view remains open. Publication effects use the same configured
source-election exclusions as the captured membership query; explicit path reads
and original input states remain authenticated by the unchanged native observer.

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
consumed executable sources and provider metadata. Namespace-only class globals retain
storage-type identity; instruction-selected constructor, call and member edges elect execution.
Explicit inventories and resource trees retain membership checks; unrelated files are excluded.

Rope source-query ownership comes from the original declared source folders and
native dependency import roots, with the most specific elected owner taking
precedence. Explicit managed effects retain their original destination witnesses.
A dependency runtime nested below the checkout root has the same ownership as an
external dependency runtime; lexical containment alone does not make its module
probes project-source elections. Actual dependency payload reads still retain
immutable file receipts, including metadata, and changed consumed bytes fail
verification in either layout. Physical ancestry and symlink guards for declared
sources remain unchanged.

The project composes the native resource/module/layout interface through MRO;
its authenticated source epoch remains the public consumer boundary. Native
initialization uses the exact upstream class descriptor through the consumed
initializer protocol, including Rope's documented `ropefolder=None` contract.
The physical root and injected filesystem identity are checked after initialization;
the protocol alone is not evidence of the vendor's signature or runtime behavior.

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

Generation projects the declared Python requirements before upgrade resolves
dependency locks. This keeps workspace members on one declared source identity
when a Git dependency changes; installing from conflicting stale projections is
a failure. The internal `codegen init` adapter publishes the canonical Make
bootstrap when an existing project's dispatcher predates that lifecycle. It
does not add an `initialize` Make verb.

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
Setup resolves the executable through `mise which python` at the environment-sync
boundary and passes that exact path to uv. Upgrade consumes the declared resolver
runtime without synchronizing the physical environment. Recursive Make calls do
not require a caller-provided `SETUP_PYTHON` environment variable.
Make provisioning and the shared workspace reader restrict global and system
configuration discovery to the elected runtime's `.mise` directory; unrelated
host tool declarations never belong to project provisioning. Direnv activation
also exposes operator-owned host tools, without installing or resolving them.

Setup provisions the available frozen toolchain without writing `mise.lock`;
check owns its pin and completeness verdicts. `make upg` resolves the declared
manifest and writes its lock. Installing the recorded release belongs to setup.
Generation projects the declared Mise configuration without resolving a lock or
regenerating unrelated project files.

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

An associated project installs from the lock and physical environment of its native
UV workspace within the authenticated Git scope, while still tracking its own
`uv.lock` for standalone installs and frozen CI (see below). Its `make setup` and
`make upg` delegate full toolchain provisioning and dependency resolution to that root.
A standalone checkout owns those operations itself. Only `upg` resolves moving
Git branches; `setup` installs the
exact committed lock without changing it.

`help` and its catalog submake require no provisioned runtime; `.envrc` only observes
the runtime association. Setup owns official Mise acquisition and locked native
tool provisioning in the authenticated bootstrap scope. Provisioned native UV
then elects the runtime owner before normal delegation. Upgrade requires those
tools and never installs its workspace reader. CI retains native workspace
election rather than selecting standalone execution from a hosted-provider flag.

The approved native flow uses one root uv workspace in local execution and root
CI; lock ownership follows ADR-030 (below). CI checks out declared submodules
and installs noneditably; it does not select a checkout-free standalone
resolver. Independent repositories keep their own native contracts. Retire synthetic
`make.uv_resolution` views and their hosted-selection consumers rather than
maintaining both routes. Native uv owns
workspace election; the existing installed detector exposes the resulting typed
context without duplicating uv's resolver. Each runtime root owns its physical
`.venv`; no second installer or post-install editable overlay is introduced.

The project's authored dependency categories retain their identity. Native
resolution consumes those declarations without promoting dev or examples
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

One `make upg` resolves the declared native project/workspace and tool manifests.
Attached members delegate resolution to their elected workspace; standalone
repositories own their own locks. Lock ownership is
[ADR-030](../../../docs/architecture/adr/030-member-locks-composition-upg-guard.md)
(tracker memory `operator-ruling-2026-10-25-member-locks-uv-mise-upg-guard`), which
supersedes the earlier same-day "only the root lock" decision: member `uv.lock` and
`mise.lock` are kept and formed by each member's own declarations, the workspace
lock is their composition, only `make upg` writes locks, and exact SHAs pin the
dependency hierarchy. Workspace `make upg` still processes every member in one pass
(operator ruling 2026-10-25): its guard first, then members in `.gitmodules` order,
then the root (uv documents that `--upgrade` implies `--refresh`). The guard (uv
only, in the upgrade preflight) requires, for an editable workspace, every governed
repository committed and each gitlink equal to its member's HEAD, and, for a
standalone checkout with an external editable install, a clean external checkout
whose HEAD the consumer's committed gitlink or locked SHA records. The guard and the
composition mechanism are a design whose verification questions are settled but
whose implementation is pending (ADR-030 "Proposed design"); the running upgrade
still relocks the root workspace in one native `uv lock --upgrade`. CI installs
frozen locks and never relocks (tracker memory
`operator-ruling-2026-10-24-ci-frozen-homologated-locks`); in the ADR-030 target,
root CI installs the composed root lock, member CI the member's own committed lock,
and a member checked out without its workspace installs from its own lock. Pins of
internal Git requirements follow the
line each member's `pyproject.toml` declares: the manifest keeps the Git URL and
the lock pins its exact SHA (tracker memory
`operator-ruling-2026-10-24-lock-sha-pyproject-url-waves`). An
internal dependency may require the locking member back by its own Git URL, which
native uv cannot reconcile with the local project. The pyproject generator derives
one internal override per declared internal Git URL requirement of the member
(runtime, optional or development) at exactly that URL, and emits one scoped
`[tool.uv] exclude-dependencies` entry per internal override, removing only that
distribution's requirement on the member. A repository declares an internal override
in `toolchain.uv_override_dependencies` only when the distribution is not its own
requirement and reaches it transitively. An entry does nothing where the distribution
does not require the member; the workspace root, which lowers members through native
workspace sources, derives none.
Each owner supplies its declared paths and
source identities. An editable supplier supplies sources, never its physical
environment. Upgrade does not generate manifests or Makefiles, install tools,
synchronize an environment or invoke another lifecycle operation.

When declarations change, explicitly generate their projections, resolve their
locks and install the frozen resolution through their respective verbs. A missing
generation input fails its prerequisite instead of triggering corrective generation
inside upgrade. The declared lock platforms and release cooldown remain owned by
the typed toolchain. Consumer convergence and runtime acceptance are tracked
separately in `algar-723.1`; this contract is not a publication receipt.

`codegen.scaffold.project.retired_dev` declares development distributions that
must no longer reach managed `dev` or `codegen` groups. Conformance filters them
from existing groups and member contributions;
declaring the same distribution as a required development floor fails. Retire
obsolete typing stubs here when their runtime SDK supplies inline typing, then
regenerate, run `make upg` to resolve locks, and run setup to install that resolution.
Member contributions include the requirements parsed from captured declarations;
the composed development group uses the same retirement filter.
Do not uninstall packages manually or weaken the type checker.

Third-party typing comes from the library itself (inline annotations or
`py.typed`) or from a published `types-*`/`*-stubs` distribution declared as a
dependency. No local stub package is generated. Pyright's
`reportMissingTypeStubs` is the single checker exception (tracker memory
`operator-ruling-20261022-missing-type-stubs`): `config/tooling.yaml` declares
it once under `settings.pyright`, the pyproject projection carries it to every
member, and a project needing another value declares it in its own
`config/tooling.yaml` overlay. Pyright, Mypy (`follow_untyped_imports`) and
Pyrefly still analyze the untyped library source, and each used surface stays
typed through `p` protocols at one boundary module per library.

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

A workspace root preserves declared Git requirements and publishes its declared
package members in `[tool.uv.workspace].members`. Its `[tool.uv.sources]` entries
bind the root package, when present, and members through `workspace = true`.
Native UV owns source lowering and dependency resolution against one workspace
lock. Conflicting authored sources for a declared member fail explicitly.
Publishable members retain their package requirements for independent checkouts,
which own their native project declarations, lock and physical environment.

Development groups, included groups, extras and markers retain their declared
categories. Workspace membership does not promote packages or reciprocal development
requirements into the root's runtime dependencies. Native UV consumes these inputs
directly; generation creates no synthetic non-package identity or
local/standalone/editable resolution view.

Generation publishes the native declarations transactionally; upgrade alone resolves
their lock, and setup installs the frozen resolution into the runtime owner's
physical `.venv`. Root CI obtains the declared members and installs that same
workspace and lock noneditably. An independent checkout resolves its own declared
sources without discovering neighboring repositories or borrowing their environment.
When composition changes, regenerate its declaring owner, upgrade its lock and
install that resolution through the separate lifecycle operations.

Resolver-wide source election is explicit policy in
`Infra.codegen.toolchain.uv_override_dependencies`, not inferred from an installed
SDK or a direct requirement. The strict library, project and local config layers
append their declarations in that order. Rendering elects the last global override
for each normalized distribution and marker, preserving other marker variants and
native scoped tables. A supplier cannot replace the resolution root's global policy
for a distribution through an environment selector. The same elected policy reaches
the selected native project metadata; the workspace root owns workspace-wide UV
policy, while independent checkouts retain their own native project policy.
Unconfigured conflicting direct and transitive sources remain native UV failures.

Dependency-family provenance validates sources per normalized distribution and
marker, separately from the shared provider identity. Different distributions may
declare different explicit Git refs. Documentation governance resolves its ref from
the exact declared Infra distribution, never Core, requirement order, an installed
package or the consumer's local branch. Conflicting sources for one distribution
and marker, competing family providers, and ambiguous Infra marker variants fail
loudly. Captured documentation inputs and governance-provider authentication remain
required before publication.

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
The fixer holds the repository mutation lease, captures native repair inputs once,
revalidates every metadata, source, lock and report input, and publishes only
`project.dependencies` through the guarded TOML owner. Its receipt retains the
pre-repair diagnostic and whether publication changed the declaration. Completion
describes that repair operation, not a subsequent dependency scan or project
acceptance; independent verification runs only through an explicit check.
Unresolved plans and publication failures retain their original failure. A repair
request with a read-only context fails before scanning or writing; it never
dispatches a different operation.
The native `codegen init` adapter acts on its explicitly selected target only.
An existing project uses the bounded Makefile recovery surface and its declared
artifact dependencies. An explicit kind may author that target's declaration
through the existing guarded transaction; a conflicting kind fails.
A target without project metadata must instead pass the workspace detector's
positive new-tree admission using its own complete project, integration, kind
and dependency-provenance declarations and prepared Git checkout. That case uses
the same complete generation planner and publisher as `make gen`, with bound
collaborators from the adapter's actual tool runtime. No kind, Beads identity or
dependency provenance is synthesized. A declared new workspace member should
normally be materialized by the workspace's `make gen`.
For a standalone target without a Makefile, a preinstalled generation tool
runtime invokes `codegen init`; then the destination runs `make upg`,
`make setup` and `make gen`. Native Mise, Python and UV are prerequisites of
the generation tool runtime. Only setup creates the destination's product
environment; initialization and generation neither install nor resolve locks.
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
setup provisions dependencies. A stale Git binding requires canonical
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

Editable imports and packaged configuration share one delivery path: both resolve
from the editable source tree, so a configuration edit is live without `make setup`.
Only a declared build hook adds generated native UV cache keys, retaining UV's
ordinary project inputs plus the hook module, because the hook alone changes the
built editable artifact.

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

### Check engine contract

One `m.Infra.GateContext` carries everything an invocation shares with its gates,
built once at the check composition root and passed explicitly; no gate reads
ambient or process-global state:

- `reports_dir` and `fail_fast` are the invocation's report base and stop policy.
  `run_projects(projects, gates, ctx)` and `run_projects_report(projects, gates,
  ctx)` take them only through the context; without one the checker's defaults
  apply.
- `scope_facts` (`p.Infra.GitScopeFacts`) is the invocation's tracked Git inventory,
  read once per repository and scope. Applicability (`selected_for(project_dir,
  ctx)`), Markdown collection and doctest discovery all query it.
- `signal_wave` (`p.Cli.SignalWave`) is set only for a gate running inside a
  concurrent stage. Read-only gates of one project run concurrently, bounded by the
  memory the typed Mypy policy reserves per whole-program checker. The main thread
  owns operator-signal forwarding for the wave; every child process subscribes
  through the wave it receives, so an interrupt reaches every owned process group.
  Repairs and explicit fail-fast runs stay serial.

Every gate assembles its result through one builder: the native output receipt is
published, every finding blocks acceptance, and an undeclared native outcome is
derived from the findings and the tool verdict.

The duplication and smells gates analyse authored sources only. Generator
projections repeat their template by contract, so the generated projection surface
has one owner, derived from each projection's own generator marker and the
generated-artifact catalog, never from a hand-kept glob list. The jscpd
configuration and the rendered `qlty.toml` both consume that owner; the template a
projection comes from is measured at its source. No authored code is excluded.

Tracked Pyright configurations contain analysis policy and import roots, without
`venv` or `venvPath` bindings to the checkout that generated them. The native gate
passes the runtime owner's interpreter explicitly. Pylance uses the editor-selected
environment. Attached members share the workspace environment; independent
checkouts and worktrees own their physical environment. One tracked member
`pyproject.toml` serves both the attached and the standalone topology, so any
tracked interpreter binding would be wrong in one of them. A direct Pyright run
without the gate's interpreter binding resolves whichever interpreter its process
finds first and is therefore invalid evidence; checker results count only from the
gate's own invocation in the real tree under the project configuration.

## Mise toolchain

Mise manages itself: the generated `.mise.toml` declares the `toolchain.mise_selector`
release as a `[tools]` entry, and `mise.lock` pins it like every other tool. Setup
provisions its recorded release asset and verifies the checksum before entering
the recursive Make lifecycle. The `_setup_lifecycle`, `_setup_activated` and
`_upg_lifecycle` recipes call `SELF_MAKE` indirectly and must carry GNU Make's `+`
recipe prefix so the native jobserver descriptors reach child Make processes.
Preserve those descriptors and `MAKEFLAGS` through native Mise execution, without
another wrapper or clearing the inherited jobserver contract.
A complete self-pin does not require a host Mise.
Without that pin, setup stops before provisioning; `make upg` can establish it
using an available native Mise. Setup qualifies the final self-pin before
installing tools. Every later `mise` resolved
through the release's own shims is the pinned release, and `make audit`
(`codegen mise-proof`) fails when the running Mise differs from the lock.

The runtime's `.mise.toml` remains a native project configuration. The optional
global configuration has the distinct path `.mise/config.toml` under that same
runtime owner; its absence does not select the operator's global configuration.
Project resolution writes the project lock in project scope. It never classifies
the project manifest as global or updates unrelated host tools.

Only explicit generation publishes a changed Makefile. Upgrade consumes that
projection and never regenerates it or reinvokes itself after publication.
An older committed Makefile retains its old behavior until the canonical generator
replaces it; invoking another verb is not a repair of that projection. Separate
bootstrap launchers and lock-convergence scripts are not lifecycle owners.

`toolchain.tools` in the packaged `config/codegen.yaml` owns native tool declarations;
the toolchain model rejects a Mise `npm:` selector (ADR-025). A tool whose upstream
release metadata publishes no checksum declares `lock_checksum: false`.
ADR-025's October 9 amendment requires distributed JavaScript tools, including
FLEXT's, to use one owned Bun project, `package.json` and a frozen lock. It does not
restore Mise npm backends or retire native Node wrappers where used. Source-owner
implementation and real installed-consumer proof are required before claiming this
cutover complete; the amendment itself is not a runtime receipt.

`make setup` passes the explicit declared key list
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
Logical tool names select their typed `toolchain.tools` entry; its declared Mise
selector is the exact key shared by the manifest, lock and executable request.
When no selector is declared, that key is the logical name itself. Resolution never
substitutes the logical name for an explicit provider key or searches alternate keys;
the native pinned release and checksum authority remain unchanged.

A project `bin/` never enters PATH (shell, `BASH_ENV`, or CI `GITHUB_PATH`): Mise binds
the shared shims to the first `mise` on PATH. Caches and installations stay out of Git.

Mise reaches GitHub during setup to install a declared tool missing from its cache,
and during upgrade to resolve releases. Only `make upg` writes `mise.lock` and `uv.lock`;
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

The default `make gen` handler invokes the generation engine at `PROJECT_ROOT`,
with `all` scope locally and `self` scope in its declared CI context. A local
workspace invocation covers its root and declared members, while a standalone
repository has only itself. The request model's default remains
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

File phases share each participant's already journaled transaction root. Flat,
phase-qualified staging leaves replace intermediate phase directories; the existing
manifest verifier authenticates the root and its residents before staging. Each leaf's
absent-parent identity must match that original created-root receipt before its intent
is durably persisted. Directory creation receipts, file intents, CAS writes and fsync
remain required at their existing boundaries. Recovery consumes recorded paths, not
the staging filename layout, including paths in previously prepared journals.

Interrupted no-clobber staging can leave the atomic writer's temporary name and
its intended staging leaf linked to one inode. Physical equivalence, matching
bytes and a producer-shaped filename do not prove who created that temporary.
The journal's private-directory identity grants no blanket disposition authority
over unregistered residents. Recovery must preserve and refuse a linked temporary
unless exact producer attribution was persisted before publication; the original
staging-intention contract records no such temporary name or inode receipt.
Existing retention of published destinations does not authorize ignoring foreign
transaction residents. Ordinary cleanup inventory still rejects hard-linked
files. The normal writer defers catchable termination signals across link,
ownership bookkeeping and temporary unlink; this prevents that catchable-signal
window but is not a crash-recovery ownership receipt.

An exception-only repository outcome is a failed plan even when it has no diagnostic
message yet. Planning progress and persisted evidence must agree on that failure;
an `OK` planning row never attests publication. The managed executor settles the
independent bootstrap, lazy-init and documentation targets through their own input
and dependency guards before returning the aggregate failure. A logical rejection
does not replace a later first native exception, and secondary failures do not
replace an earlier native cause. Incomplete operation receipts retain planning and
publication issues alongside successful batches and cannot qualify as complete.

Input dependency evidence remains fail-closed. A module-selected lazy-init invocation
plans that package and its descendants, not every package in its source/test surface
or its production sibling. The shared repository index still authenticates native
namespace selection and negative discovery witnesses. Prefetched originals are not
semantic consumption: each artifact retains its actual native reads, transitive
ancestry and cache-dependency replay, including dependencies outside the target tree.
The executor never drops those guards or exempts `conftest.py` to tolerate edits.
A rejected dependent component remains rejected, while authenticated independent
components keep their published gains. A fresh canonical invocation after repairing
the causal input renders from fresh inputs rather than retrying a stale candidate
inside the failed invocation.

Dependency modernization and conformance both consume the project's typed
`config/workspace.yaml` declaration for distribution roots and packaged data.
Modernization must retain those declarations when rebuilding Hatch targets;
an empty topology cannot replace a declared one. Wheel and source-distribution
templates use the same bounded `only-include` selection as modernization, with
the declared wheel source mappings and explicit file inclusions.

Analyzer search paths retain the precedence order derived by
`FlextInfraExtraPathsManager`. The Pyright declaration phase and its later
synchronization consume that same order; the declaration's list operation must
not alphabetize it and create a competing change in the same pass. Generic TOML
list operations keep their declared sorting behavior. Modernization acceptance
requires a byte-identical second render and an audit that reports every remaining
drift, including formatting-only drift; phase notes alone do not prove that
contract.
The ordinary renderer orders plain mappings through the shared JSON key-ordering
owner before constructing TOML nodes, retaining configured leading sections and
array order. It does not move existing TOML tables with order-dependent trivia.
The separate Git-reference migration continues to preserve the original TOML
tree. The audit compares the final bytes with the original bytes exactly and
describes layout drift even when no semantic phase added a change note.

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
The internal initialization adapter qualifies its elected surface: an existing
project's Makefile bootstrap or an admitted new tree's complete generation. Its
read-only verification requires that same recorded coverage. Complete generation
qualifies its managed and documentation batches after each has settled. A
complete `all` scope can verify the `self` subset only when that repository
root is in its recorded coverage. Checks authenticate source, generator, output
and physical identities without planning, rendering, repairing or replacing the
receipt. Missing coverage and changed identities remain failures.

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
Explicit class-owner recognition and rendering resolve each declaration through
the physical path in the authenticated source map and its native Rope resource.
The declaration's import spelling indexes that captured map; it is not a fresh
global module election. Separate packages may share an import spelling without
sharing a physical provider. Neither basename matching, reconstructed module paths
nor fallback lookup may replace the captured resource identity.
Namespace bases are read through the native source class's `get_superclasses()`
on the authenticated candidate module. Rope evaluates its original header AST
in the defining parent's lexical environment, before namespace-body bindings.
A separately parsed AST has no native node-identity context and must not replace
that lookup. Every declared base must resolve; an omitted native superclass is
an error, not permission to drop a base. Same-name class publications inside the
namespace remain authored bindings and do not change header lookup semantics.
After completeness validation, each returned superclass is paired in declaration
order with its AST base and admitted by the strict native-class guard before any
ancestor traversal. A rejection names that exact expression, position, physical
facade, namespace and Python SDK type without querying the rejected object.
An ancestry admission failure retains its original exception and reports the
rejected object's concrete SDK type through Python type metadata only. Diagnostics
never call native name, module, type, attribute or ancestry APIs on that rejected
object: those calls can trigger inference rather than observe stored metadata.
The introducing class is already admitted; only its name and SDK type are queried.
Uncaptured resources remain explicit `None`, without diagnostic module resolution.
The physical facade and its declared AST base expressions supply source context.
Diagnostics do not admit unknown objects, skip ancestors or widen the class
contract without evidence from the real consumer.
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

Conform's initial lazy plan supplies the provider overlay consumed by facade
composition. When that composition changes Python sources, the final lazy plan
must observe those proposed facades, not reuse the baseline export decisions.
Original-file currentness alone does not prove overlay equivalence. Receipt replay
is restricted to its issuing source authority; changed-overlay reuse requires that
owner to prove the complete consumed effects, negative queries and export decisions
against the final candidate before retaining any package result. Until that proof
exists, retain final planning and measure its index, snapshot, package-decision and
receipt-verification costs through the existing generation profiling owner, without
raising deadlines or sharing native caches across source authorities.

Deriving candidate views must remain an operation of the existing authenticated
read owner. One original authority owns its physical files, import election,
directory inventories and negative witnesses. Each candidate owns immutable
declared effects, its semantic graph and the receipts it issues. Opening candidate
B must neither mutate candidate A's overlay nor reinterpret A's receipts under B.
The original issuer must still reject copied or foreign receipts. Added and retired
paths retain their original physical witnesses and candidate-specific query results.
Import roots introduced by declared effects are derived virtually by this owner;
their admission must preserve the same resolution as a fresh candidate binding.
They do not re-elect the physical authority or admit unrelated roots. An ordinary
same-effects consumer retains its existing election and source-folder preference.
The orchestrator injects this authority; it does not copy a source inventory or
merge a parallel path/text map. Final candidate planning, source-publication
verification and physical CAS remain required. This is the derivation acceptance
contract for the OUD generation repair tracked in `algar-723.1`, not evidence that
the current API or generation already satisfies it.

The ordinary generation handler admits `settings.Infra.profile` around its actual
typed `codegen_generate` call. The shared profiler preserves the returned Result
and classifies failure from `Result.failure`, not its truth value. Its output uses
the existing Git report-evidence owner and publication-report path with a `.pstats`
suffix; native termination checkpoints and atomic publication remain shared with
command profiling. Disabled profiling performs the original direct call and creates
no profile. Capture measures the generation operation, not CLI startup, and never
certifies successful generation or replaces its first failure.
A failed operation's return value also survives a secondary profile diagnostic
write failure on closed or unavailable stderr. Profile finalization still fails an
otherwise successful operation; missing evidence never becomes capture acceptance.
Publication emits one stderr identity line containing the PID, owning thread and
exact immutable raw path, without argv or credentials. Bind that line to the real
command receipt; mutable latest paths and unassociated older captures are not
performance evidence. Native temporary-file contexts own descriptors and staging
cleanup for both raw and text publication, preserving captured inode checks and
the original failure. Finalization also releases a successfully acquired profiler
when signal registration fails; a cleanup diagnostic cannot replace that cause.

The existing opt-in public CLI form is
`FLEXT_INFRA_PROFILE=true FLEXT_INFRA_PROFILE_OUTPUT=<file> flext-infra <command> ...`.
The CLI entry profiles the whole command once. The generated gen, mod and check
recipes declare the destination through `FLEXT_INFRA_PROFILE_OUTPUT` (make
`generation_profile_path`, `modification_profile_path` and `check_profile_path`).
The check route's captured checker child writes its own profile beside its gate
receipts. The private
`flext_infra._profile_entry` module survives only as a deprecated pass-through for
Makefiles not yet regenerated, and is deleted once none calls it (bead
`flext-dngq7`). Raw profiles,
including the existing clock's immutable per-invocation versions, remain in the
authenticated exact worktree Git control directory's report tree; they are not
copied into the source repository. The report reader admits a selected native
profile from that owned Git-control report root or the repository's `.reports`
tree, never an arbitrary external path. Already admitted repository profiles do
not require Git lookup; a selected Git-control profile requires the existing exact
owner authentication, whose original failure escapes without fallback or guessing.
Text output and pytest run receipts remain confined to the repository's `.reports`
tree. This is capture-only plumbing correctness, not performance optimization:
execution, deadlines, outcomes and gates remain unchanged. Report row limits affect
display only; all raw statistics remain retained. The parent owns real capture,
rendering and native-gate evidence; source alignment alone proves no timing gain.

Profiling has one owner per synchronous execution context. When the Make launcher
already profiles the CLI, the generation handler joins that capture instead of
starting a second cProfile instance. The outer invocation owns its artifact and
signal checkpoint; the nested operation keeps its exact return value and exception.
Direct CLI generation still owns its operation capture when no launcher capture
exists. This is profiling composition, not permission to skip generation work or
reuse an earlier source observation.

Selected capture measures only its owning thread. Other threads, logging and the
productive workload continue unchanged; they are not disabled, serialized or
filtered after collection. Owner waits measure owner wall time, not worker CPU.
Native `pstats.Stats.total_tt` is not the operation's external elapsed time. A
ContextVar joins a nested selected capture only on that same owning thread; an
explicit capture on another thread must acquire its own native profiler and fail
when `sys.monitoring.PROFILER_ID` is occupied, never join a foreign capture.

The shared stdlib-only clock owns actual standard `cProfile.Profile` engines.
After native `enable()` acquires the tool ID, it reads the actual monitoring event
mask, pauses events and takes every enabled callback through public
`sys.monitoring.register_callback`. Each displaced callback must be bound to that
engine through its standard `__self__`; every event is gated by stdlib
`threading.get_ident` before invoking that original callback with unchanged
arguments and return value. Foreign-thread callbacks return `None`, never
`sys.monitoring.DISABLE`, which would disable locations for the owner too. Only
registration-window statistics are cleared while events are paused, before the
productive operation starts. Restore the original event mask only after all gates
are installed. No private upstream callback name, subclass access, custom timer,
replacement profiler, version pin, SDK mirror or statistics filter is admitted.
The public `CALL` group includes its ancillary `C_RETURN` and `C_RAISE` callbacks:
gate those too, even when `get_events()` reports only the controlling `CALL` bit.
CPython's native event storage omits those ancillary bits; iterating only the
returned mask would leave C exits able to corrupt the owner stack. This follows
the [public monitoring event groups](https://docs.python.org/3.13/library/sys.monitoring.html#ancillary-events)
and the inspected CPython 3.13.15 `Python/instrumentation.c`, `Modules/_lsprof.c`,
`Lib/cProfile.py` and `Lib/pstats.py`; it is not a runtime version constraint.

Tool ownership is exclusive and cooperative, as native cProfile already requires.
An occupied tool fails without cleaning up or mutating the foreign owner. This is
not protection against uncooperative direct monitoring-registry hijacks. Exceptional
partial acquisition preserves the first cause and reports any unrecovered native
state explicitly; it must never report a clean release it could not establish.
Disabled profiling does not probe monitoring capabilities.

Use the actual native `cProfile.Profile` directly. Its public `snapshot_stats()`
reads native `getstats()` into `Profile.stats` without disabling or flushing active
frames (`cProfile.py:54-91` in the managed CPython 3.13.15 source). A signal
checkpoint uses that primitive while capture continues unchanged: it is partial
completed-entry evidence, not full operation duration or proof that active frames
were flushed. Final publication disables the native engine first, then calls
`snapshot_stats()` for the full captured window. No session controller, segment
list, replay, aggregation, restart, re-enable or productive-stat clearing is needed.
Publication serializes the actual native `Profile.stats`, never a mirrored SDK
interface or manually populated Stats stub. Keep immutable invocation artifacts;
the original `41ee` interpreter-wide thread capture remains invalid timing evidence,
not a queue-to-Rope critical path. Only a new qualified owner-thread profile can
support attribution. The parent must prove the actual `FLEXT_INFRA_PROFILE=true`
operation and report at the same root-loop scope, plus occupied-tool capability QA.
No Rope or staged-package optimization is authorized by this profiling repair.

Diagnose slowness from the actual immutable cProfile artifact before changing the
implementation. Queue or lock waiting in a parent identifies a native execution
boundary, not the supplier algorithm's cost; obtain the supplier's own profile when
that distinction matters. Follow measured callers to their canonical owner, preserve
the full source/receipt/invalidation contract, and compare the same productive work
after repair. Raising deadlines, dropping the final candidate pass, weakening source
checks, adding cross-authority caches or replacing runtime with a smaller workload
does not establish a performance correction.

The packaged `Infra.codegen.toolchain.uv_override_dependencies` declaration owns
the Rope revision consumed by generated project metadata. A supplier performance
repair must be integrated and validated through that supplier's native lifecycle
before this declaration advances. Generation projects the declaration, upgrade
resolves its native lock and setup installs it; these operations remain separate.
Confirm the installed Git provenance before attributing a new generation profile
to the supplier repair.

The cProfile report retains native callers for its bounded hot-function selection in
addition to the selected repository's source callers. A workspace operation can spend
its time inside a declared provider repository or the standard library; source-root
filtering must not hide that caller chain from diagnosis. Both views use native pstats
and the same complete immutable profile, without running or reconstructing the workload.

The standard Make operations admit the same opt-in setting:
`FLEXT_INFRA_PROFILE=true make gen`, `FLEXT_INFRA_PROFILE=true make mod` and
`FLEXT_INFRA_PROFILE=true make check`.
`settings.Infra.profile` defaults to false; it never selects a different operation
or changes source admission, target scope, publication or native failure handling.
The recipes use the existing shared CLI profiling transport. Their report paths
come from `Infra.codegen.make.generation_profile_path`,
`Infra.codegen.make.modification_profile_path` and
`Infra.codegen.make.check_profile_path`, bound to the selected `PROJECT_ROOT`,
not the caller's working directory. Disabled capture retains the direct CLI call
and creates no profile. There is no common profiling verb or legacy alias.

Make transport capture starts after settings admission and transport imports; those
startup costs and Make/environment preflight are outside its raw statistics. Child
process waits are parent wall time, not child CPU or evidence of child hot functions.
Retain the existing immutable raw captures and termination checkpoints, rendering
them only through the public `validate cprofile-report` owner. Bind evidence to the
actual source, runtime, configuration, command and selected scope; an interrupted
capture is incomplete failure, never successful modification. The universal command
deadline includes startup and children: request termination by 118 seconds and
finish by 120 seconds, using an enclosing deadline when the native operation has no
such bound. Capture repair alone proves neither a timing improvement nor a green
generation, modification or gate result.

The transport delegates directly to the single native capture owner. Existing
run receipts remain with their producer; there is no separate command-context
model, writer or receipt-admission branch. An older capture without a receipt
remains unbound. Preserve its raw, native failure and declared installed source;
neither inferred settings nor post-capture source hashes authenticate its epoch.

Caller edges that attribute YAML parsing to queue waits or native locks contradict
the actual call contracts and cannot justify a latency optimization. Preserve the
raw and its native caller report, repair the collector owner, and obtain a new
capture from the correctly delivered source before attributing causal costs.

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

Internal transport preserves existing typed instances, including immutable physical
observations, by reference; consumer selectors do not clone them for every probe.
The canonical receipt owner merges consumption once at the boundary, preserving
identity, negative queries, membership, symlink and physical-alias checks. Construct
the final model once, at the owner where all its real fields are available, rather
than constructing a partial result for later completion. `model_copy(update=...)`,
dumps followed by revalidation, `model_construct` and custom clones are not internal
transport mechanisms and cannot replace that ownership. Reuse `c/t/p/m/u` with `r`
and canonical defaults; closed domains use `c.StrEnum`, while free-form text stays
open. Type narrowing and redundant conversions are not transport mechanisms.
Conflicting observations still fail.

Repository rendering owns one assignment-validated `CodegenRenderInputs` state
per planning operation. Its static target, workspace, codegen policy, artifact
snapshot and branch references are read-only; only planned requirements and the
resolved tooling context advance. No state is shared between repository workers.
An unchanged tooling derivation returns that same state and original tooling
receipt, without a second template pass. Changed tooling replaces only that
state's tooling reference. File plans retain their original source witnesses;
configuration and durable publication receipts remain frozen. These are ownership
contracts, not runtime acceptance.

The census refreshes its Rope inventory after constant-consumer publication and
declaration removal, before collecting the resulting report. Deleted or added
initializer projections must be reflected in the source inventory it reads.

Constant source discovery is separate from consumer orchestration. Native import
provenance, facade publications, assignment identities and inert literal discovery
belong to `FlextInfraUtilitiesSemanticConstantSources`, exposed only through the
consumer facade's `ConstantSources` class binding. Project-owned native
`ownership_transfer` contracts in the constant-consumer phase authenticate
the existing method identities and all receivers before retiring their original
declarations in the same candidate; there are no forwarding methods, manual cuts
or module-cap exemptions. Consumer orchestration retains its shared consumption
receipts. A flat facade constant can retire only at one explicitly published,
equivalent authored component declaration; its complete value and native type
identity must agree. Declaration retirement and consumer rewrites share one
authenticated candidate. Layer-zero modules retain their configured runtime roles,
and generation still rejects genuinely mixed scalar/class facades.
The rule catalogue belongs to the elected repository root, not the physical Rope
workspace root that an attached member shares with its containing workspace.

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
generated. A shell containing only documentation and future imports is derivable:
the existing native syntax facts prove that it has no executable publication.
A nonempty authored initializer with loaders, declarations or constants is retained
in full; its public exports remain part of discovery. Custom facade planning first
seeds derived export plans into its declared-source cohort, then converges facades
and exports over that same authority. It does not publish a bootstrap initializer
or replace a missing upstream publication with a private import.
The lazy planning report records `ownership=authored`, `disposition=retained` and the
existing RETAIN action. Publication reelects ownership from the current target before
its single write, so a later authored replacement is retained and is not counted as
a generated file. No directory-name exemption list selects this behavior.
Shared input snapshots document the planner's inputs; later source edits do not
invalidate an entire generation. Directed validation checks the actual generated
targets rather than comparing every source with an earlier workspace snapshot.
Each repository plans once against one original source epoch. A source that
changes while it is being planned fails verification and raises its original
exception; there is no in-process successor, receipt adoption, conflict
classification or bounded re-plan. The repository outcome records that exception
and no files, and generation is rerun with `make gen` once the sources are stable.
Changed external member dependencies are source inputs, not exclusions.

Repository generation plans treat malformed source as a failed input. The
planning report at `.reports/codegen-plan.json` under the worktree's Git directory
(never the source tree) records each selected repository's
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

A project finding is an operation result, not an engine exception. Independent
registered gates continue in declared order after a failed verdict, including
repair operations; only an explicitly selected fail-fast contract stops that
sequence. The combined result remains unsuccessful and retains each native
diagnostic. A repair selection is validated for supported operations before its
first effect. Unexpected engine exceptions retain their original traceback;
continuation never catches or normalizes them into findings or success.

The Make-engine stabilization scope covers dispatch, report fidelity, execution
boundaries and measured performance. Local project violations are inputs to that
engine validation, not an instruction to repair their application code or weaken
their gates. A truthful nonzero project result can prove engine behavior while
remaining a failed project acceptance result.

Persistent analyzer caches are namespaced by the selected physical project root.
Their allocation does not parse packaging metadata or require `[project].name`;
Ruff also supports tool-only configuration, as its
[native configuration contract](https://docs.astral.sh/ruff/configuration/) documents.
The cache owner derives one deterministic digest from the resolved root, with no
metadata-name route or fallback. Native tools retain responsibility for their input
diagnostics. Packaging operations still require their own declared metadata.

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

Local runs, CI, and hooks derive their gates from the same active set and from
each gate's declared stage (`c.Infra.GateStage` in the registry row, or `stage` on a
`make.project_check_gates` entry); no hand-kept gate list exists. `CI=N make check`
and `make check` without `CI` run the complete active set. `CI=Y make check` runs
the commit and CI stages (`make.check_gates_ci`, Pyrefly included). The commit hook
passes `make.ci.pre_commit_value` and runs only the fast commit-stage gates
(`make.pre_commit_check_gates`: lint, format and Markdown); it runs no tests and no
other validator. Mypy, Pyright, codemod, smells and repository-owned validators
carry the push stage, so they block locally and at pre-push. Every gate blocks in
every context that runs it; there is no informative or advisory gate. The `check`
pre-push hook drops the inherited `CI` to run every active gate.
Conflict detection uses the canonical Git inventory, including unpublished files,
and the shared merge-control classifier. It reads literal source-link targets without
following them. Every finding, including a native warning, blocks approval while its
original severity remains in the receipt.

Every workspace and standalone projection exposes `make pre-commit` for the CI validation
workflow. CI invokes the separate approval verbs declared by `make.workflow`, in their
declared order; it never substitutes the fast hook for approval, and no verb requires
a clean or unchanged tree. The configured CI token selects the blocking CI gate
partition. Audit is read-only conformance and installed-lock provenance, not
generation or a dirty-tree check; legitimate staged changes are not rejected simply
for being staged.

CI setup reconciles the owned physical environment through locked, noneditable
installation, including an existing venv. Root CI checks out declared members
before installing the same native workspace/lock as local execution; standalone
CI retains its own project contract. The CI token does not replace native source
declarations or select a synthetic resolver. Only explicit upgrade resolves or
writes locks; setup preserves the first install error without another lock mode.

After installation, local setup authorizes the published `.envrc` with native
`direnv allow`; CI skips that authorization. Setup never renders, compares or
repairs environment files: `make check` verifies environment provenance and
projection drift, and `make gen` owns regeneration. Repository batch operations
such as `codegen mise-artifacts` select `all` in local workspaces; attached
members, standalone repositories and CI select `self`. Git declarations own discovery
order, and each operation runs serially through its original validator or consumer.
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
workspace execution context, policy and report digests before signing. It does not
invoke Make. Schema v3 addresses each immutable proof by original receipt digest,
effective runtime/policy context and stage. The signed Git tag anchors the exact
original receipt blob, never a commit or tree. An unborn repository needs no commit to
store proof. Unlike v2, the signed command retains workspace scope, runtime identity and
nullable before/after Git observations; the JSON shapes are not interchangeable.
Repeated publication compares the canonical signed fields, not process-local model
state, and verifies the existing object and original artifacts before reusing it. Signed
public facts retain the actual process outcome, portable operation intent and diagnostic
classification. The original public receipt binds the exact argv digest; command bytes
and the working directory remain in private execution checkpoints, outside the CI
artifact allowlist.

Admission derives from the original typed reports rather than caller success flags.
Checks require complete target and requested-gate coverage in SARIF. Tests require
original process, accounting and diagnostics reports with complete positive execution.
Timeouts, signals, collection errors, operational failures, missing artifacts and
changed digests remain failures. The complete-execution policy may admit finished
findings while preserving their nonzero status; the clean-quality policy rejects them.
Bare `make check` uses the existing workspace capture route to execute the original
checker once. It preserves that producer's native process outcome and owns an exclusive
report base, then writes an immutable receipt when the original reports and execution
context remain valid. Dirty, changed or unversioned workspaces still execute and can
retain original execution receipts with observational Git metadata, never
commit-validation proof. Tracked and untracked WIP, unknown Git identity, missing origin
and HEAD/tree movement are not acceptance failures. Observations retain `true` or `null`
rather than pretending to be clean. Unrelated changes do not invalidate the run;
relevant inputs require affected-scope revalidation, not a globally frozen tree. No
receipt certifies all WIP. Signature verification authenticates the named execution
history. Reuse by a new operation still requires that operation's consumed-source and
native-context checks; the signed receipt is not a substitute for affected-input
revalidation. Configuration or runtime drift still prevents receipt publication. The
native pytest runner captures its candidate immediately before the original suite
process and publishes original receipts after accounting and diagnostics are written. It
retains its existing deadline and testmon execution. Both producers share the same
capture and report-binding owner. CI preserves the public original receipts and their
required structured reports, while omitting private checkpoints, commands and capture
errors. The Make policy and receipt directory come from the typed codegen specification.
CI signing/restore wiring, zero-execution cache evidence and other stage adapters remain
required integration work. Verifying a setup proof never provisions a fresh runner.

Capture receives the selected repository's full `CodegenInputs` through the canonical
layer loader. Its policy and report directory come from that typed target specification.
The context binds the effective specification, ordered input filename/content digests,
portable operation intent and actual runtime. Tests also bind their existing native
`testmon_environment` identity. Completion reloads the same target loader and rejects
configuration or runtime drift while preserving the original process outcome. Config
payloads and machine paths are not exported with these fingerprints.
Signed verification selects the original receipt explicitly and checks the tag's blob
bytes against it. Neither current HEAD nor a caller-supplied commit selects the proof.
Missing origin does not
select a remote effect or prevent local capture, signing or verification. Toolchain
verification reads the elected live resolver inputs and effective configuration,
including uncommitted values; membership in a Git commit is not required.

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
verb runs only the qlty smell scan and fails when it finds defects. Each smell
finding carries the repair text declared under `smells.fix-text` in
`config/tooling.yaml`, keyed by the qlty check. Static enforcement has no
hand-maintained catalog: each owner that detects a law claims its `ENFORCE-NNN`
id where it is declared (ast-grep rule `metadata.enforce`, the Ruff rules'
`tools.ruff.lint.enforce`, the qlty checks' `smells.enforce`, the gate registry's
`GATE_ENFORCES`, a codegen template entry's `enforce`). The `enforcement-catalog`
gate in `make check` derives the catalog from those claims and fails on a claim
its owner repeats or on an id whose only owners are disabled or unregistered.
An empty or
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
casts and suppressed diagnostics are not repairs. `ScopeMixin` owns repository,
project and verbosity inputs. Module and namespace selection each have one
narrow mixin, composed only by a request or service that consumes it. Namespace
enforcement requests compose module selection; accessor migration requests
compose both selections. Lazy initializer planning and runtime census services
compose module selection, and accessor migration services compose both. The
common command context and general read/write request mixins declare neither
selector.
The local service-import law is
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

Read-only Make verbs never invoke generation, repairs, formatting, or codemod
application; `make check` runs conform only in its read-only `--mode check`. Audit
checks installed dependency and environment provenance, and check validates the
documentation without rendering replacements. Installation provenance binds the
locked source, installed origin, declared physical checkout and committed gitlink;
unrelated worktree changes do not invalidate that identity. Operation admission
separately authenticates the content and epoch of its consumed sources and accepts
changed inputs only through its actual publisher's effects. Persisted publication
reports never authorize those changes. Staged, unstaged and untracked work is
never a check condition (Shared Worktree Contract).
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
The existing CLI route selector constructs a separate tuple for each of the
codegen, check, dependency, release and workspace groups. These groups retain their
current owners, which resolve service classes through the existing public barrels
when constructing that group. Refactor resolves directly through its own owner;
docs, maintenance and validate still share their existing eager table. The
command models, handler bindings, messages and ordering remain unchanged. In
particular, workspace propagation retains the facade that injects its conform
collaborators. Shared facades, every command in the selected group and their real
transitive dependencies remain available; this boundary does not promise lazy
resolution per subcommand or measured startup gains. It does not combine native
processes or replace their interpreter and outcome receipts.

The infrastructure CLI profiler starts before importing its public CLI facade.
Each completed invocation retains a uniquely named raw profile beside the latest
profile through that same publisher. It also retains the previous completed
artifact before replacing the latest path, including profiles from older launchers
that did not yet retain per-invocation artifacts. Termination checkpoints have their own
invocation-owned artifact and never overwrite the last completed profile.
Each raw profile's text report records the publishing process ID and its monotonic
capture timestamp. Bind that report to the invocation's process interval and consumed
source identities before comparing captures; UUIDs and filesystem timestamps alone
do not establish which concurrent invocation produced an artifact.
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

The pytest deadline correction tracked by `algar-723.1` applies the same absolute
entrypoint clock to complete, incremental, file, coverage and profiled operations.
Selection mode cannot disable that clock. The typed tooling policy bounds the
operation, including lock waits, collection and execution, within the 120-second
command contract. One declared budget replaces project-specific wall exceptions.
Termination grace stays inside that budget.
Historical 300-, 600- and 1200-second exceptions are superseded by the current
performance requirement, rather than retained as measurement modes.

Run-context receipts must carry the absolute deadline even when collection fails.
The existing process owner retains native timeout and signal outcomes; incomplete
collection or execution remains red. Disabling a per-item timeout is independent of
the aggregate operation deadline. This correction does not by itself prove a bound
on Make activation or Python work outside supervised children. Until the complete
native boundary is verified, the required outer command deadline still applies.
Exercise the current public `make tests` operation before changing its regression
tests; the retired common file and profiling targets are not validation routes.

A failed native pytest collection is a failed project operation, not an exception
of the runner. Preserve its raw exit, timeout and signal receipt and its original
log unchanged. Publish the existing typed collection diagnostics and identify the
unexecuted suite without fabricating JUnit or complete inventory accounting. The
terminal identifies those receipts rather than embedding the entire collection
log in another traceback. A startup failure can precede report-plugin
configuration: record the missing native report paths as unavailable, retaining
the failed process status and unknown diagnostic counts rather than manufacturing
empty diagnostics. Existing malformed reports, filesystem errors and runner
defects still escape unchanged; no catch or success normalization hides them.

The check engine must retain its current aggregate reports before the first gate
and after every completed gate, using its existing invocation report directory and
report models. The optional external report destination does not enable this
preservation. An interrupted run leaves the reached outcomes and marks required
unreached work incomplete; it cannot publish a passing project or invocation.
Results retain their declared target order, including real attempted projects
without applicable gates. Such an attempt is published before advancing and
remains incomplete; equal directory basenames never identify the same target.
The existing progress callback and Markdown/SARIF owners implement this contract.
No extra reporter, latest pointer or alternative acceptance path is introduced.

Duplication assessment consumes every native scanner candidate. Within one
assessment, its existing captured-source owner must parse and tokenize each
physical Python source once and reuse that analysis across candidate spans.
Classification, measurements, original scanner data and final source
revalidation remain unchanged. This is invocation-owned analysis, not a
persistent cache or a substitute scanner. The interrupted check at
`20261023T222230.866234Z-2924444` retained the scanner's complete raw output but
stopped during assessment; its timings do not quantify individual Python
functions. Native before/after execution and current profiling must establish
the performance result without reducing scope or raising deadlines.

## Workspace snapshot and analysis engine

| Infra declaration | FLEXT architectural declaration |
| --- | --- |
| This subproject's Workspace snapshot and analysis engine section. | [ADR-028 Decision 17](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md#decision-17) |
| ADR backlink to this exact Infra section. | [ADR-028 bidirectional traceability](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md#bidirectional-traceability) |

Generation and modification run through one workspace organizer. It loops over the
selected repositories in dependency order without worker pools; each repository
invocation owns one planner and one native workspace model. The model is injected as
`p.Infra.WorkspaceSnapshot` into that repository's planners, renderers and queries. A
service that can run standalone opens its own snapshot only when none is injected; no
consumer opens a second snapshot or analysis project while one is bound. Generated
rule builders pass the same snapshot to their classifiers and library-prefix discovery;
they do not discard it before calling snapshot-owned package or layer queries.
The public `mod` composition preflights the selected repository references and
uses the existing dependency-order owner before invoking each repository handler
in the same process. Each rule plan contains only that repository's generated
provider. Authored fixture discovery collects resources from separate repository
plans and verifies each fixture owner once; it does not union generated rule IDs.

Each repository snapshot owns exactly one analysis project rooted at that repository's
runtime owner root (`u.Infra.runtime_owner_root`). It does not merge sibling repository
trees into one project. A cross-repository operation passes its separately owned native
projects to the native multi-project refactoring capability rather than building a
parallel cross-repository model. Only the `u.Infra` snapshot and adapter owners name the
underlying implementation; orchestrators, models, protocols and external consumers see
the generic `p.Infra` capability.

Every derived fact is a lazy memo on the snapshot, computed on first query and
reused for the rest of the run:

- `workspace_python_files`: the governed source inventory for this repository;
- `workspace_source` / `workspace_sources`: authenticated reads carrying the
  atomic file state, digest, module and member of each source;
- `workspace_module_tree`, `workspace_module_imports`,
  `workspace_module_closure`: the engine's parsed module, its runtime and
  `TYPE_CHECKING` import edges, and their transitive closure;
- `workspace_resolve` / `workspace_class_ancestors`: the defining identity of a
  name and its linearized class ancestry, from the engine's own object model;
- receiver bindings, facade paths, pyproject texts and codemod renderings, each
  keyed by the identity that determines it.

A memo is valid only for the source state it was computed from. After a batch
publishes, the publisher refreshes the snapshot for exactly the published paths:
the engine revalidates those resources and the snapshot drops every memo entry
derived from them. A later query recomputes from the new bytes. Publication and
source authentication still belong to the existing transaction owner; the
snapshot never authorizes a write.

Each repository snapshot lives only for its invocation. There is no cross-run cache,
persisted import index, or automatic-import database; the engine's object database is
persisted only for the generation and modification verbs that declare it.
`workspace_snapshot_verify` rechecks the captured source states before that repository
invocation accepts its plans.

The lazy-provider pass consumes the authenticated repository root and the
snapshot's source inventory only. Configuration, local workspace metadata and
the conformance target are resolved by the managed pass that consumes them;
initializer planning does not repeat that resolution for every member. Both
passes retain the same source authentication and publication boundaries.
The codemod generic-specialization fact is declaration-only, before migration:
it passes the injected `snapshot.engine` to the facade-member owner, resolves
the published `p` and `t` classes and their inherited members through native
source identities, and reads PEP 695 alias declarations without evaluating
their values. Only a `p` alias whose immediate subscript origin is the exact
same-named `t` binding contributes. Target and dependency packages are never
imported to derive this fact. Unresolved or dynamic candidate identities fail
explicitly; no runtime retry, omitted fact or second analysis engine is allowed.
This contract is not runtime acceptance; the consuming public `make mod` and
subsequent global gates remain the integration owner's proof.
Repository planning emits an exception's original traceback when capturing its
failed outcome. The final report retains that same cause; interruption before
the cohort finishes cannot hide the first failure behind a timeout.
Each repository keeps its own module index and name bindings, including internal
packages whose names may also occur in another member. The source engine shares
directory facts keyed by physical path and module facts keyed by native parsed-module
identity. Resource invalidation cannot reuse facts from the replaced parse. An explicit
planned source view derives its own facts and cannot populate the original snapshot's
facts.
Facade-letter election consumes the parsed module from that same source
project, including candidate overlays. It must not parse the module's text
again or keep a separate source-text cache to identify its exported letters.
Export declarations retain the shared literal and named-sequence semantics.
This query does not authorize publication or replace source-state verification.
Protocol-consumer discovery likewise reads the native module's tree and lexical
scope together. It must not construct a string module after separately parsing
the same source to find receiver references.
Tooling derived from planned Python sources uses that same injected view for
first-party namespace discovery as well as runtime bases. It must not reopen
physical workspace metadata while deriving the planned artifact.
Native project construction belongs with the existing source-project factories;
module queries inherit that capability through the runtime facade. Catalog
utility rules use the declared provider-rule owner directly, without a second
catalog reader.

Current state (2026-10-26): the one-project-per-repository contract is accepted in
ADR-028 Decision 17. Module-level identity reuse is partially implemented; nested class
qualnames, publication refresh, and the remaining consumers of source-base analysis are
still in the `flext-1engx.15` cutover. Managed conformance currently retains a source
engine per distinct planned view in some repository paths, while the provider pass uses
the repository workspace engine. That split violates the accepted target until each
repository invocation has one shared project with proven provider invalidation and
member-scoped bindings. This status is not a performance or convergence receipt.

### Profiling a root verb

Profiling is opt-in: export `FLEXT_INFRA_PROFILE=1`. The root `gen` and `mod`
recipes set `FLEXT_INFRA_PROFILE_OUTPUT` themselves, from the typed Make spec
(`generation_profile_path`, `modification_profile_path`), so an output path
exported by the caller is overridden. A profiled run writes
`<reports>/codegen/gen-<id>.pstats` (and `<reports>/refactor/mod-<id>.pstats`)
with a readable `.txt` beside it. The signal checkpoint observes termination
through the CLI's existing parent-signal observer while a native child is
active. It captures completed profile entries without disabling the profiler,
restoring handlers or invoking the displaced terminating action; the process
owner first cancels and reaps its child. Direct termination outside that
containment retains the previous native signal action. A checkpoint publication
failure remains visible without replacing the command's first failure.

The complete invocation, including profile publication and child cleanup, keeps
the operator's 60-second budget. Reserve termination time inside that budget;
never increase it to finish a profile. An interrupted capture remains partial,
and absence of a readable capture is a profiling defect, never a speed result.
When an external deadline encloses the shared heavy-operation lock, use the
native `flock --no-fork` form: the monitored child must remain the actual Make
invocation. If a forking lock holder exits on TERM first, the deadline monitor
may return while its descendants remain alive. Consume the command result and
verify termination of its owned processes; the monitor's disappearance alone
does not prove cleanup.

The first structural optimization retains the invocation's snapshot and
precomposed rule plan through fixture verification and the initial scan. No
source transformation precedes that scan. Later candidate changes still require
their own current analysis; this first cut does not authorize reusing the
original plan after publication. Native tool caches and per-invocation facts
are the approved reuse boundary; Infra adds no persistent semantic index or
derived-fact database. The existing shared workspace, candidate and report
owners remain the implementation boundary; ADR-026 is still proposed.

Scope producers share the snapshot's explicit-export facts, read from the
engine's existing module tree with the canonical assignment reader. Membership
queries use the same elected file inventory as a set; they do not traverse the
member's full path sequence for each module or ancestor. Declaration discovery
uses that same native tree instead of parsing its captured text a second time.
The original authenticated source states remain the verification inputs.
Imported-package discovery also consumes that native tree. The existing
absolute-import reader owns the statement traversal for both source-text and
parsed-module callers, preserving nested imports and excluding relative imports.
Its member-wide result is retained on the same source-epoch snapshot, so utility
producers and renderers share one traversal of that member's native trees.
Namespace-location questions also share that snapshot, keyed by the consumer root
and source path. The import law remains their sole classifier; a captured
non-package result is reusable only within that same source epoch.
Runtime dependency facts are keyed by requirements and the interpreter import
path, not by the facade or mixin class through which the producer was called.
Both callers consume the same existing metadata owner and closure calculation.
The existing progress channel records each scope producer, utility producer and
renderer before invocation and on exit, with its wall duration and a completion
flag. A failed producer remains incomplete and its original exception escapes.
A timeout therefore identifies the unfinished producer without
mistaking an earlier completed log line for the current work.
The reverse-import producer receives the same snapshot inventory and native
trees for syntactic service pre-election and layer ranking. It retains its
member-scoped ancestry resolver; sharing syntax does not change import
resolution or merge homonymous internal packages across repositories.
Native staging serializes already validated rule mappings through the existing
JSON adapter, using JSON-form YAML rather than the generic runtime-value YAML
normalizer. A scan stage writes its elected rules as one native document stream;
global utilities remain single-document files. The same document writer serves
generated providers and staged fixture rules. Source catalogs and golden
snapshots are not rewritten by this optimization.
Fixture staging also groups its bound rules into one native document stream,
retaining every declared rule and test. Durability remains with the atomic
publisher; one publication replaces per-rule file and parent-directory syncs.
Internal scope metadata uses its declared JSON manifest: its derived selector
keys may be longer than a YAML flow mapping permits. The generated provider's content
identity hashes the exact serialized paths and bytes, including that format
choice, so a different encoding cannot reuse an older directory's identity.
Reusing a generated provider also verifies its complete physical inventory and
every expected file digest through the existing authenticated tree owner.
Directory existence alone does not admit a materialization; missing, unexpected
or altered entries fail before native execution.
Read-only member ancestry passes use the existing native project's frozen
layout context, reusing folder and module elections for that pass without
changing its consumer root. Facade component discovery obtains each holder's
member inventory once before comparing component bindings; it does not repeat
the same directory query for every member. Owned-member reference election also
captures each facade's member names once per census, rather than enumerating
the facade again for every owner/member/receiver combination.
Family-composition checks consume the same snapshot's native trees and shared
public-export reader. The source-text class-info reader delegates to its
parsed-module reader; composition does not reread and reparse each family member.
Authored catalog parses and provider mappings are memoized by their exact current
contents in process memory. The custom persistent parsed-catalog store and its
configuration are retired; native tool caches retain their existing contracts.
The ancestry inventory may reuse its member-scoped native module only when the
resource bytes and that module's source both equal the captured source. Proposed
or changed text keeps its existing native string-module path. This does not
combine member projects or change resolution of homonymous packages.
Source-module reads require the native source-bearing capability before using its
captured text. Callback admission uses Rope's native restructuring hook once;
the adapter counts observed/admitted matches there and leaves change computation
to the native implementation. It does not filter the same occurrence again in a
second change-computer override. Snapshot consumers use the shared source ports,
including their mutable-map value contracts, rather than concrete model classes.
Untyped SDK core and match results enter through strict native adapter admission;
the project subclass does not override SDK methods merely to replace their inferred
return annotations.
Documentation collection and pytest collection publish distinct manifest methods;
their different inputs must not collide in the composed utilities facade.

The joint loop consumes its returned post-phase scan instead of discarding it
and repeating the same scan. Semantic publication retains the canonical
publisher's acknowledged paths. CSV campaigns additionally return authenticated
post-publication states; their count must agree with the published file count.
An actual CSV effect refreshes the model and requires a new complete scan before
the loop returns its report. Empty campaign effects do not authorize stale input
reuse or waive the existing post-publication scan and cycle checks.

Current state (2026-10-25): the root `rename-plan` closure and the quadratic
scan-target discovery of the semantic source closure are being reduced under epic
`flext-1engx`.
