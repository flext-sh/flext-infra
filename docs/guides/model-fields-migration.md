# Model-class boundary migration

<!-- TOC START -->

- [Model-Field Access Migration (`model_fields`)](#model-field-access-migration-model_fields)
- [Codemod Gate and Mechanical `refactor ast` Boundaries](#codemod-gate-and-mechanical-refactor-ast-boundaries)
- [Declaration-Layer Import Law and Environment Reads](#declaration-layer-import-law-and-environment-reads)
- [Compatibility-Alias Cutovers (`plan_semantic_cutover`)](#compatibility-alias-cutovers-plan_semantic_cutover)
- [Upgrade Interruption, Rule Snapshots, and Proof Presets](#upgrade-interruption-rule-snapshots-and-proof-presets)

<!-- TOC END -->

## Model-Field Access Migration (`model_fields`)

`make mod` owns model-field access migration. The ast-grep rule reports dynamic
`model_fields` lookup; its semantic phase narrows an untrusted class argument using the
public `flext-core` model-class guard before accessing required fields.

A boundary that already rejects a missing or empty field mapping retains its original
rejecting branch. Non-model classes, model instances, and arbitrary objects reach that
branch without evaluating their `model_fields` attribute. Populated Pydantic model
classes continue through the boundary. Empty models remain invalid where the existing
boundary already required fields.

The migration discovers argument and local identities from the function source; there is
no project, filename, or function-name catalog. It also recognizes direct access emitted
by earlier versions of the textual rule. Ambiguous error branches, additional uses of
the temporary mapping, and conflicting guard bindings fail without publishing a partial
rewrite. Other dynamic lookups remain findings until their receiver contract is proven;
they are never blindly rewritten.

## Codemod Gate and Mechanical `refactor ast` Boundaries

The codemod check gate blocks on every reported policy finding, whatever its rule
severity, and reports each finding with its native severity. Failed rule discovery,
incomplete scans, invalid diagnostics, and other native scanner failures also block,
with their own failure diagnostics.

The standalone `refactor ast` mechanical circuit remains full-corpus only.
Its request declares no module or namespace selector, so the native CLI rejects
those options before execution. Project filters fail before rule planning or
scanning until both mechanical inventories, publication preconditions, and
expected-count receipts share an exact resolved target scope.
Non-text `--output-format` requests also fail
before scanning rather than returning a text report mislabeled as JSON. This is a
safety boundary, not implemented bounded selection or structured reporting.
`--dry-run` and `--check` take precedence over `--apply`: they report findings without
applying either cascade. Scan evidence publication remains part of the scan contract;
read-only source mode does not mean an artifact-free invocation.

The namespace enforcement request consumes `--module`. Accessor migration
consumes `--module` and `--namespace`. These requests compose the shared narrow
selection mixins explicitly; general read/write scope does not add either
option to other commands.

## Declaration-Layer Import Law and Environment Reads

Authored declaration layers cannot import their own namespace at any scope, including
function bodies and annotation-only guards. The shared import-law owner identifies
these declarations from the family catalog. Declaration relocation resolves imports
to identity-proven external public exports through Rope; dependencies without a lawful
owner remain typed findings. Generated facades alone compose local declarations through
lazy packages. Moving an import into a method does not repair its ownership.

Dynamic environment reads require a resolved OS import and a config-owned key, either
directly or through an unambiguous same-function alias. The destination settings source
must declare both optional and required lookups. Optional reads retain `None` for
absence and preserve empty strings; required reads retain the native `KeyError`. Static
keys, rebinding and competing settings owners remain errors. Consumers are rewritten
only by `make mod`.

## Compatibility-Alias Cutovers (`plan_semantic_cutover`)

> Deprecated mechanism (ADR-028 Decision 17 amendment 2026-10-28): the LibCST
> qualified-import analysis below is being exterminated — rope is the only
> accepted Python interpreter in FLEXT's own code, and these cutovers migrate
> to rope transforms over the single indexed project. The behavioral contract
> (consumers, bindings, root-binding agreement) is preserved by the replacement.

Compatibility-alias cutovers resolve module attribute reads through LibCST qualified
import identities, not receiver spelling. Module aliases and dotted imports retain
their import location, including function-local imports. Parameters, comprehension
bindings, local rebindings and unrelated imported homonyms are not alias consumers.
Dotted expressions must also agree with their lexical root binding: a local or
unrelated root cannot inherit an outer module import's full qualified name. Both
rewriting and final residue validation apply this proof; mixed or unknown import-root
identities refuse the complete plan rather than bypassing consumer closure.
Ordinary strings, `Literal` payloads, `Annotated` metadata and inert reflection-name
literals remain unchanged. Identity-proven builtin `getattr`, `hasattr`, `setattr` and
`delattr` calls on a retiring module reject the complete plan when their attribute names
select a retiring alias or are dynamic. The planner never rewrites reflection strings
to hide a consumer. Known non-retiring attributes, unrelated receivers and shadowed
getter homonyms are not classified by spelling. Unproven consumer bindings reject
the complete plan before the transaction publishes any source; existing residue
validation remains the final post-rewrite boundary.
Names and attributes share the same all-bindings proof: a retiring identity mixed
with an unrelated import or local binding rejects the complete plan immediately.
Multiple recognized imports may converge only when every identity names the same
destination; exact module-local owner alias reads remain supported. Direct alias
imports with any `as` binding remain unsupported and reject the plan.
Imported retiring modules may be used as direct attribute receivers or as the first
argument of a proven builtin reflection call with a known non-retiring attribute.
Assignment, return, container storage and passage to opaque callables reject the plan
as module escapes. A shadowed getter is not classified as builtin reflection, but
passing a retiring module to it still constitutes an opaque escape. This boundary
does not infer interprocedural behavior, arbitrary reflection or dynamic imports;
acceptance is limited to qualified identities in the supplied source inventory.
The public `u.Infra.plan_semantic_cutover` contract verifies these boundaries and a
second unchanged plan produces no edits. This safety repair does not move declarations
or remove fleet helpers.

## Upgrade Interruption, Rule Snapshots, and Proof Presets

The upgrade interruption regression owns its child session through the CLI process
facade. Native procps selects that session's threads and proves the resolver is blocked
on the fixture FIFO before interruption. It never scans unrelated process directories or
discards a disappearing-process error. The test then verifies the original lock and
staging cleanup against the real upgrade implementation.

Rule snapshot changes are projected with `make mod-snapshots`. Run `make mod`,
`make gen`, and the native validation lifecycle after updating the automation
dependency. Do not repair the consumer by editing the rewritten call site.

Census consumers pass the canonical `m.Infra.CensusInput` to `infra.census`.
That composition owns the Rope workspace, authenticated source preview and
request defaults for both CLI callers and behavioral test fixtures.

Mise reality proofs carry their validated inputs in
`m.Infra.MiseToolchainProofOptions`, using the shared frozen preset. These inputs
contain declared models, JSON, paths and collections; they require no arbitrary
type allowance.

Transaction plans and journals use the existing exact-text frozen contract
preset instead of combining independent Pydantic presets. Staged source strings
retain their whitespace and enum identities. Toolchain proof scenarios execute
the managed native UV binary; version and platform expectations come from its
declared probe and current lock.
