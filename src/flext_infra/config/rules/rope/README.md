# rope phase parameters (ADR-017)

Parameters and violation models for the rope phases of `make mod` (import-alignment,
accessor-renames, dataclass-modelizer, pydantic-presets, compat-alias, private-import,
future-annotations, class-nesting, deferred-models, contract-drift). Layer order stays
in `config/tooling.yaml` (`lazy-init.import-layer-order`).

`flatten-family-namespace-wrapper.yaml` declares the single-wrapper family rule. The
existing class-nesting phase consumes its typed operation and collision policy; it does
not create another mod loop or publication path. Planning uses a closed, read-only Rope
snapshot so proposed imports and inherited consumers share identities. Real entity
classes remain nested. A wrapper used as a value, an unresolved member, unresolved owner
inheritance, or a second prefix collision fails the complete plan. Receipts report the
exact wrapper and source-edit counts. Publication remains owned by the semantic
transaction, and generated facades remain owned by `make gen`.

The same class-nesting phase promotes shared behavior from private test fixtures to the
unique declared utilities facade of its tier. Rope resolves the original class and its
external consumers before planning a move; classes with pytest cases and unused helpers
keep their owners. The planner preserves declaration names, rejects ambiguous facades or
occupied destinations, and stages only content changes in the governed source inventory.
Existing nesting and publication complete the cutover; `make gen` updates the package
exports. When an existing export needs regeneration, run `make gen` before `make mod` so
the move observes the current public binding.

Quoted annotations are resolved before relocation loses the original binding, including
aliases imported through generated reexports. Rope elects the destination import; the
nesting step keeps `get_type_hints` bound to the moved class. Consumers used only in
type positions participate in the same plan. Ordinary literals, `Literal` values,
`Annotated` metadata, and unrelated homonyms retain their values.

The contract-normalization phase consumes its `phase` rows in `contracts.yaml`
through the canonical semantic-phase enum; constant-consumers consumes its own
rows through the same typed catalog and native planner. Unknown phases fail
configuration validation. Python matches and replacements use native Rope
`SimilarFinder`, identity-constrained `Restructure` patterns and ChangeSets.
The phase shares the existing semantic fixed point and publication transaction;
it has no independent repair loop or CST, AST or regular-expression parser.

Constant consumers reuse declarations already exposed by the package's public
`c` facade. Complete function returns can use a uniquely assigned string or
nonnegative decimal integer constant with the same native scalar type. Enum
members are excluded from that rewrite because returning an enum changes the
observable type. String spelling is taken from Rope's native literal regions,
including raw, Unicode, escaped and triple-quoted forms; formatted strings do
not establish a static value.

Singleton `Literal` field annotations can reuse an existing public `StrEnum`
member with the same value. This rewrite preserves defaults, aliases,
discriminator metadata and the field's accepted JSON values. Function
annotations and multi-value `Literal` declarations are outside this operation.
Singleton static builtin `frozenset` declarations can replace the right-hand
collection of an `in` or `not in` predicate. Construction and return expressions
retain their original object identity. Shadowed constructors, mutable values,
reassigned declarations, conflicting constant owners and competing `c` bindings
cannot authorize a rewrite. These operations do not create new constants or
enum declarations.

Pydantic field rewrites require ancestry established from the native Rope
object graph. Same-spelled factories and declarations outside those model
scopes retain their behavior. Empty factories migrate only when the declared
concrete collection and the existing factory share their native identity.
Destination imports use Rope's import manager and reject competing lexical
bindings before publication. Configured defaults and factories remain policy
data; projects do not carry copied detectors or symbol mapping tables.

Native restructuring carries imports once: a sequence introduces declarations;
a binding-keyed mapping also reuses existing compatible facade imports. The same
operation contract serves configured rules, symbol migrations and path cutovers.
Runtime equivalence, read-only planning and a second-pass no-op share one
`u.Tests` proof consumed through the real Rope fixture; scenario data retains
distinct validation, factory and binding failures.

A wildcard argument may declare several native identity constraints. The
shared Rope wildcard delegates each alternative to the SDK's exact identity
matcher during the same resource pass. Canonical `Field` publications are
declared once and reused by the field rules; an unrelated same-spelled callable
does not become a Pydantic factory.

When a replacement repeats or reorders annotation evaluation, the rule declares that
effect. The existing Rope word finder supplies call coordinates for the matched
region; authored calls prevent automatic duplication or reordering of their effects.
This proof is separate from collection mutability and destination import
availability.

Moving a sole `Field` metadata item out of `Annotated` retains the callable,
field position and arguments. A factory that receives previously validated field
data must keep that signature and its evaluation order; it is not an empty
collection factory. Additional constraints, aliases, validators and serializers
are not discarded to make a pattern match.

Python and JSON validation are separate Pydantic contracts. The former automatic
`fix-json-loads-paired-validate` rewrite is retired. The remaining boundary finding
requires proof of accepted and rejected inputs, validator modes and context, custom
decoder behavior, and parse failures before changing the call. Strict date and
tuple fields alone can distinguish `model_validate` from `model_validate_json`;
the presence of a same-spelled method cannot establish equivalence.

Declaration context uses the captured occurrence and the admission pass's shared
Rope snapshot. Equal short names in different class namespaces are resolved
independently. Model recognition follows BaseModel ancestry, including inherited
fields; settings and behavioral classes remain outside payload relocation.
Native validators, serializers and computed fields preserve their identities.
Generic ancestry contributes its declaration owner only when its subscription
binding is the native Pydantic or Protocol contract; custom subscription behavior
does not establish equivalent ancestry. Protocol admission requires an explicit
direct Protocol base, preserving concrete implementations of existing protocols.
Both `typing.Protocol` and `typing_extensions.Protocol` are resolved through their
native bindings, including aliased and specialized bases. Recognized declaration
decorators must be the decorator expression's actual callable: a native serializer
nested inside an unknown wrapper, or a locally shadowed decorator name, does not
admit relocation.

Typing unification resolves names in concrete-syntax type positions through lexical
bindings. `Any`, `typing.Any`, and `object` do not establish JSON or attribute-probe
contracts; they remain visible to enforcement until their consumer defines the precise
type. Datetime and filesystem paths are not converted to JSON aliases. Imported facade
rewrites preserve ordinary strings, documentation, `Literal` values, and `Annotated`
metadata values, including quoted annotations and aliased typing imports. A referenced
callable may acquire its proven facade path without changing the metadata it produces.
Destination imports keep their declaration scope, and a competing or unproven facade
binding rejects the complete rewrite before publication. Structural type roots are
shared with family relocation, including quoted generic bases. Deferred strings inside
typing factory/cast calls that cannot be migrated by that selected path reject the
complete import rewrite; they never survive as orphaned references after their binding
is removed. Imports from another branch or a `TYPE_CHECKING` suite do not establish
runtime availability: each migrated declaration retains its original execution condition
unless a preceding import in the same suite proves availability.

Introducing a local facade import also requires that it cannot capture existing reads of
an ancestral binding, including reads in closures. Otherwise the source transaction is
rejected. Typing unification explicitly requires runtime availability, including for
`get_type_hints`, PEP 695 aliases, and Pydantic fields. Deferred, conditional, or late
imports do not prove it. A new import of the source file's owning package is also
rejected without an existing runtime binding, preserving package initialization order.
Consumers that explicitly require only type-checking bindings retain that behavior.
