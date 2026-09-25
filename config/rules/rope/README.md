# rope phase parameters (ADR-017)

Parameters and violation models for the rope phases of `make mod` (import-alignment,
accessor-renames, dataclass-modelizer, pydantic-presets, compat-alias, private-import,
future-annotations, class-nesting, deferred-models, contract-drift). Populated by cycles
C2 and C5 of the rope-modernize program (bead epic flext-exbwv); layer order stays in
`config/tooling.yaml` (`lazy-init.import-layer-order`).

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
