# Execution context

<!-- TOC START -->

- [Runtime is the authority](#runtime-is-the-authority)
  - [Post-install cold atomic resource ownership](#post-install-cold-atomic-resource-ownership)
  - [Native-bootstrap task route: flext-0029c](#native-bootstrap-task-route-flext-0029c)
  - [Catalog, Templates, and Semantic Refactoring Boundaries](#catalog-templates-and-semantic-refactoring-boundaries)
- [Canonical architecture checkpoints](#canonical-architecture-checkpoints)
  - [Mod Service, Workspace Sessions, and Receipt Verification](#mod-service-workspace-sessions-and-receipt-verification)
  - [Governance, Layer-0 Config, and Toolchain Repair](#governance-layer-0-config-and-toolchain-repair)
  - [Facade Projection and Model-to-Protocol Generation](#facade-projection-and-model-to-protocol-generation)
  - [Provider Election, Source Bindings, and Native Module Resolution](#provider-election-source-bindings-and-native-module-resolution)
  - [Recursive Component Composition and Holder Election](#recursive-component-composition-and-holder-election)
- [Namespace migration](#namespace-migration)
  - [Incremental Testmon and Primary Check Admission (ADR-029)](#incremental-testmon-and-primary-check-admission-adr-029)
- [New projects](#new-projects)
- [Environment activation](#environment-activation)
  - [Make Activation, Packaged Resources, and Hatch Wheel Packaging](#make-activation-packaged-resources-and-hatch-wheel-packaging)
  - [Producer Authentication and Cold-Import Verification](#producer-authentication-and-cold-import-verification)
  - [Editor Settings, Pyright Environments, and Tooling YAML Pairs](#editor-settings-pyright-environments-and-tooling-yaml-pairs)
  - [Mise PATH Composition and Beads Server Environment](#mise-path-composition-and-beads-server-environment)
- [Dependency locks](#dependency-locks)
  - [Member Lock Composition and Upgrade Guard (ADR-030)](#member-lock-composition-and-upgrade-guard-adr-030)
  - [Development Groups, Typing Policy, and Git Requirement Lines](#development-groups-typing-policy-and-git-requirement-lines)
  - [Deptry Detection, Dependency Repair, and Cold Initialization](#deptry-detection-dependency-repair-and-cold-initialization)
- [Runtime environment](#runtime-environment)
  - [Check engine contract](#check-engine-contract)
- [Mise toolchain](#mise-toolchain)
  - [Self-Managed Mise and Reality Proof (`mise-proof`)](#self-managed-mise-and-reality-proof-mise-proof)
  - [Generation Staging, Transaction Journals, and Modernization](#generation-staging-transaction-journals-and-modernization)
- [SonarCloud exclusions](#sonarcloud-exclusions)
- [Bootstrap credentials](#bootstrap-credentials)
- [Evidence and checkpoints](#evidence-and-checkpoints)
  - [Publication Receipts, Pytest Profiles, and Testmon Leases](#publication-receipts-pytest-profiles-and-testmon-leases)
  - [Architecture Checkpoints and AST Rule Catalogs](#architecture-checkpoints-and-ast-rule-catalogs)
  - [Rope Superclass Resolution, Lazy-Init Planners, and Candidate Overlays](#rope-superclass-resolution-lazy-init-planners-and-candidate-overlays)
  - [cProfile Thread Isolation and Performance Diagnosis](#cprofile-thread-isolation-and-performance-diagnosis)
  - [Candidate File-Effect Composition and Constant/Model Normalization](#candidate-file-effect-composition-and-constantmodel-normalization)
  - [Lazy Initializer Ownership and Transaction Failure Recovery](#lazy-initializer-ownership-and-transaction-failure-recovery)
- [Check gate partitions](#check-gate-partitions)
  - [File Gate, Pyright Diagnosis, and Stage Partitioning](#file-gate-pyright-diagnosis-and-stage-partitioning)
  - [CI Setup, Early Bootstrap Receipts, and Git Reference Migration](#ci-setup-early-bootstrap-receipts-and-git-reference-migration)
  - [Testmon/Toolchain Caching, SSH Gate Attestations, and Smells Enforcement](#testmontoolchain-caching-ssh-gate-attestations-and-smells-enforcement)
- [Census consumer evidence](#census-consumer-evidence)
- [Bounded Mypy failure status](#bounded-mypy-failure-status)
- [Abstraction-boundary project identity](#abstraction-boundary-project-identity)
- [Service foundation](#service-foundation)
- [Import normalization](#import-normalization)
- [Codemod scanner contract](#codemod-scanner-contract)
  - [`ast-grep` Scanner, Binding Inference, and Source Previews](#ast-grep-scanner-binding-inference-and-source-previews)
  - [Journal Footprint, Child Profiling, and CLI Route Selection](#journal-footprint-child-profiling-and-cli-route-selection)
  - [SARIF Receipts, Pytest Deadlines, and Duplication Assessment](#sarif-receipts-pytest-deadlines-and-duplication-assessment)
- [Workspace snapshot and analysis engine](#workspace-snapshot-and-analysis-engine)
  - [Single-Project Repository Snapshot and Memoized Facts (ADR-028)](#single-project-repository-snapshot-and-memoized-facts-adr-028)
  - [Profiling a root verb](#profiling-a-root-verb)
- [Related Documentation](#related-documentation)

<!-- TOC END -->

## Runtime is the authority

Generation must remain importable before repairing projections. Authored component
facades that share ancestors must impose compatible C3 precedence; reordering a
generated outer facade cannot repair contradictory component hierarchies. Repair
the authored composition first, then regenerate through `make gen`. Unresolvable
source ancestry remains an error, never a reason to drop a component silently.
An explicit base already inherited by another component follows that component
in the authored base list, preserving Python's subclass-before-parent precedence.
Outer compositions omit redundant direct ancestors when their declared components
already provide those capabilities.
Documentation components consume shared URL, scope and report behavior from their
base component, never from the outer facade that imports and composes them.
Extracting a facade must preserve its authored methods as well as its bases.
This includes the public Core operation-logging decorators used by generation;
an extracted payload helper does not replace the decorator's executable body.
The Git composition includes the declared-requirement source parser used by
repository discovery. Repository identity validation and dependency parsing share
that owner rather than duplicating URL normalization.

Make applicability is a layer-zero contract, independent of the configuration
singleton and its models. Configuration models and codegen consume the same
`make_contract` owner; importing it must not initialize `config`. This preserves
the acyclic configuration boundary required by ADR-005 during cold CLI startup.

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

The root has one native uv workspace and composes member locks per
[ADR-030](../../../docs/architecture/adr/030-member-locks-composition-upg-guard.md).
Root CI checks out its declared submodules and installs that same composed workspace
noneditable; `--no-editable` changes installation mode, not dependency origins.
Independent checkouts and member CI retain their own native project contracts and
committed member locks. Their locks pin the FLEXT distributions they consume.
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
current catalog declares `make tests` and the explicitly requested `make tests-full`,
without file or match inputs. The first executes persistent Testmon selection
once; the second executes the complete applicable population once without
Testmon, a preliminary incremental run or any cache read, lease or publication.
The existing database remains untouched. The operator's latest 2026-10-28
clarification is owned by
[ADR-029](../../../docs/architecture/adr/029-always-working-one-complete-cycle.md).
Both operations retain source admission, applicability, original failure and the
same complete invocation deadline. Historical commands
are receipts for their own source epochs, not aliases or executable instructions
for this catalog. An undeclared old target is corrected at the documentation
owner, never bypassed through raw pytest or another dispatcher.

### Catalog, Templates, and Semantic Refactoring Boundaries

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

Documentation templates resolve from the installed package resource owner exposed
by `FlextInfraConfig.ssot_config_dir().parent`, under `templates/docs/`, never
relative to the renderer module's position. The codegen catalog's `project` root
selects project scaffolding, not documentation templates. Rendering retains the
CLI's authenticated native template loader and source witnesses; a missing source
fails without creating directories or searching alternate roots.

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
Source ancestry resolves provider identities from their captured physical paths,
then the project's declared namespace discovery. Rope's shortened regular-package
name cannot replace that identity when a namespace ancestor has no initializer.
Member lineage, package ownership and component discovery share the provider-name
boundary with source ancestry; native external providers retain their own names.
Member classification uses the existing pre-assignment binding owner for class
publications. Native builtin ancestry follows the original builtin class, not the
identity of a Rope wrapper, whose superclass list may be empty.
Kind queries follow the source origin of value aliases as well as class aliases;
ordinary binding queries retain value declarations and their reference identity.
Annotations are classified on that proven origin before unknown inference is rejected.
Opaque binary exports are admitted from their installed stub declaration before
source-only alias traversal; a binary resource is never treated as Python source.
An annotation-only global in that stub declares a value, not a type alias. It
retains the constant owner; duplicate class/value declarations remain ambiguous.
Project dependency inspection and semantic Python transformations must use the
existing native project and its capabilities under
[ADR-028 Decision 17](../../../docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md#decision-17).
The owning `c/t/p/m/u` families provide configuration, vocabulary, aliases,
protocols, DTOs and adapters; composition roots inject capability-named contracts
into services instead of exposing library names. Preserve the same native model
and refresh affected resources incrementally; do not add a parallel parser,
semantic index or engine to compensate for repeated work.

Retire custom Python analysis or source rewriting through LibCST, regex or
independent parsing at the native owner, closing its consumers with public
runtime proof. FLEXT code consumes native scopes, bindings, objects and planned
refactoring changes; it does not interpret an AST itself, including one supplied
by Rope. Prove and report a missing SDK capability at its owner instead of
adding an AST walker, another parser or a fallback. These are target
contracts, not evidence that the remaining migrations or SourceView acceptance
have completed.

This boundary does not remove template generation, non-Python format parsing,
Ruff, ast-grep or other canonical check/fix/format tooling, and does not change
frozen gate policy. Generation must not import the analyzed project or require
its Pulumi SDK in the Infra runtime. Native extensions remain subject to the
supplied project's declared native-module election, without an independent
import-spec probe.

The Rope DSL import organizer constructs the installed native
`ImportOrganizer(project)` once per selected cohort and obtains each resource's
change through `organize_imports(resource)`. File writes narrow native resources
through the existing typed file-resource owner before publication.

Incremental workspace indexing accepts its prior typed index and changed paths
as one refresh request. Module evolution and package assembly remain in the
existing workspace-index owner; equal package records retain their prior identity.

Facade export readers receive the elected native source module. Unpublished
rendered source enters the same invocation project's candidate binding before
module lookup and export reading; that binding restores its entry candidate on
exit. A detached string module or a second project cannot supply this identity.

Semantic rules use the existing native contract catalog and its typed models,
protocols and constants vocabulary. The unconnected second Rope DSL interpreter,
its private declaration model and its unused operation enums are retired; they
had no Make entry point or configured consumers. New rules extend the active
owner instead of creating another execution pipeline.

Catalog document values remain a JSON-compatible mapping after their single YAML
parse. The loader validates its elected `RopeContractOrigin` separately and passes
that same operational metadata through `config_decode`'s typed document context.
Pydantic binds `owner_root` from that origin before its strict Path schema; no
Path is inserted into the parsed document. A textual rule cannot select its own
owner root, and a Rope document missing its required origin fails before effects.
Ordinary Python/JSON rule construction remains independent of document context.

Private-import export discovery receives the active workspace project through
its planner. Documentation contract extraction opens its existing native project
once for export assignments and symbol validation, passing that project through
recursive imported-assignment resolution.

Assignment docstrings likewise consume the source module elected for the
documentation check, preserving that project through recursive symbol and
inherited-documentation checks instead of reparsing assignment source text.
Their existing admission covers simple assignment names; the native reader
does not expand that documentation surface while replacing its parser.
Assignment lookup elects matching native name spans before resolving lexical
ownership, so unrelated declarations cannot trigger superclass inference.
Absolute import roots come directly from the elected module's native binding
index. That query retains guarded, nested, star and overwritten imports while
excluding relative imports; Infra no longer traverses syntax nodes for this fact.
Semantic capture regions come from the native match's public region query.
The runtime boundary retains its module-range check without fetching captured
syntax nodes or introducing a second interpretation of the match.

Documentation reads module, class and function docstrings from their elected
native objects' `get_doc()` methods. Local declaration admission still excludes
imported bindings; recursive public-symbol documentation owns import traversal.
Inherited class documentation follows the elected class's native superclass
identities, not a second parse of class headers and imported base spellings.
The rendered summary keeps its existing whitespace normalization at the docs
rendering owner. Source-only wrappers for those three SDK capabilities are retired.

Subfacade composition elects a source class's native member kind before visiting
its nested declarations or assignments. Entity roles remain declaration leaves;
their fields, members and bases are not flattened into namespace-supplier
evidence. Ordinary type holders retain recursive namespace discovery, including
empty holders and nested type declarations. This boundary does not remove an
entity or any model/protocol field from its owning projection. Unresolved native
ancestry still fails classification with its original cause.
Within one synchronous supplier-discovery invocation and its unchanged native
project, recursive discovery may reuse a nested class's classification only when
the current parent-scope binding resolves to that exact native owner. The caller
supplies no classification for a retained declaration whose name now binds another
object; that call uses canonical member classification. A supplied classification
with a different binding fails explicitly. This is the target reuse contract;
source edits alone prove neither runtime behavior nor profile acceptance.

String-sequence declarations use the elected module's native binding-index query.
Its nullable result distinguishes absent declarations from explicit empty or
invalid declarations. Direct module declarations win; `__all__` alone may use a
single direct class's metadata when the module declaration is absent. Export
consumers preserve that presence boundary before considering implicit exports.
The unused source-only class-base parsing wrapper is also retired; active
declaration readers retain their own elected native source boundary.
Unused source-only import-root and sequence-constructor parsing helpers are
retired as their active consumers already use the elected native query owners.
Inline-import hoisting is planned by its existing candidate owner and published
through that transaction; the unused direct filesystem-writing wrapper is retired.

A DSL consumer that updates one working source binds it through the existing
source-view owner. That binding retains the entry candidate's foreign/provider
plans and their original witnesses and modes; an owned-source mapping must not
silently replace the complete cohort. Explicit declarations still reject
competing bytes before the native view changes.

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

The existing `refactor apply-renames` package-bound mapping also covers bare
imported class references. Native qualified-name metadata authenticates each use;
the native workspace authenticates the destination before planning. Import and
declaration tokens and string payloads are not renamed. The existing publisher
adds the public receiver import and removes the unused private import. A competing
lexical receiver binding rejects the candidate rather than capturing another name.

A package destination in that same campaign retargets a composite's imported
member references to their native declaring class within the selected package.
Only consumers inside that package participate. Native definition resources and
lexical class scopes determine each destination, not facade-name conventions or
field maps. A declaration in the consumer's own module uses its local class name
without importing itself; siblings use their declaring package's lazy export.

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
source drift before publishing through the shared semantic transaction. A
candidate mismatch reports the differing candidate fields and the first differing
record's metadata field names, without logging source bytes or configuration
values. Ordered closure differences remain authentication failures; diagnostics
do not normalize, replace or exempt any persisted candidate field.
Each consumer retains its own native source-folder election, so independently owned
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
and receive only proven dependency effects. Workspace dispatch retains the exact
consumer selection on each declared member request. The common coordinate parent is not
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
Quoted relocation uses one native lexical-declaration map for before/after
validation, rewriting and final identity verification. Keys retain native ancestry,
AST declaration kind, name and same-name sibling occurrence, not breadth-first
cache positions. Declaration order, missing or added declarations and name capture
remain blocking. The installed Rope scope cache also contains synthetic
comprehension objects: only native `ListComp`, `SetComp`, `DictComp` and
`GeneratorExp` AST scopes are excluded from this declaration map, because their
expression grammar cannot declare annotations. An absent scope kind alone never
excludes a scope. The existing quoted-type selector still owns annotation positions,
including nested quoted types and typing-only declarations; ordinary strings,
lambda payloads, literal values and annotation metadata are not replacement targets.
Native annotation-scope rejection reports both declaration counts and the first
differing identity (bounded, without source payloads) in the primary exception
message, so CLI transports that omit exception notes retain the causal evidence.

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

### Mod Service, Workspace Sessions, and Receipt Verification

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

### Governance, Layer-0 Config, and Toolchain Repair

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

Rope DSL closed operation and transform vocabularies belong to `c.Infra`;
`m` validates the composed declarations, while `p` defines injected ports consumed
through Pydantic `t.Port` fields.

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

### Facade Projection and Model-to-Protocol Generation

Facade projection composes constants, utilities and models from the exports and
base order declared in their configured private family. Authored dependency ports
retain their consumer-owned capability contracts and normal `p` facade composition.
The accepted 2026-10-28 [model and service protocol projection](../../../docs/architecture/adr/018-generator-declarations.md#model-and-service-protocol-projection)
contract owns the automatic first-party projection, extending the model-to-`p`
restoration tracked by `flext-vjj1s.8`. Its complete native inventory and source
module ownership determine coverage and destinations; a consumed-model filter is
not the accepted scope. The ADR owns the structural data/callable distinction,
runtime boundaries, grouping, collision failure, pilot matrix and expansion order.
The operator explicitly authorized drift admission by coherent cohort on
2026-10-28, with pilots published and integrated before fleet rollout. The existing
transaction/admission owner implements this bounded change; it is not a new
projector, loop or a reduction of Python checker scope. Complete workspace
discovery/planning remains visible, and unadmitted cohorts remain explicitly
incomplete. Recompose the admitted candidate through the same planners rather
than filter a final global file list whose shared exports can reference pending
outputs. Staged validation is not evidence of a published pilot. Another pattern
waits for this entire pattern's fleet and consumer cutover, runtime/gates and
integration closure under the ADR. Beads owns progress; publisher receipts supply
evidence, not a second tracker.
The accepted DSL integration is `RopeWorkspaceDsl.protocol_projection()` with a
typed invocation-local projection plan, consumed by both generation and an
existing `ModLoopPhase.plan` callback. Share the invocation's authenticated native
session/snapshot across callbacks and refresh changed resources incrementally.
No fake static restructure patterns or per-symbol catalogs represent this dynamic
projection. The entry, callback, cohort policy and runtime receipts remain
implementation/validation work, not proven capabilities of the current engine.
Authored rewiring and obsolete-owner retirement run through `make mod`; its coherent
candidate includes dependent projection through the existing generation owner.
`make gen` continues to derive protocols and fails before effects if publication
needs an unplanned authored cutover. The ADR's retirement safeguard preserves every
consumer in that same candidate; prefix/header matching does not authorize deletion.
Neither operation invokes the other public verb. Protocol sources and every affected
workspace consumer converge with their facades and lazy exports through the same
publisher and read-only drift comparison. No target-package import, separate
scanner, per-model catalog or publication engine supplies the projection. This is
an accepted target; source restoration alone is not generation, pilot coverage,
gate or integration
evidence. The original MRO/Pydantic analyzer/environment plan remains incomplete.
The workspace snapshot and injected native candidate own source authentication;
the projector consumes their existing source-access contract, not a separate
project flag. Builtin annotation identities use the native semantic-module
adapter before attribute lookup. Private renderer helpers preserve that same
inventory, candidate and dependency closure without opening another project.
The utility path delegates
directly to the declaration planner. Static and runtime consumer checks retain
their own import-failure verdicts.
The native annotated-assignment query classifies explicitly annotated scalar values
as well as generic annotations. A proven name or attribute annotation remains a
value declaration even when its factory has no inferred return object; generation
must not reject an ordinary model field or treat that field as a component alias.
Unresolved or ambiguous annotation identities remain failures at the classifier.
The query reuses the native module's syntax and lexical scope; no independent parser
or source cache is introduced. AI Hub consumer qualification is tracked by
`aihub-6sls5.1`, with producer evidence on `flext-6b3zg`.

Generated protocol and model namespace assignments are derived output, not new
contract declarations. When an assignment resolves to an exact inherited class,
projection removes that binding and inherits the canonical private owners in C3
order, including their declared overrides. A stale renamed alias cannot publish
itself or shadow a different inherited contract. The generated ownership marker
and native class identity are both required; unrelated namespace members remain
unchanged, and contradictory authored class bindings still fail before publication.
An upstream owner containing the target class under another name does not prove
that the receiving namespace inherits that publication. Redundancy is resolved
against the effective same-named member of that namespace, not an arbitrary
attribute anywhere in its ancestors. Composed utility providers retain their
separate callable-cohort admission.
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
The final generated facade also prunes an unused typing guard import through the
native import visitor, even when its export declaration was already canonical.
Runtime-base discovery treats supplied planned bytes as authoritative, including
unpublished packages. Original-file reads and package membership checks retain
their native project-tree scope; planned initializer bytes own alias analysis.
Generated Ruff bases retain the qualified import spelling used by the consumer.
The provider's declaration identity remains separate from that reexport spelling.
Facade base retirement resolves imported member expressions from the lexical
import provenance visible at the class declaration, not a later module-level
alias assignment. The shared source-member resolver follows declared public lazy
exports and native C3 to return the actual declaring binding in the captured,
planned project view. Local scope, value shadowing, module-as-base, cyclic routes
and unknown bindings retain their native failure; spelling alone never proves
that a base can be dropped. No private import or live-disk replacement may bypass
that public source provenance.
Upstream import bindings follow [ADR-028](../../../docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md) Decision 10: preserve a used bare letter
or a source-proven existing alias according to the declaration's header references.
A later publication of the package's own letter does not alone require aliasing the
upstream import. Diagnose a static/runtime binding disagreement against the same
captured declarations and lazy exports before changing that election; an inferred
duplicate base does not prove that distinct native components may be removed.

### Provider Election, Source Bindings, and Native Module Resolution

The runtime-base inventory retains its exact native declaring module by reference
through binding lookup. A native module display name is not an import path:
search-root election may shorten it or collide with another package. Captured
providers are elected by exact resource identity in the supplied source mapping;
their planned bytes form the declaration and its binding together. Reopening a
provider by a reconstructed name, replacing planned bytes with original source,
or accepting ambiguous resource ownership is forbidden.
The inventory owns provider election for both lexical and runtime-base consumers.
Cached native modules retain identity only when their source matches the captured
bytes; resource equality alone does not authenticate a module cache entry. Derived
text receives a provider built from that capture, and explicit mismatched providers
remain errors. Both consumers pass the same request and elected provider explicitly.
Provider publication reads the completed source-binding inventory, including
declared lazy exports and assignments after class declarations, before using
native import inference. An explicit unknown source value is an error, not
permission to reuse an earlier import. This completed provider view does not
replace the declaration-line lexical view used to resolve that class's bases.
Literal dunder metadata on a bound provider does not bind or replace a class.
Recognize that metadata in both completed and conditional source inventories;
ordinary attribute rebinding still requires its declared class-namespace owner.
Instance attribute stores do not publish class bindings. Classify their receiver
through the elected native source provider and the current source-binding state,
not the assigned value or a library-specific metadata spelling. Native class
objects and source-declared class receivers retain namespace-mutation admission;
structural stores never become instance metadata exemptions.
Exception branches are inventoried independently from the same incoming bindings.
Equal references retain their binding. Differing ordinary function or value
bindings require native object-kind proof for every present alternative, including
unknown lexical values; absence is distinct from an unresolved value. A single
proven function alias remains available to later consumers without claiming that
its return value is a class. Differing class references and unproven potential
class origins retain fail-closed admission. Finally statements apply to the merged
binding state; neither import probing nor executing a branch establishes its kind.
Native value evidence retains literal RHS provenance: looking up a Boolean literal
as a module attribute may yield an opaque native builtin, not its expression type.
For source-function calls, the existing annotation-origin owner resolves the return
annotation in its defining native scope. A concrete builtin-backed data constraint
is separate evidence, never a fabricated instance or class identity. Metaclass and
universal-object constraints, unresolved aliases, and an actually inferred class
cannot receive that data proof. Function aliases remain unchanged for later factory
consumption. Native inference and source-declared return constraints are consumed
together; the annotation does not override a proven class result.
These native queries are public capabilities of the existing runtime MRO:
`call_data_return_constraint` consumes the canonical annotation-origin owner,
while `concrete_data_class` and `definition_location` belong to its lower native
query owner. Consumers use those inherited methods directly, without private
cross-class access, forwarding aliases or a second implementation.
Foreign attribute receivers are checked by their exact native expression binding,
including subscriptions, not by stripping the receiver to its root name. A store
without a source-declared or native class receiver does not invalidate unrelated
class identities; unknown inference does not manufacture a class receiver. Known
class receivers and structural stores retain mutation rejection. Protobuf's
standard builder publishes message descriptors and message classes under separate
bindings: descriptor serialization offsets are value metadata, not class bindings.
Generated protobuf sources remain in whole-code admission, unchanged by this rule;
neither generated headers nor descriptor names grant an exemption.
When a package has no explicit binding for a name, a native submodule of that
name remains a valid import provider. Resolve its remaining class path through
the same native source owner; an explicit value binding keeps precedence and
must not be replaced by a sibling file.
For an explicit `from . import child` source binding, Rope's imported-name
provenance and native child resource establish the submodule before following
its remaining class members. Re-entering the package's same import binding is
not a reexport cycle; completed class or value assignments retain precedence.
This applies even when the supplied source map contains only unrelated scripts:
the native provider's retained source and AST own its final publication. Exact
resource matches elect planned source owners; absent a match, use the captured
native source, never a fresh disk read or the earlier imported binding.
Completed inventories of uncaptured external providers use the collector's
external-provider mode, matching direct native class inventory. An augmented
value mutation becomes an unknown binding; using that value as a class still
fails. Owned resources and captured source declarations retain strict mutation
rejection.
Chained stores to known external class namespaces retain Python's single
right-hand-side binding. Admit every nonstructural receiver before updating any
member map, then apply that binding to each target in source order. A missing or
structural receiver still rejects the complete statement.
Uncaptured native class-constructor functions use the existing constructor
identity resolver. Their callable binding does not require inventorying unrelated
module mutations; captured source still owns any planned binding.
Native module election retains source resources before compiled extensions.
When no source resource exists, an extension import spec elects Rope's native
builtin-module representation at the project boundary. Semantic base resolution
uses that same election instead of constructing its own module representation.
Failed source-member resolution retains the original typed reference target,
attributes and qualified spelling as exception notes. Provider failures also
identify the selected native module, resource and matching captured source path.
These notes preserve the original exception and traceback; they do not retry,
drop members or substitute a different provider.
Repeated member queries within one captured source view bind one explicit
resolver port. Its source mapping is an immutable copy for that binding, and
its existing alias, resolution and C3 memoization remain local to the port.
The resolver retains that supplied capture by reference and derives one exact
path-to-owner index from it. Each path retains every module name in capture
order, including competing owners; the index neither resolves paths nor
normalizes aliases. Native folder providers still use their initializer path.
This index has the same fixed-capture lifetime as the existing derived state.
Rewritten source requires a new binding; no process-global resolver cache may
serve another native project or a changed source view.
The upstream-import pass and its following namespace-base queries reuse that port
when the pass returns identical source. A changed import starts a new source mapping,
native module and port together; it never mutates a mapping already held by a resolver.
Protocol owner additions use the same elected package name as their captured
declarations when inserting imports. A native module's shortened display name
must not introduce a new import root during the recursive projection pass.
Rendering a facade returns source only. Package-form imports require publishing
the owning family's initializer through the existing lazy-init planner before a
fresh consumer loads the generated facade.

### Recursive Component Composition and Holder Election

Recursive private domains use the same composition owner for every declared
`c`, `t`, `p`, `m`, and `u` family. A domain directory publishes through its
canonical sibling module: `_utilities/rope.py` composes `_utilities/_rope/`,
and `_rope/analysis.py` composes `_rope/_analysis/`. Existing public class
identities survive module relocation. Native source ancestry elects meaningful
providers; generated inheritance exposes their behavior without delegation
wrappers or duplicated entities. Opposing base precedence and competing owners
remain errors.

`plan_component_facades` stages domains deepest-first, their dependent
initializers, all root family facades, and the final package exports in one
candidate. Native ownership is elected from the observed-source snapshot before
pending initializer projections can withhold a still-consumed export. Moves and
consumer rewrites retain their original witnesses in the current candidate. An
unresolved observed owner remains an error, never an accepted native class.
Later rounds recognize a moved owner only through its recorded creation and
retirement plans and the canonical candidate's native composition proof.
Conformance and other callers inject the same
`FlextInfraCodegenLazyInit.plan_candidate` initializer capability. Module moves
authenticate any existing candidate against its declared `CodegenFilePlan`
bytes and original physical witness; lazy installer targets participate in the
same move as ordinary imports. A later physical edit still fails publication
CAS. Planning performs no target-provider imports and publishes no intermediate
source state.

Conform supplies its complete initial lazy plan through the existing
`provider_plans` state for that invocation, restoring the caller's state on exit.
Only the existing unchanged-input and foreign-provider predicate permits seed
reuse; actual facade or consumer effects still require export replanning.
Component composition consumes the caller's existing source-view capability.
The workspace snapshot owns the source-view factory, planned-folder election and
authenticated planned-source witnesses. Publication inherits that factory; native
workspace queries consume it directly without importing the publication facade.
The targeted `facades` surface authenticates its existing destination module and
published family before selecting that package's recursive family cohort. The
same component, initializer, import-normalization and candidate-admission owners
close that scope and all native move consumers; an explicit `None` selection means
all owned families. Unrelated family drift is not added to the selected cohort.
Native declarations elect an authored methodless composition beside or inside
its private child domain before any missing identity is derived. Suppliers must
come from other native domain modules, not the holder's own nested declarations.
An existing public namespace's native MRO authenticates its composition holder:
that holder's declaration-time class publications may supply its component MRO
without reclassifying ordinary type publications globally. Once the composed
receiver binds identical native callables and their consumer cohort is closed,
stateless method-provider publications retire rather than preserving compatibility
paths. Native entity and stateful-helper publications retain their declarations.
Native module moves retain the holder name, retire its old module and carry every
observed consumer and export effect in that same candidate.
Callable receiver rewrites admit only native load contexts. Assignment, deletion
and augmented assignment retain their mutation owner and block provider-publication
retirement when that owner would otherwise disappear from the candidate.
An inherited component is not a competing owner when another candidate is its
strict native descendant. Elect maximal owners by source ancestry; incomparable
owners still fail. An existing family `base.py` that is already the domain's
canonical sibling stays in place rather than being rejected as a relocation.
An authenticated composition already published at the canonical sibling takes
precedence over broader compositions that reuse its capabilities. Otherwise a
consumer's larger MRO could displace the domain's actual owner. Canonical location
does not waive the native declaration and supplier proofs above.
Once elected, an authored sibling keeps its declared path and class identity.
Only an owner inside the private child domain relocates to the canonical sibling;
without an owner, the declared project and family naming rules derive the seed.
Scanning sibling import text or ignoring read errors cannot elect an alternative
publication. Root-family `base.py` still cannot relocate to another domain.
An ambiguous election reports each candidate's native bases, declaration-member
suppliers and callable receivers separately, with bounded identities and total
counts. Only declaration-time bases and published members establish namespace
composition. Callable receivers are diagnostic consumer evidence, never owner or
containment evidence. If no authored composition exists, derive the canonical
missing facade; do not elect an unrelated caller to avoid creating it. A holder
whose declared suppliers span more than one private domain directory is a
family-root composition and never a single-domain owner; a declaration inside the
native child domain outranks an external composition, and the canonical sibling
outranks both. Relocating one family's elected owner must not retire a file that
another family's election also selected: multi-domain holders are excluded before
any move is planned.
An occupied destination without elected ownership still fails before seeding or
moving source. Its diagnostic records the elected path, class and source owner,
the candidate project's root, and bounded exported native class identities and
base origins from that same authenticated source view. Candidate/native source
agreement is reported as a boolean; source contents and native object reprs are
never included. Physical source alone does not prove candidate ownership.
Nested class composition supplies ownership evidence through its native ancestry
too: a namespace that exposes a derived nested contract consumes the contract's
base. Class-supplier discovery first classifies declared members through the
existing facade-member policy. Positively declared constant values do not become
class suppliers merely because their values originate in another domain module;
their ordinary value inference is not a facade-ownership prerequisite.
Its class name is retained when the native module move places that owner at its
canonical sibling. The complete source inventory, consumer rewrites, dependent
initializers and original file witnesses stay in one candidate. The root private
family's existing `base.py` is not moved or replaced to manufacture a namespace.
Within the repository planning scope, identical root and effective planned bytes,
including retirement tombstones, reuse the same native project and bindings.
Changed candidates bind distinct views before dependent families render; this
does not batch dependency-sensitive renders or replace original physical plan
witnesses. The caller retains snapshot authority and source-view teardown.

Generation, modernization, lint repair and read-only checks consume the same
import planner. The planner elects the nearest lazy publisher from the captured
exports and resolves inherited facade members through their originating
declarations. A facade's construction dependencies retain their upstream owners;
rewriting a consumer must not introduce a runtime cycle or change a referenced
binding. Imports, facade projections and lazy exports form one candidate before
publication. Unsupported or ambiguous bindings fail with their original cause.
Services receive this capability through a typed functional port; native syntax
and analysis objects remain inside the owning facade families.

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

### Incremental Testmon and Primary Check Admission (ADR-029)

`make tests` uses the persistent Testmon owner's native incremental selection over
the complete applicable population
([ADR-029](../../../docs/architecture/adr/029-always-working-one-complete-cycle.md)).
The 2026-10-26 operator order supersedes the forced complete-run behavior:
unchanged tests are not rerun merely because the verb was invoked again. Selection
and execution share one persistent database and aggregate deadline, with no second
execution pass. The common catalog has no manual
file selector. The explicitly requested `make tests-full` executes the complete
applicable population once without Testmon or an incremental pre-run, preserving
the persistent database untouched. It is a distinct operation, not an alias for
incremental execution. The 2026-10-26 operator priority
requires global Ruff and Pyrefly admission before native incremental pytest and
global pytest success before later phases (ADR-029). Produce original global
source-admission evidence with
`flext-infra workspace check --repository-root <root> --phase primary`, then use
`flext-infra workspace tests --repository-root <root> --scope all`. Generated Make
consumers use `make check CHECK_PHASE=primary` followed by `make tests`; bare
`make check` retains complete acceptance. An attached member's primary check
uses its containing runtime workspace, never member-only evidence. The primary
phase derives its gates from `make.check_prerequisite_gates`; the complete phase
retains the full configured check inventory and its context partitions. Both use
the same native checker, original capture and SARIF publisher. The test owners
consume the newest primary-phase receipt before executing native engines in
dependency order. Every test mode requires this admission. A direct diagnostic
`check run` report is not captured evidence. Missing, incomplete, red or stale
same-phase evidence refuses execution without electing an older success.
Admission diagnostics identify the required phase and direct recovery to that
same declared check phase. A bare complete check does not repair missing primary
evidence, and diagnostics must not suggest that it does.
Original invocation, policy, report digests, global topology and per-repository
source identities remain mandatory; primary evidence never proves complete
check or publication acceptance. Initial admission does not replace the final
completion-cycle tests. Mutating local operations refresh primary source proof
before complete check and final native incremental tests; the read-only CI
workflow reuses initial proof only while it remains current. These are separate
declared invocations, never a forced second pass inside one tests invocation.
Ordinary test failures preserve the first original status while every selected
repository is reached. Configuration failures escape unchanged. Existing
receipt-based operations retain their own admission contracts. Full applicable
checks remain required before completion and integration; a member-only receipt
never claims fleet completion.

Ruff's native findings exit is classified before policy can erase its explanation.
When the existing per-identity exemption owner authenticates every original native
diagnostic, the lint producer may report an effective clean execution while retaining
the original process status and verbatim output receipt. An empty native report,
unexplained findings exit, unauthenticated diagnostic, stderr failure, timeout or
signal never qualifies. Operational errors always fail the displayed gate verdict;
a green Markdown row cannot override an error in the original typed SARIF summary.
Receipt admission continues to consume that same phase-specific report and its
original byte bindings, never a fabricated receipt or an older green invocation.

The existing N802 settings-namespace exemption requires the callable at the exact
reported source position to be an own property of a class derived from the native
`typing.Protocol` identity. Its direct decorator must resolve to the builtin
`property` identity, and its name must be a genuine immediate settings/config
branch field. A matching field name alone never authenticates another callable,
an ordinary class method, an imported function alias, or a shadowed decorator.

Within a read-only check invocation, prerequisite gates run first, but their
failed verdicts do not suppress the remaining requested diagnostic gates unless
explicit fail-fast is selected. All native findings and receipts remain in the
same aggregate report; a fully measured red result is not an incomplete target
inventory and never becomes green. Interrupted execution still stops, and
mutating checks retain prerequisite admission. Missing project or gate executions
remain incomplete and fail closed. This diagnostic collection does not admit
tests, publication or any subsequent lifecycle phase on red prerequisite evidence.

The phase-aware Make and CI consumers are generated projections. Until the
updated template is published, use the native `workspace check --phase primary`
composition above; setting `CHECK_PHASE` on an older Make projection does not
select the new policy. Template edits alone are not rollout or runtime evidence.

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

### Make Activation, Packaged Resources, and Hatch Wheel Packaging

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
The generation CLI reports repository, planned-file and written-file counts from
its returned typed publication receipt. A successful repeated invocation with
zero written files proves that receipt's generated population required no effect;
exit status alone does not prove convergence.
Planning diagnostics without an exception remain failures. Publishing admitted
sibling outputs does not turn such a plan into success, and read-only conformance
retains the same planning failure even when its generated files are current.

Direnv confines its isolated Mise configuration directories to the native
activation subprocess. The activated shell retains the host's native shim
directory behind the project's resolved tool paths, so host-owned tools remain
available without joining the project's tool catalog. Project provisioning and
Make retain their own locked configuration boundary.

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

### Producer Authentication and Cold-Import Verification

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

### Editor Settings, Pyright Environments, and Tooling YAML Pairs

When the checkout owns the distributed configuration file, its project declaration
uses the derived `<stem>.project.yaml` file beside that default. The local layer
remains `<stem>.local.yaml`. This keeps project editor declarations separate from
the library defaults while preserving the same ordered configuration layers.

VS Code's `.vscode/settings.json` is a versioned projection of those declarations,
regenerated by `make gen`. Editor settings, `[tool.pyright]` configuration and
Git ignores use the same guarded file publisher. The root public Make interface
owns generation; the retired `make gen-editor` spelling is not an execution route.
Its `${workspaceFolder}` environment tokens remain
portable in workspace members, independent checkouts and linked worktrees.
The declared generation-time environment token resolves through the runtime
topology owner to a relative path anchored at `${workspaceFolder}`. Opening an
attached member alone still selects the workspace environment; opening an
independent project selects that project's environment. A nearby `.venv` is
never ownership evidence. Setup does not rewrite or untrack editor files.
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

Analyzer environment ownership follows
[ADR-003, Decision 5](../../../docs/architecture/adr/003-workspace-tooling-hub-distribution.md#5-analyzers-use-the-environment-owned-by-the-checkout-topology).
The 2026-10-28 approved correction is tracked by `flext-itpd1.13.11`: derive
Pyright's relative environment binding from checkout attachment, and bind the
mypy editor command to the opened interpreter with nearest-configuration
discovery. The approved settings are declared once in that ADR and projected by
the existing tooling/editor owners. A serialized path is not proof that imports
resolved through it. Acceptance exercises root, attached-member and independent
contexts and records the actual engine/configuration/import origin.

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

### Mise PATH Composition and Beads Server Environment

Activation loads the native `mise env --shell bash` output, which puts the
installed tool directories ahead of the host's shared shims. This includes the
self-managed Mise executable: a shim named `mise` otherwise invokes the host
release instead of the project release. The project-only registry selectors
belong to that environment evaluation, not to the caller's resulting shell.
After applying the native output, activation removes those selectors and puts
the existing shared shim farm last in PATH. Project-pinned executable paths
remain first; tools declared exclusively by the AI Hub host registry retain
their existing native shim and lock ownership. Make independently selects its
isolated project registry for its own lifecycle. This follows AI Hub ADR-0037's
host/project PATH composition without copying host tool declarations.
Activation does not install tools or
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

### Member Lock Composition and Upgrade Guard (ADR-030)

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

### Development Groups, Typing Policy, and Git Requirement Lines

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

### Deptry Detection, Dependency Repair, and Cold Initialization

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

Repair invocations execute their complete requested fixable-gate inventory in
declared order, with the same applicability and explicit fail-fast policy. The
read-only prerequisite partition must not strand pending repairs after an ordinary
failed verdict. Repair completion retains every actual finding and receipt; it
does not imply an independent read-only verification pass or project acceptance.
Interrupted or fail-fast executions retain unexecuted targets as incomplete.

Every gate assembles its result through one builder: the native output receipt is
published, every finding blocks acceptance, and an undeclared native outcome is
derived from the findings and the tool verdict.

The duplication and smells gates analyse all owned executable sources, including
generated Python in `src/`, `tests/`, `examples/` and `scripts/`. Generator markers
and generated-artifact catalog membership establish generation ownership, not
third-party provenance or an analysis exemption. Measuring a template does not
replace measuring its executable output. The license header remains the only
clone-content exception. Genuine third-party exclusions require canonical policy
paths and proven provenance; a directory basename such as `protos` proves neither.
The artifact's `generated_source` flag controls tracked generation ownership and
package-initializer production only. It does not feed analyzer exclusions, native
source-scan ignored resources, SonarCloud exclusions or module-cap exemptions.
Native discovery and gate targets admit owned generated Python, including modules
under `protos`, through the same configured source roots as authored Python.
The generated-module rule fact remains available for the specific static import
publication contract; it is not a blanket file-admission exemption.

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

### Self-Managed Mise and Reality Proof (`mise-proof`)

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

### Generation Staging, Transaction Journals, and Modernization

Local source binding remains part of `make setup FLEXT=<workspace>`. The frozen
UV installation is mandatory and continues to own the complete dependency
graph. The subsequent source-only pip step runs in the consumer's physical
Python environment and does not resolve a second graph. Dependency checking and
validation of each installed PEP 610 editable origin must succeed before the
existing selection receipt is published. No `--no-config` escape is used.
Additional installed distributions, such as the dirty Rope checkout, are
declared through `toolchain.editable_sources` in the existing local codegen
override layer. They must identify the same project name as their source
manifest and cannot conflict with the selected FLEXT workspace. Production
pins and locks remain unchanged; a plain setup restores the locked environment.

For the operator-directed causal repair of 2026-10-29, the original Make/gen/mod
plan remains active. Rope and the declared FLEXT suppliers are loaded editable
in the physical consumer environments at `~/ai-hub/.venv` and
`~/devops-oud-iac/.venv`; those environments are not borrowed from the supplier.
Installation uses the existing package installer against each explicit Python
environment, without changing production pins or locks. Reproduce the public
consumer command immediately after an owner repair. Auxiliary SDK probes do not
establish acceptance or justify changing Rope to accommodate an incorrect
consumer. Preserve valid WIP and establish which side violates its contract
before extending either side. This development installation is distinct from
the final locked-package, CI and integrated-runtime proofs.

The lint-freeze catalog retains entries outside a modernizer invocation's
observed project scope. It may replace the complete inventory only when the
observed project roots equal the declared operation roots, retaining missing
managed checkouts in that comparison, and the scan has no invalid paths. An existing digest
must not be changed or removed merely because the scanned document differs;
that drift requires the operator's rule-change authorization. Existing catalog bytes are
validated before use and retained as the original publication preimage; the
shared codegen publisher owns the update. This does not authorize changing any
frozen rule, scope, severity or tool setting. Missing or malformed evidence
remains a failure, and a partial refresh never proves fleet coverage.
The catalog location is declared by `make.lint_freeze_catalog`; the checker
uses its explicit repository execution root, never a search through neighboring
catalog files. The modernizer validates each rendered candidate against that
original catalog before writing the document. It cannot initialize a missing
baseline or admit a new entry from the current working tree. Initial baseline
materialization belongs to the generator's explicitly declared project inputs;
that bootstrap path still requires implementation and runtime verification.
Live document reads retain their original atomic file state by reference.
Publication includes the unchanged catalog observation in the same existing
publisher call as the candidate document, so both preimages are verified before
effects. Pure in-memory rendering has no physical witness and cannot publish.
Publication reuses the existing ordered multi-owner leases for the operation
root and every physical project owner in its plans. The catalog and consulted
configuration inputs remain unchanged observations in that same publication.
This protects the cooperating writers of the cohort; it does not establish a
global reader barrier or authorize replacing the frozen catalog.
Catalog keys use the manifest's declared project identity, not the checkout's
directory name; an independent clone or linked worktree preserves that identity.

The default `make gen` handler invokes the generation engine at `PROJECT_ROOT`,
with `all` scope locally and `self` scope in its declared CI context. A local
workspace invocation covers its root and declared members, while a standalone
repository has only itself. The request model's default remains
`SELF` for callers that do not select a scope, including file-only surfaces.
**Accepted contract, implementation pending (2026-10-28):** ordinary
projections, Mise artifacts, lazy exports and docs participate in bounded
dependency-complete transactions under campaign `flext-pipol`; see ADR-018
[single-read, single-batch publication](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/architecture/adr/018-generator-declarations.md#single-read-single-batch-publication-amended-2026-10-28-campaign-flext-pipol).

Native filesystem consumers that need both original bytes and a publication witness
use the CLI reader's joint `atomic_read_binary_file_capture` operation. Its
`AtomicFileState` and payload-free `AtomicFileReceipt` come from the same
authenticated descriptor observation, including parent identity and exact absence.
The receipt keeps the native version key and digest; it never stores original bytes.
This reader capability does not materialize directories or authorize publication,
and it does not replace the existing state-only or streaming receipt APIs.
Semantic class ancestry delegates to the installed SDK's native `get_mro` on
abstract classes, including builtins. Its C3 order, unresolved-base witnesses and
original hierarchy errors are preserved without a local walk or cache. The separate
direct-base query retains authenticated specialization facts; generic inheritance
must be qualified through consumers before this cutover is accepted.
Consumers requiring complete ancestry reject unresolved native entries before
classification or publication, identifying the source class. Missing SDK coverage
keeps those scenarios unqualified; a local parser or partial ancestry cannot replace
the native result or authorize publication.
Source-cut state (2026-10-29): the unused Infra generic-base ancestry helpers
and unresolved-base predicate are removed without a replacement walk. Component
ancestry admits every native MRO entry through the strict class guard; an unresolved
entry propagates its admission failure. SDK completeness and the original public
Make runtime remain pending acceptance under `flext-u9h2i`.
An incomplete-ancestry error includes the native MRO and immediate base witnesses
from the failing class itself. Those diagnostic observations neither filter the
witnesses nor supply an alternative ancestry calculation.
Facade-supplier diagnosis retains the nested owner's native binding, declaration
role, source project and ancestry identities from the same view. An unknown member
keeps its original exception and receives those observations as notes; names or
paths alone never justify treating a model field as a composition supplier.
Candidate overlays do not authorize converting hierarchy failures into a singleton,
empty bindings or unchanged source. A later pass in another project cannot attest
the current candidate's ownership or import-retirement proof.
Codemod utility requests sharing a library use one complete native classification
within their existing workspace snapshot. Requested facade letters select from that
classification; they do not trigger independent scans or omit unknown public members.
The same producer collects its catalog prefixes together, preserving every requested
identity and the original classification failure. This operation-local sharing adds
no cache or secondary index. Its performance and document equivalence require the
same public `make mod` reproduction; source consolidation alone proves neither.
One native project retains unchanged observations and refreshes changed
resources and dependent facts incrementally in the same engine. Candidate
validation, publication, index/mode/directory effects and refresh share the
existing publication owner. ADR-018 defines the barrier before live Make/Rope
reads, protection of later lazy reads, durable interrupted-state admission
and narrow CAS rollback of the failed transaction's own effects. This gives
atomic visibility to cooperating readers, not operating-system atomicity
across files or an invocation-wide rollback promise.

An external edit invalidates the affected candidate; reading a new preimage
immediately before writing is not permission to adopt it silently. Preserve
foreign WIP, completed independent transactions and the original causal failure.
Failure stops dependent execution; unreached work remains unexecuted. These
obligations supersede the historical no-preimage-restore wording only for
authorized owned-effect rollback. Existing journal mechanics below are
implementation context, not proof of the accepted transaction target.
Generated output must already satisfy STRICT at its template/renderer;
post-render repair or formatting is not admission. The owner is
[ADR-028 Decision 8](../../../docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md#decision-8).
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
an `OK` planning row never attests publication. The managed executor retains
the first failure and confirmed effects; it does not continue publishing
bootstrap, lazy-init or documentation targets after failure. Secondary
diagnostics never replace the original cause. Incomplete receipts retain
failed and unreached work alongside completed transactions and cannot
qualify as complete.

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

Dependency modernization and conformance derive distribution roots and packaged
data through automatic detection of the project's own declarations — the typed
`config/workspace.yaml` declaration was exterminated in `flext-a0cjp`, and no
legacy list or inventory replaces it.
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

### Publication Receipts, Pytest Profiles, and Testmon Leases

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

### Architecture Checkpoints and AST Rule Catalogs

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

### Rope Superclass Resolution, Lazy-Init Planners, and Candidate Overlays

Generated facades compose declarations published by their current private family.
Explicit class-owner recognition and rendering resolve each declaration through
the physical path in the authenticated source map and its native Rope resource.
The declaration's import spelling indexes that captured map; it is not a fresh
global module election. Separate packages may share an import spelling without
sharing a physical provider. Neither basename matching, reconstructed module paths
nor fallback lookup may replace the captured resource identity.
Lazy aliases use the captured alias inventory and the provider's native source
bindings. A missing indexed provider or declaration remains a resolution error;
walking physical ancestors or rereading an initializer cannot repair that epoch.
An authenticated final local class declaration is elected before evaluating an
earlier import that the candidate replaces. Native lookup is performed only
when that election still requires it, and its failure is never normalized.
The resolver propagates the original failure instead of reporting a skipped
binding and returning an unresolved placeholder.
Namespace bases are read through the native source class's `get_superclasses()`
on the authenticated candidate module. Rope evaluates its original header AST
in the defining parent's lexical environment, before namespace-body bindings.
A separately parsed AST has no native node-identity context and must not replace
that lookup. Every declared base must resolve; an omitted native superclass is
an error, not permission to drop a base. Same-name class publications inside the
namespace remain authored bindings and do not change header lookup semantics.
Metaclass source bases such as `type(Protocol)` use that captured module's native
source-binding context at the original expression offset. The SDK evaluates the
complete expression and supplies the actual metaclass object; Infra admits it
through the existing native-class contract and retains its declaring module and
complete nested class path. Resolving this source fact never imports the target
module or reflects on a target runtime class. Local and external source owners
follow the same native identity contract. Missing inference, class identity or
declaring provenance remains a failure, without a package-name exception.
The existing native object identity conversion is owned by the runtime module
utilities as `native_object_identity`. Source inventory and metaclass base
resolution consume that same conversion. It preserves the original native scope
path and builtin class metadata; the former private inventory helper is retired
with its callers rather than retained as a second route.
Ancestor traversal admits both source and builtin SDK classes through the existing
native-class contract. A genuine builtin may have no ancestors; an unresolved
object is rejected rather than treated as that builtin leaf.
The class query protocol requires native superclass and MRO queries, without a
source-only mutation capability. Component and model-protocol ancestry consume
one native MRO result and admit every entry through the strict class guard.
Read-only ancestry queries never invalidate bases, retry resolution or filter an
unresolved witness; the original admission failure escapes unchanged.
Upstream import collision checks use that same declaration-time binding for
every nested class header. A preceding enclosing-class binding still reserves
its name; an already imported alias for the same captured owner does not.
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
Component composition uses that same admission: a rejected base stops the whole
query and retains its original exception, never a partial ancestry result.
Native startup imports Core utilities before planning. A syntax error in an
authored declaration means generation has not run. Repair its minimal bootstrap
declaration without changing tuple arity or parameter separators, then repair the
rewriter's candidate validation at its owner; do not substitute an older runtime
or bypass the import. Annotation rewrites must preserve surrounding punctuation
and validate the complete candidate before publication.
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
An unavailable provider is never replaced by the first sibling declaring the
same class name, whether that sibling is found in candidate strings or on disk.
Class moves must publish their native consumer rewires in the same candidate
before dependent base projections run. The external-reference owner reads the
module elected by the injected project and retains its resource identity; a
missing provider or failed binding escapes unchanged. Captured file contents and
lazy-export aliases are not evidence of an old-to-new declaration relationship.
The same epoch rule applies to ancestry and initializer bindings. A candidate
cannot borrow a physical initializer's old export or a physical class's old
superclasses after its own resolution fails. Native hierarchy errors propagate;
an unresolved ancestry witness blocks decisions requiring complete ancestry.
Component ancestry follows native C3 order rather than a separate superclass
walk, and a failed member lookup never means an empty public surface.
An ancestry failure cannot reclassify a class as a function or another role.
Repair the candidate's declarations and consumer rewires, then recompute its affected
native facts before publication.
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

### cProfile Thread Isolation and Performance Diagnosis

The sole clock implementation is the stdlib-only
`flext_infra._pytest.clock` owner. Public lazy exports retain
`FlextInfraPytestClock`; they do not require a duplicate root-level implementation.
The profiled-child transport resolves the top-level package spec without importing
its runtime, then follows every relative component of the configured clock module
to its Python source file. It loads that canonical file directly, retaining the
same signal callbacks, owning-thread profiler and native publication behavior.
Flattening a nested module to a root filename is not a valid bootstrap route;
missing canonical source remains an error rather than selecting an older copy.

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
capture is incomplete failure, never successful modification. The active Make
deadline includes startup, preflight, lock waits, children and termination within
sixty seconds. Reserve termination time inside that bound and use an enclosing
deadline when the native operation has none; do not allocate a fresh budget to
each stage. Capture repair alone proves neither a timing improvement nor a green
generation, modification or gate result.

Rendering and filesystem preparation preserve their original exceptions and
tracebacks. Publication returns the existing atomic writer's typed Result
directly, without rebuilding its success payload or failure metadata.

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

### Candidate File-Effect Composition and Constant/Model Normalization

The exhaustive-enum contract action resolves each reference through the installed
Rope source-binding index's token context, including class headers and shadowed
aliases. Structural class scopes establish field ownership; they do not replace
the token's binding environment. Annotation payload protection uses absolute spans
from the authenticated complete module, observed once per invocation alongside
references and statements. All domain/default proofs precede candidate import views.

Candidate file-effect admission reports duplicate destination paths with bounded
producer ownership, original and desired byte digests, modes and tracking metadata,
never source payloads. This diagnostic consumes the declared plans already in memory;
it does not reread physical files. A duplicate is not proof of a sequential producer
chain: composition must authenticate that chain and retain its original physical CAS
witness before admission. Independent competing desired contents remain failures.
Managed generation and documentation can independently declare the same unchanged
`pyproject.toml`. Before normalization, their shared file-plan composition owner
coalesces only effects with equal project, complete original source state (including
lexical source metadata), ownership, policy, tracking, index witness, desired bytes
and desired mode. It retains the first original witness by reference and unions
tracking dependencies in producer order. Hash equality alone never admits a plan.
Only explicitly ordered, source-derived projection composition may advance desired
contents; independent documentation effects cannot claim that lineage.
Every mutable candidate index stages declarations through that same composition
owner before replacing an entry. Ordered stages may advance desired bytes and mode,
but never original witnesses or publication authority. Peer declarations, including
same-depth domain moves, compose unordered before joining the ordered candidate;
different peer effects conflict. Semantic seed edits retain preceding declared-plan
metadata through the canonical semantic-edit conversion. Only genuinely absent
sources use the creation path.
When complete generation invokes documentation, it supplies the composed managed
file plans to the presentation-metadata producer. That producer projects the locale
leaf from the candidate's desired bytes, not the physical pre-generation manifest,
and retains the original witness, publication metadata and dependencies. Only these
explicitly derived metadata effects join the managed plans as an ordered phase;
independent rendered documentation effects retain strict identical-effect admission.

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
provenance,FlextInfraUtilitiess, assignment identities and inert literal discovery
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
Before facade model-owner validation, generation may repair exported singleton
model entities declared directly in model-family modules through the existing
class-nesting engine. This bounded entry uses
the authenticated candidate's repository workspace and native model ancestry;
it does not run helper promotion, family flattening or unrelated nesting. The
entity retains its name, bases, fields and methods inside a same-named namespace
holder. Native identity consumer rewrites and structural edits join the shared
source plan with their original CAS witnesses; generated consumers remain excluded
and are regenerated after rebinding. No intermediate publication, parallel project
model or recursive public operation participates. Runtime acceptance remains with
the coordinator's serialized generation and gate cycle.
Fieldless namespace declarations are not singleton entities merely because they
inherit a model preset. Before wrapping, the same semantic owner proves that the
declaration contains only nested payload models and inert documentation, has no
decorators, class keywords, type parameters, fields, configuration or methods,
and directly inherits the exact native canonical arbitrary-types model preset.
The existing wrapper consumer census must prove no constructor, type, base,
value or inherited-member use, including quoted annotations. Only then may its
incorrect model ancestry be removed. Arbitrary custom bases are never discarded.
A plain holder containing that same-named, otherwise pure model namespace is
recovered by the existing identity-bound wrapper promotion and source-region
unwrapping machinery, without prefixing or copying the nested payloads. All
payload declarations, defaults and subtype relationships remain unchanged; the
facade regains those members through canonical holder MRO. Real entity uses
block promotion, and field-bearing singleton entities retain their nesting rule.
The existing seed owner rebinds its authenticated source view between private
repair epochs until no source edit remains, retaining original file witnesses
through every epoch and rejecting repeated nonconvergent candidates. Namespace
normalization and real entity nesting therefore complete before facade validation
in one unpublished candidate, even when both shapes occur in one repository.
Selected model-facade planning restricts declaration repair to its admitted package
while retaining the repository's authored consumer population; selecting another
family does not schedule model repair.
Family discovery returns textual catalogue letters; singleton admission compares
their values, not object identity with the facade-family enumeration. This
selection precedes native model-ancestry proof and never replaces it.
The rule catalogue belongs to the elected repository root, not the physical Rope
workspace root that an attached member shares with its containing workspace.

Typing-alias relocation plans the declaration, destination and consumer changes
before one protected publication. Explicit imports retain their lexical scopes
and local bindings. Unsupported references, ambiguous bindings and uncertain
star exports reject the entire move before publication, including creation of a
previously absent destination. Quoted type expressions participate in semantic
identity checks; ordinary strings, `Literal` values and `Annotated` metadata do not.

Parent lookups share one canonical owner: the family-leaf `rope_ast`
`ast_parent_map`, keyed by child node id with native AST-node values. The leaf
imports nothing from the rope family, so runtime members load it at module top
level and analysis members inherit it; per-module `ast.walk` parent-map
constructors and deferred family imports are consolidation defects. Consumers adopt
the native identity-keyed contract instead of retaining a private key shape. Module
relocation compares quoted-annotation scopes through one lexical identity map
(ancestry, native kind, AST kind, name and same-name sibling occurrence), not
positional correspondence; Rope's cached synthetic comprehension scopes are
excluded by their native AST identity, and every declaration, ordering, capture
and module-identity change still fails the move.

### Lazy Initializer Ownership and Transaction Failure Recovery

Lazy initializer planning publishes only explicit exports of a package's direct
declaring modules. A child's `__all__` never adds symbols to an ancestor
initializer, regardless of the family, source tier or directory depth.
`child_packages_for_lazy` records importable direct child packages as metadata;
it does not authorize reexports. Explicit facade letters and inherited serving
contracts continue through the existing letter election. Authored initializers
retain their declared publications and content.

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

### File Gate, Pyright Diagnosis, and Stage Partitioning

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

The retired `check-pyright` and `mod-types` Make subverbs, including their former
member-Makefile dispatch examples, are historical interfaces. Use the active
root's selector-free `make check` for declared Pyright validation and native
reports, and `make mod` for the existing semantic transformation pipeline.
Missing declared coverage is repaired at those owners, never by reviving a
subverb or manually selecting a member Makefile. The native engine verifies rule
fixtures, resolves bindings and repeats safe rewrites to its fixed point.
Source models and protocols own the resulting contracts: consumers pass
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

### CI Setup, Early Bootstrap Receipts, and Git Reference Migration

CI setup reconciles the owned physical environment through locked, noneditable
installation, including an existing venv. Root CI checks out declared members
before installing the composed workspace lock per
[ADR-030](../../../docs/architecture/adr/030-member-locks-composition-upg-guard.md);
member and standalone CI retain their own committed member lock and project contract.
The CI token does not replace native source
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

### Testmon/Toolchain Caching, SSH Gate Attestations, and Smells Enforcement

The ordinary `tests` operation uses incremental Testmon selection
([ADR-029](../../../docs/architecture/adr/029-always-working-one-complete-cycle.md)).
The explicit `tests-full` operation executes the applicable suite once without
Testmon, an incremental pre-run or database access. Marker applicability remains
owned by the declared execution context; neither operation invents exclusions.
The incremental filesystem cache lives at the typed XDG/HOME-derived project path
and full execution leaves it untouched.
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
Green-check reuse receives its global-target planner through the required typed
`p.Infra.GlobalCheckTargetPlanner` callback. The pytest composition supplies the native
checker's `plan_global_targets` operation; the Git evidence utility never imports the
checker. Admission invokes the callback only after original execution and complete,
unfiltered SARIF coverage have been admitted, retaining the first-failure order before
topology comparison and candidate freshness. The native checker remains the sole
topology and applicable-gate planning owner; no caller-authored target inventory or
optional planner fallback substitutes for it.
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

The existing `refactor census` request also accepts explicit `consumer_roots`
and an optional `source_plan_output` destination for the authenticated
`SemanticSourcePlan`. This invocation remains read-only: `--check` or the
existing dry-run mode must be selected before collecting external consumers or
exporting the source plan. The same captured native closure feeds both census
evidence and the optional artifact; exporting it does not start a second source
scan or require a placeholder rename decision. The ordinary census contract is
unchanged when neither option is supplied. External roots remain exact request
inputs and never expand through an implicit host-wide inventory.
Source-only capture returns that authenticated closure directly; it does not
enter declaration-renaming analysis or recapture the same candidate. Explicit
rename plans continue to require real, nonempty naming decisions.

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

## Import normalization

The import-law utility owns one source planner for generation, modification,
lint repair and verification. It consumes the existing workspace snapshot and
proposed source cohort through a functional port; native source-engine objects
remain inside the utility boundary. Applying operations publish its typed file
plans through their existing journal. Verification reports the same pending
changes without publishing them, and no operation invokes another public verb.
Batch consumers use `u.Infra.plan_import_normalization`; single-source lint and
semantic callbacks use `u.Infra.normalize_import_source`. Both public capabilities
compose the same import-law implementation through the utility facade.
Batch callers supply their existing `declared_files` plans explicitly, including
retirements; a live cohort supplies an empty tuple. Both planning and runtime-cycle
verification retain those tombstones and their original file witnesses.

Concrete class imports use the nearest package that actually publishes that
source identity. Application modules consume their local facade when its native
MRO includes the imported provider and the consumed member paths resolve through
that composition. Declaration families, facade construction, bootstrap inputs and
runtime dependencies that would introduce a cycle retain their original provider.
Import aliases keep their lexical binding. Unknown origins, conflicting owners
and incompatible member paths fail before publication; a matching letter or
directory name never proves identity.

Before boundary validation, normalization may repair an own-family facade import
only when its published provider belongs to that namespace's family. A root
publication that forwards an upstream facade retains the upstream identity;
sharing the same facade letter does not make it an own-family dependency.
Native member identity must also prove every consumed reference's declaring
owner and its nearest published export. The semantic cutover owner preserves
lexical bindings and the original import's typing-only placement. Same-module
owners, unresolved identities, captured bindings and unsupported quoted annotations
remain blocking and require the canonical structural `make mod` route; generation
does not relax the own-family ban. The rewritten candidate is reparsed and subject
to the unchanged boundary, placement and native runtime-cycle validation.
Corrective imports are emitted as separate native statement lines, never as
semicolon-separated small statements. This preserves each import's physical span
for subsequent line-based placement, including when runtime reads promote only
some imports out of a typing guard. Leading and trailing comments remain attached
to the rewritten statement group; no empty guard is masked with a synthetic pass.

Deferred class annotations stay typing-only when native source ancestry proves
ordinary class construction through `object`: undecorated declarations, no class
keywords and no class-construction hook. Inheritance alone does not make annotations
runtime reads. Decorated, metaclass-driven and unresolved external classes remain
runtime-sensitive. Initialized `Final` alone does not exempt a field, because
dataclasses can consume it. Reverse-import failures report runtime-read positions.
Family ownership comes from catalog-declared private directories or a facade module
at its namespace root, not a similarly named test category such as
`tests/unit/utilities/`. Bare nested categories do not assign an import layer.

## Codemod scanner contract

### `ast-grep` Scanner, Binding Inference, and Source Previews

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

The strict `AstGrepDiagnostic` model owns severity as `NativeRuleSeverity`.
Scanner JSON is parsed once with `AstGrepReport.model_validate_json`, which admits
the native severity strings. Python construction requires enum instances: passing
a raw Python severity string raises Pydantic's `is_instance_of` validation error.
Owned-path findings therefore supply the enum directly, and the gate preserves
their validated model instances. The latest preset target uses
`use_enum_values=False`: validation and Python dumps preserve the enum member;
native JSON serialization emits its string value. JSON-compatible dumps are
output data, not strict Python constructor input. Consumers pass the validated
diagnostic by reference instead of reconstructing it from a dump.
Invalid strings and Python bytes remain errors. ADR-005 and ADR-028 Decision 14
own this newer enum-preservation contract; native validation remains required.

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

### Journal Footprint, Child Profiling, and CLI Route Selection

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

The generate and conform command declarations belong to the codegen handler
family inherited by the public API. Their request models and caller-bound
handlers supply the existing CLI result-route contract directly. The CLI
formats the typed receipt only at its output boundary; API callers retain the
original receipt and the caller's settings, context and injected ports.
The shared CLI result-route factory receives the framework-validated request
instance without serializing or revalidating it. Failure metadata and causes
retain their original Result boundary, and no success marker replaces the
operation's receipt before formatting.

Generation's public execution class is
`codegen.FlextInfraCodegenConform.Generate`. Bootstrap and tests consume its
inherited planning and execution methods through this facade. The private
execution part remains an implementation supplier and has no public export.

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

### SARIF Receipts, Pytest Deadlines, and Duplication Assessment

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

Recursive component facades use the existing family declaration renderer and
native C3 ordering. Each private component domain publishes through its sibling
module and the child package's generated initializer. Discovery follows the
declared facade family and source ownership, including nested domains; it does
not maintain a separate directory or class catalog. Existing authored
declarations retain their identity and behavior.
An owning composition's base order is part of that semantic contract. Two
individually valid domains can impose opposite precedence on shared ancestors,
making their generated aggregate impossible to import. Repair the contradictory
owning composition and preserve its consumed capabilities; do not hand-reorder
the generated root, drop a capability, or suppress the native C3 failure.
Generation must retain a jointly valid ancestry for dependent facades before
publication. A failure while importing that aggregate does not prove any gate ran.
Native composition ownership includes both domain superclasses and published
class members supplied by that domain. A facade that publishes input entities
through aliases retains its authored identity and nested declarations.
Supplier admission reads native declarations lazily; it does not infer every
inherited attribute to establish a direct domain publication.
Within one unchanged candidate, domain-owner election retains the exact member
suppliers authenticated during admission for its subsequent composition comparison.
This reuse ends with that election call; it neither skips the initial integrity
checks nor adds superclass or callable suppliers to the comparison's evidence.
Member classification receives an operation-owned lazy factory for the existing
native member resolver. It captures the same declared source mapping and constructs
that resolver only at the first model-contract query. Subsequent queries reuse its
native resolution state, not cached declaration kinds. Exception, enum and protocol
classification still precede that query; unresolved contracts, empty contracts and
invalid ancestry retain their failures. The factory is discarded when its operation
or captured source view ends, never retained across publication or source changes.
The method admission predicate reads the class's cached native AST, including
conditional definitions and excluding methods owned by nested classes. Native
member bindings are evaluated only when superclass suppliers do not elect it.
Domains at one depth stage their seeds together before one dependent initializer
pass; shallower domains then consume the completed child publications.
An unchanged module owner retains its captured native view while seeding.
Actual module moves rebind their candidate before the seed consumes it.
Provider reexports retain Rope's imported-name provenance through resolution.

One generation process runs several publishing surfaces. The workspace snapshot
records each source's read state once; after a surface publishes effects, the
executor rebases the recorded states of exactly the written paths, so a later
surface verifies its plans against the bytes this run wrote. External mutations
still fail the unchanged-file proof, because only the run's own publisher may
rebase. CLI failure rendering emits native exception notes (owner, base index,
inferred kind, scope identities) after the message: producers attach the causal
annotations, and dropping them turns a precise diagnosis into a bare string.
The existing captured-source override decides rebinding before the imported
module is elected; a declared leaf import does not restart at an ancestor
package and mistake namespace traversal for a provider cycle. Campaign
`flext-pipol` (2026-10-28) owns the accepted, implementation-pending
single-read contract across lazy planning, model→protocol and docs: reuse
unchanged observations in the same native engine, refresh changed resources
incrementally and retire routes that reopen projects for later phases.

Component-call correction follows the same native family composition through
all ancestor components and nested namespaces. It rewrites a direct component
method call only when the bound public facade resolves the identical callable.
Class construction, base expressions and entity/type references retain their
existing declarations. Consumers without a bound facade and calls within the
owning private family require the separate semantic receiver cutover; textual
class-name replacement does not authorize those rewrites.

The API composition root binds the component and import planners through
`p.Infra.CodegenConformPorts`, using the public utility facade. The orchestrator
passes the same typed candidate and snapshot to those injected capabilities.
The component planner receives the existing initializer planner by reference;
it does not construct a second lazy-export implementation.
It retains original physical witnesses, additions and retirements through each
fresh candidate view, and returns file plans to the same atomic publisher.
Domain discovery uses the snapshot's repository ownership inventory, so nested
members retain their own generation pass while remaining native import providers.
Dependent child initializers and the root family facade belong to that same
candidate before runtime acceptance.

| Infra declaration | FLEXT architectural declaration |
| --- | --- |
| This subproject's Workspace snapshot and analysis engine section. | [ADR-028 Decision 17](../../../docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md) |
| ADR backlink to this exact Infra section. | [ADR-028 bidirectional traceability](../../../docs/architecture/adr/028-facade-boundary-orchestrators-declarative-enforcement.md) |

### Single-Project Repository Snapshot and Memoized Facts (ADR-028)

The complete same-engine incremental refresh contract below is accepted
and pending implementation/runtime proof. Dated partial-implementation
observations do not attest fulfillment of that contract.

The operator-approved 2026-10-28 STRICT campaign starts with the documentation
and Bead alignment described in
[ADR-029](../../../docs/architecture/adr/029-always-working-one-complete-cycle.md#current-state-and-recovery-order).
`flext-brr3y` tracks the campaign; `flext-ir794`, `flext-jskve`, `flext-s9r3a`
and `flext-1engx.15` keep their existing bounded responsibilities. A command that
cannot import its implementation has executed no downstream gate. Only the
causally necessary bootstrap repair belongs to that initial documentation
delivery; structural application waits for its native acceptance.

In the subsequent discussion about moving the incremental repair before
documentary publication/validation, the operator replied, "continue para
executar o plano até o final". The adopted execution boundary advances only
the causally demonstrated candidate-planning repair needed to publish and
validate those documents, after the affected owners are aligned. S0 remains
open through native documentary acceptance. This continuation does not waive
the specification: post-publication rebase and atomic-publisher receipts remain
separate S3 obligations and do not explain or prove repair of the present
planning timeout. Pilot order, complete gates, budgets and the analyzer freeze
remain unchanged.

The approved rollout qualifies three peripheral pilots, one dbt, one tap and
one target, before structural foundation rollout. Their identities and proof
belong to the active plan and Beads, not a fixed project list in this guide.
The completion and admission owner remains
[ADR-029](../../../docs/architecture/adr/029-always-working-one-complete-cycle.md).

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

The native project's identity remains stable across candidate bindings; identity
alone therefore does not authenticate a derived memo. Derived facade census and
resolver observations belong to the active source binding, rather than a
process-global `id(project)` key. Reuse the native parsed facts and their own
invalidation; do not add another versioned cache or counter merely to preserve
that stale memo. Physical before-images remain authenticated separately and are
never rebaselined by a candidate transition.

Source-base lazy declarations read the bound candidate through the injected
project's authenticated source access. A captured module path identifies its
declared owner and takes precedence over native election by import spelling;
only modules without a captured owner use the native elected resource. Earlier
captured text never replaces missing candidate bytes. The
resolver retains a lazy declaration inventory for that binding, including an
absent name, rather than discarding it and rereading live files. Namespace
descent uses captured module identities and native module election; it never
constructs a sibling filename from a namespace segment. Physical publication
witnesses remain owned by `source_state`, separate from candidate `source_text`.
This correction still requires the original public runtime and native gates;
source changes alone provide no acceptance receipt.

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
Declared facade parents outside that inventory resolve through the bound native
project's elected package resources, including the consumer's admitted editable
suppliers. They remain read-only inputs, never additional plan targets. Namespace
spelling does not establish a sibling directory; do not construct substitute
paths or run another ambient-import election beside the native source model.
Local FLEXT setup binds only the selected distributions after frozen installation.
That source-binding step uses native no-dependency installation and then native
dependency compatibility checks before publishing its selection receipt; it never
re-resolves third-party dependencies or replaces the consumer's locked SDK origin.
The setup composition must load this declared source owner in the same physical
consumer environment, including on a cold installation, without Python-path shadows
or borrowing another workspace's interpreter.
After frozen provisioning, Make binds the explicitly declared
`toolchain.editable_sources` with that environment's native pip before starting
the source-selection process. That declaration includes the Infra executor and
its required local suppliers; otherwise the frozen SDK would execute the local
selection. CI rejects this local input before any binding. Each named distribution
must already belong to the frozen environment. The existing FLEXT selector then
binds only the remaining distributions, validates the entire selection and publishes
its existing receipt. Already correct editable origins are observed through native
PEP 610 metadata, without another installation or a separate inventory.
The bounded Make-bootstrap operation receives the same publication collaborators
as generation; a missing publication capability is an error, never permission to
edit the generated Makefile directly.
Native scalar match captures use the SDK's `get_capture_region(name)` boundary.
Infra's `semantic_capture_region(module, match, name)` validates the returned
half-open offsets against that same module's source. It does not obtain an AST
node or reconstruct its region. An absent capture raises explicitly; the selected
SDK must supply this capability without an Infra parser or fallback.

The native-query cutover is not complete: snapshot import classification and
remaining source transformation consumers still require migration and runtime
proof. Reusing one project does not prove incremental refresh. Creation, movement,
removal and export changes must invalidate the affected native and derived facts
before readers resume. Source, built wheel, installed SDK and the original public
Make invocation require separate receipts. A source-derived MRO failure belongs
to the native SDK owner; its repair must preserve the installed capture and
source-binding query capabilities rather than replacing them with an older SDK.

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
Facade-member census, ownership and component metadata use that same injected
source project, including external-library classification. Their canonical APIs
accept native bindings, not arbitrary runtime objects. Published facade selection
is shared across the requested letters; qualified publishers remain qualified
(`infra.contracts` and `infra.pulumi.lib` are independent publication boundaries).
Source ancestry and declaration kinds retain the configured owner precedence;
direct protocol declarations are not confused with concrete protocol descendants.
Binding identity is proven by the same alias declaration or exact nominal binding,
never by equal expression text or generic origins with their arguments erased.
Unknown kinds and unsupported dynamic identity proofs fail explicitly. No metadata
producer imports the target to bootstrap its own migration, and no runtime API
compatibility branch or second classifier is retained.
Repository planning emits an exception's original traceback when capturing its
failed outcome. The final report retains that same cause; interruption before
the cohort finishes cannot hide the first failure behind a timeout.
Returned planning failures retain and emit the same original exception as raised
failures. Publication-identity diagnostics attach the already-observed route,
binding kind and expected/observed owner to that exception; they do not resolve
another candidate, manufacture a cause or replace the failing publication check.
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
The lazy-initializer orchestrator binds its existing planning, rendering, source-view
and snapshot owners directly. Its first-party namespace phase likewise binds the
consumed utilities directly and loads runtime detector and dependency services only
when their operations need them. Neither initializer planning nor source-view
namespace discovery composes the generated root utility facade that it may need to
repair. Publication remains with the same conformance publisher; these dependency
boundaries introduce no alternate generator or initializer writer.

The lazy-map freshness validator consumes that same planner in verification mode.
Its unchanged-source comparison must be paired with independent fresh-process
public consumption: resolve the declared export, its owning identity and the
consumed MRO capability. Account for legitimate eager metadata separately from
lazy bindings. A child package's exports never become an ancestor export cohort.
The generated initializer's bootstrap must be usable before its target package
is repaired; the Core specialization remains at
[ADR-014](../../../docs/architecture/adr/014-family-part-shape-rope-codemod-rules.md#core-lazy-bootstrap).
This acceptance contract is not evidence of an implemented or integrated repair.

Conformance binds source-planning capabilities through the existing Codegen domain
facade, never through the generated root utility aggregate or a mirrored `u` facade.
That domain composes the existing capability owners by MRO; public orchestrators do
not flatten their private helper methods into another implementation. Runtime-only
workspace, dependency and validation services remain lazily selected from their
existing package exports when their operations are exercised. These bindings retain
the same planner, source snapshot, admission guards and injected publisher.
Native project construction belongs with the existing source-project factories;
module queries inherit that capability through the runtime facade. Catalog
utility rules use the declared provider-rule owner directly, without a second
catalog reader.

Current state (2026-10-26): the one-project-per-repository contract is accepted in
ADR-028 Decision 17. Module-level identity reuse is partially implemented; nested class
qualnames, publication refresh, and the remaining consumers of source-base analysis are
still in the `flext-1engx.15` cutover. Generation retains a separate repository
snapshot through its lazy-provider and managed passes; nested inventory membership
does not enlarge that repository's native source election. Managed source views
without declared effects reuse that repository's engine and authenticated reads.
Scoped lazy planning indexes that repository's own inventory; the outer declared
repository loop owns the nested checkouts rather than indexing them again for
each ancestor's initializer plan.
Effectful candidate views still open a distinct overlay, so the complete target
remains unmet until provider invalidation updates the one bound project safely.
This status is not a performance or convergence receipt.

### Profiling a root verb

The generation start message includes the resolved profiling flag and destination
beside its native PID. These process settings are evidence of selection, not evidence
of a completed capture; the raw capture and readable report must still be verified.

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

The native profile owner prepares its configured output directory before starting
the operation or registering signal checkpoints. A planning rejection can occur
before generation creates any report artifacts; it must still leave the same
immutable profile and readable report. Directory preparation errors fail before
the profiled operation, not during finalization after its original failure.

The CLI composition injects the existing `CProfileReport` renderer into the
stdlib-only clock's finalization. It renders and emits a bounded summary from
that invocation's immutable capture, using the canonical tooling sort and row
limit, after native profile publication. The clock only transports the callback
and capture path; it does not import application models or configuration.
Report failures remain visible through the same finalization owner without
replacing the operation's first exception or nonzero status. A report failure
after an otherwise successful operation is an error. This applies when Python
finalization runs; it does not change signal actions or promise cleanup after
an uncatchable process termination.
For a nonzero `SystemExit`, the existing diagnostic emitter prints a secondary
report failure because Python does not display that exception's attached notes;
the original exception object and exit code remain unchanged.

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
Routine negative annotation-deferral predicates do not emit per-class debug
messages; phase summaries and original exceptions carry actionable feedback.
Singleton-model classification propagates the original native ancestry failure.
An incomplete hierarchy is not a no-op and cannot be deferred to a later
fixed-point pass as proof that no model transformation is needed.
Facade-member classification also preserves that failure; an unresolved class
cannot be reclassified as a function to continue library-owner discovery.
Import-boundary failures identify the consumer path, imported binding and
provider so a structural-repair request locates the actual source owner.
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
the same directory query for every member. The same facade-member owner builds
its declaration inventory once per class and passes it by reference to package
ownership checks, rather than rebuilding ancestry for each method. The inventory
belongs to that source view and is never retained across candidate transitions.
Owned-member reference election also
captures each facade's member names once per census, rather than enumerating
the facade again for every owner/member/receiver combination.
Protocol-member consumption resolves every receiver through Rope's lexical
scope and original imported identity. It does not infer a module-wide binding
from a FLEXT AST census: repeated imports, shadowing and nested scopes remain
the native resolver's responsibility. Removing that shortcut adds no alternate
index or cache and does not establish a performance improvement; the full
generator and its invocation-owned profile remain the validation boundary.
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
captured text. A single-file export query reuses its current native module when
the captured text already matches; otherwise it binds only that candidate through
the existing source-view owner. It does not discover or copy the repository's
complete source inventory for each queried provider.
Facade-owner derivation reads package exports through its existing captured-source
reader; a native package object is not passed to the source-module guard.
Callback admission uses Rope's native restructuring hook once;
the adapter counts observed/admitted matches there and leaves change computation
to the native implementation. It does not filter the same occurrence again in a
second change-computer override. Snapshot consumers use the shared source ports,
including their mutable-map value contracts, rather than concrete model classes.
Untyped SDK core and match results enter through strict native adapter admission;
the project subclass does not override SDK methods merely to replace their inferred
return annotations.
Own-method MRO promotion authenticates builtin decorators by native identity,
including imported aliases. The emitted classmethod decorator must retain the
builtin identity in its actual lexical scope; a shadowed same-spelled name does
not satisfy the publication contract.
The existing native import owner elects a deterministic capability-derived alias
only when the canonical member binding is shadowed in a participating lexical
scope. It checks native bindings for each candidate spelling, publishes the
elected alias through native import operations, and authenticates the rebound
candidate before publication. This is source-local collision avoidance, not a
registry, compatibility alias, or alternate import pipeline.
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

## Related Documentation

- [Make Commands Guide](../../../docs/guides/make-commands.md)
- [Codemod Rules Guide](../../../docs/guides/codemod-rules.md)
- [CSV Rename Campaigns](csv-campaigns.md)
- [Repository Configuration and Local Overrides](local-config-overrides.md)
- [Model-Class Boundary Migration](model-fields-migration.md)
- [Git State Capture](git-state-capture.md)
- [Plan Collection](plan-collection.md)
- [Recovery Runbook](recovery.md)
- [ADR Index](../../../docs/architecture/adr/README.md)
