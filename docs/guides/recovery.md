# Recovery runbook

<!-- TOC START -->

- [Broken bootstrap (the checkout's Makefile misbehaves)](#broken-bootstrap-the-checkouts-makefile-misbehaves)
- [Install-mode mismatch](#install-mode-mismatch)
- [The recovery loop](#the-recovery-loop)
- [Orphan imports](#orphan-imports)
- [Racing-lane merges](#racing-lane-merges)
- [Render provenance](#render-provenance)

<!-- TOC END -->

How to diagnose and heal a checkout whose own tooling is the broken part.
Every cure here is owned state re-applied by a verb — never a hand patch
that the next generation cannot reproduce (aihub-l42it.11 consolidation
postmortem, 2026-10-13).

For `flext-0029c`, the [native-bootstrap task route](execution-context.md#native-bootstrap-task-route-flext-0029c)
overrides the general Make-first recovery sequence below: use the direct public
Infra CLI for subsystem diagnosis, runtime, refactoring and gates; integrate Make
last with `flext-itpd1.4.13`. The confirmed trust decision retires pre-install
Python setup admission and copied resources, not the post-install stdlib import
guard. Recover native declarations/locks at their existing owners, provision via
Mise/uv, then verify installed imports and provenance at the existing typed owners.
Never restore the retired installer, persist supplier selection, or translate it
to shell. Repeat bounded native QA after causal repair; change tests only after
real subsystem and cold-bootstrap proof. These are requirements, not receipts.

## Broken bootstrap (the checkout's Makefile misbehaves)

Symptom: `make setup` fails inside the emitted recipe (unbound shell
variables, references to template features the pinned motor never emits).

Use the internal `codegen init` adapter from a provisioned generation tool
runtime, selecting the affected repository with `--repository-root`. An existing
project receives the canonical Makefile and its declared bootstrap dependencies
through the existing guarded planner and publisher. Change the renderer or its
configuration when that projection is wrong, then publish through this owner.
The adapter adds no public Make verb.

Creation normally runs through the workspace's `make gen` after the new member
declares its own metadata and its Git checkout is prepared. A standalone target
without a Makefile uses the same initialization adapter. A prepared tree with its
own complete project, integration, kind and source provenance receives the declared
generated layer, including Python automation files. This also applies to an
established non-Python repository that never tracked `pyproject.toml`; having a
commit does not prohibit generation. Missing metadata alone never declares that
intent. The Detector owns admission for ordinary generation and initialization,
including the checks for removed tracked metadata and existing authored Python
sources. Enabled Beads participation requires the destination's own declared identity.
Generation materializes files; installation and runtime bootstrap belong to `setup`.

For that standalone cold entry, run `codegen init`, `make upg`, `make setup`,
then `make gen`. The provisioned generation tool runtime owns its native Mise,
Python and UV prerequisites. Setup installs the resolved destination dependencies
into that destination's physical environment. Initialization and generation do
not install dependencies, resolve locks, initialize Git or create commits.
The approved native target consumes shipped declarations and locks: official Mise
acquisition, native locked tool provisioning, then `uv sync --locked`. A cold
checkout must not require Python generation of a copied bootstrap resource or
synthetic resolver. Missing inputs belong to explicit generation/upgrade, not an
AWK/shell parser or automatic lifecycle operation inside setup. This target still
requires real cold and repeated setup proof; it is not a recovery acceptance claim.

## Install-mode mismatch

`verify-environment` rejects a checkout synced in the other mode (CI's
locked noneditable build vs the local editable binding). Root CI checks out
declared submodules and uses the same native workspace and lock as local execution;
independent checkouts retain their own native contracts. Operation prerequisites
require the selected physical interpreter; they do not install or retry setup.
Run setup explicitly to consume the declared locked inputs and verify the
result. Under the confirmed native flow, physical ownership and symlink refusal
remain prerequisites, but an authored Python pre-install admission is not restored.
Installed FLEXT provenance verification follows native installation and fails at
its existing owner; it does not retroactively authenticate that installation.

## The recovery loop

Run generation and structural modification as separate operations, preserving
their original failures and publication receipts. Repeat `make gen` after its
inputs change or to prove convergence on unchanged inputs. A failed or interrupted
run does not count as convergence and is not retried without repairing its cause.

In a workspace, ordinary generation covers its declared eligible projects;
`CI=Y` restricts generation to the selected project. Runtime isolation is a
separate contract. Shared WIP is an admitted input: Git dirtiness neither
invalidates a receipt by itself nor authorizes discarding work to obtain a clean
tree. Physical source, declaration, topology and destination checks still apply.

The transaction owner holds the journal lease during recovery and publication.
Temporary retirement authenticates the current exact Git control directory,
caller-authorized participant roots, journal version and transaction, original
path closure, manifests and registered staging intentions. Historical device,
inode and mount numbers are observations of the originating execution; their
equality across mounts is not durable ownership. The original records remain
unchanged, including their internal parent bindings. Retirement authorizes the
recorded logical tree in the currently authorized scope; it does not establish
physical continuity across indistinguishable clones or snapshots.

The durable manifest comparison preserves entry paths and kinds, permissions,
owner/group and host attributes. Manifested files also retain their size, digest,
link count and modification/change timestamps. Incomplete intentions retain only
the fields actually recorded, their available original parent bindings and the
same current transaction-path closure. Unregistered residents, aliases and changed
recorded file metadata remain refusals. After that authorization, the existing cleanup
primitive receives the complete newly observed manifest and applies its exact
device, inode, mount, descriptor and journal CAS checks. Registration, active
publication, source validation and selected dependent-group compensation retain
their physical identity contracts, including the physical topology verifier used
by active journal preparation and committed-destination checks. The retirement
entry point composes its durable authorization with the same directory/entry
binding engine. An incompatible journal remains a blocking
input, not permission to rewrite its version or widen its authority.

The operator's 2026-10-24 authorization permits punctual retirement of the
prepared v8 journal `ad1c00b704d18eb06a7012e4508eaadb` in `~/cosmos-docgen`,
whose recorded destination-entry inventory is empty. The last known v8 tree,
`ceb2b84d5985f6748e493b7d59304ef1f0742586`, supplies the original protocol
owner; it is not established as the journal's exact producer. Apply the reviewed
durable-retirement correction to those same source owners in its existing
isolated maintenance worktree, then rebuild its own wheel through native
UV with its committed lock, without editable installation, development groups,
borrowed environments or source overlays. This is authorized protocol
maintenance, not an alternative setup or generation path for Docgen. The
one-shot public API holds `FlextInfraCodegenFileLeases.mutation_lease`, reads
the original journal through `FlextInfraMiseArtifactsJournal.read`, and pins
its exact path, transaction ID, prepared state, sole root selector and empty
destination inventory before calling `FlextInfraMiseRecovery.execute` under
that same lease. The corrected v8 owner must authenticate the current scope and
the original staging authority before passing the fresh manifest to exact native
cleanup and retaining its guarded journal CAS.
Any original failure leaves recovery incomplete. Do not run historical general
generation or setup, change the journal version, widen its manifest, copy its
decoder into the current engine, patch an installed package, or remove state
directly. This maintenance adds no legacy protocol support to the current engine.

## Orphan imports

The `deps` gate (deptry) fails any import the declared dependencies do not
cover, at check time. Cure the declaration (the project's dependency SSOT or
the org override surface), never the consumer's import.

## Racing-lane merges

Before an administrative merge of diverged lanes: realign the branch
(`git merge --no-ff` the declared integration base), then run the repository's
applicable canonical `mod`, `fix`, `fmt`, `check` and `tests` operations on the
realigned sources. Repair a broken Make projection through the documented
bootstrap owner first. Textual mergeability is not semantic integrity.

## Render provenance

Generated artifacts carry `# @flext-rendered-by: flext-infra <version>`.
A drift between this stamp and the consumed motor is a regeneration order:
`make gen` re-renders with the declared generator. `make check` validates
projections and their provenance without regenerating them; retain the actual
diagnostic and receipt rather than treating the stamp alone as proof.
