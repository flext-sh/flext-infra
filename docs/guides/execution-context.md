# Execution context

<!-- TOC START -->

- [Runtime is the authority](#runtime-is-the-authority)
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
- [Codemod scanner contract](#codemod-scanner-contract)

<!-- TOC END -->

## Runtime is the authority

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

## Environment activation

The `make setup` contract includes approving the `.envrc` with `direnv allow`.
Operational Make verbs activate that environment before handlers and hooks, except the
activation producer declared in `make.verbs`. For `gen`, the pin and the provisioned
physical environment are required before `pre-gen` and the selected handler. The default
handler runs one conform transaction, which includes generating the `.envrc`; a declared
`_custom-gen` still replaces that handler. Only then does Make activate the generated
environment and run `post-gen`. A producer or activation failure prevents the later hook
and keeps the command red, so `make gen` can repair a broken generated activation
without another writer outside the journal. Initial provisioning remains the
responsibility of `make setup`. Real commands work without wrapping each call in
`direnv exec`.

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
`make upg`. A missing pin requires `make upg`; a runtime that is not yet installed
requires `make setup`, whose provisioning happens before activation.
Both setup and upgrade resolve the executable through `mise which python` at the
shared environment-sync boundary and pass that exact path to uv. Recursive Make
calls do not require a caller-provided `SETUP_PYTHON` environment variable.
Make and direnv restrict global and system configuration discovery to the
elected runtime's `.mise` directory; unrelated host tool declarations never
belong to project provisioning.

If `mise.lock` has no self-managed Mise entry, `make setup` fails without
changing it. `make upg` uses the installed host Mise to resolve the declared
manifest first, then provisions the newly recorded release from its verified
asset and continues the normal lifecycle. The generated `.mise.toml` must match
the current toolchain owner before that recovery; `mise-config` conformance
repairs this single declaration without regenerating unrelated project files.

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

Configuration declares `latest`. `make upg` is the only verb that resolves newer
releases and writes the committed `uv.lock` and `mise.lock`. `make setup` installs
from committed locks; `make gen` and `make fmt` neither install nor upgrade tools.
Git dependencies follow their declared integration branches, and `APPLY` stays removed.

One `make upg` run converges. It resolves the Mise lock before provisioning,
upgrades `uv.lock`, installs the upgraded generator and conforms dependency floors.
It runs generation's producer half, relocks the projected manifests, reinstalls
and verifies the resulting runtime before generation's activation half. A
requirement or Mise self-management release that only the upgraded generator
declares therefore reaches the lock and environment in the same run. The declared
lock platforms and release cooldown come from the typed toolchain; never edit
native lock payloads or substitute manual installation commands.

`codegen.scaffold.project.retired_dev` declares development distributions that
must no longer reach managed `dev` or `codegen` groups. Conformance filters them
from existing groups, optional development extras, and member contributions;
declaring the same distribution as a required development floor fails. Retire
obsolete typing stubs here when their runtime SDK supplies inline typing, then
regenerate and run `make upg` to reconcile locks and the installed environment.
Do not uninstall packages manually or weaken the type checker.

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
Setup and audit verify the environment's installed PEP 610 and RECORD-owned editable
paths against that same topology; a frozen Git artifact is not a live local source.

Operational Make prerequisites also verify that provenance before dispatch. An
executable interpreter alone does not establish a valid development runtime.
Run runtime actions through the root Make dispatcher. Its recipes use the
setup-owned interpreter without selecting a member's lock for synchronization. Only
setup and upgrade provision dependencies. A provenance failure is repaired through setup,
not through a `--no-sync` override or a source-path injection.

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

## Mise toolchain

Mise manages itself: the generated `.mise.toml` declares the `toolchain.mise_selector`
release as a `[tools]` entry, and `mise.lock` pins it like every other tool. One host
Mise capable of reading the committed lock provisions that entry; setup verifies
the installed release and enters the recursive Make lifecycle through it. Every
later `mise` resolved through the shims is the pinned release, and `make audit`
(`codegen mise-proof`) fails when the running Mise differs from the lock.

`make upg` publishes the Makefile through the producer half of `gen`. When that
publication changes the Makefile, the running recipe stops naming its own
targets and hands off to a fresh `make upg` on the published file; a second
change inside the hand-off fails loud as a `gen` fixed-point defect. A
Makefile committed by an earlier generator still runs its own recipe once, so
generate it with the current generator (`make gen`) before its first `make upg`.
Separate `mise.version`, bootstrap launchers and staged lock-convergence scripts
are not lifecycle owners.

`toolchain.tools` in `config/codegen.yaml` declares every fleet tool. Each comes from a
native, checksum-locked owner (aqua, GitHub releases, conda, or a Mise core backend);
the toolchain model rejects an `npm:` selector at load (ADR-025). A tool whose upstream
release metadata publishes no checksum declares `lock_checksum: false`.

`make setup` and `make upg` pass the explicit declared key list
(`toolchain.mise_install_keys`) to `mise install`. A bare `mise install` would also
provision every tool of the operator's global Mise registry, so no generated recipe
runs one. After the environment is provisioned, `make setup` runs the reality proof
(`flext-infra codegen mise-proof`) before `post-setup`. For each declared tool, in
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
`make setup` never writes either. A missing or incompatible Mise lock entry fails
with its original diagnostic and exit status, without disabling lockfiles or
retrying. Setup checks whether `uv.lock` agrees with the manifests. A matching lock uses
`--locked`; a drifted lock emits its diagnostic and installs the committed lock
with `--frozen`, without rewriting it. Drift and any resulting dependency
incompatibility remain red until `make upg` produces matching locks. A missing
lock fails with an actionable diagnostic. A failed native resolver or installer
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

## Codemod scanner contract

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

The root facade export rule preserves literal tuple values and order while removing
an unnecessary type-only annotation dependency. It does not change classes, aliases
or inheritance, and it does not rewrite initializer projections.

`GateExecution.issues` retains each finding's original file, position, rule, message,
and severity. SARIF reports each finding at its native level; raw scanner output remains
available on the execution. A passing gate therefore proves both the scanner contract
and zero rule findings.

The same repair validates projected Ruff first-party namespaces strictly: a malformed
value cannot be replaced with discovered namespaces. A declared empty list remains
empty; namespace discovery applies only when the list is absent. A bare Python
annotation does not replace an existing facade binding. Mypy's module-specific
`follow_untyped_imports` policy analyzes Rope's installed source without suppressing
`import-untyped`; the typed tooling policy owns both template and dependency-modernizer
projections. See the
[Mypy option contract](https://mypy.readthedocs.io/en/stable/config_file.html#follow-untyped-imports).
