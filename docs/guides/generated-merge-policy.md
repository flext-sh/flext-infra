# Generated merge policy

`make gen` derives `.gitattributes` from the publication plan. Fully managed artifacts
and lazy initializer outputs receive `-merge linguist-generated`. Mixed
authored/generated files retain ordinary text merging. The attributes file itself
remains text-mergeable so it cannot block its own policy update.

When generated files conflict, first resolve the source and configuration conflicts,
then run `make gen`. Review and stage the regenerated result before committing. Never
resolve generated conflicts by choosing an entire branch's version. `make audit` rejects
stale generated attributes as generation drift.

Generation publishes attributes in the same transaction as the managed outputs and
checks their fixed point before committing the transaction. Repeated generation must
preserve the same bytes. Missing destination parents are journaled before creation.
Recovery authenticates temporary parents and generated files before restoring anything;
foreign content is preserved and reported as an error. Empty temporary directories are
removed, while existing coordination locks and generation receipts remain owned by their
runtime. Git runtime configuration and hook activation belong to AI Hub; generation does
not install hooks or merge drivers. AI Hub activates the generated validation script in
the native `pre-commit`, `pre-merge-commit`, and `pre-push` hooks, preserving existing
shell hook content.

Commit validation rejects unstaged or untracked changes before invoking pre-commit. The
generated candidate hook runs `make gen`, `make fix`, `make fmt`, and `make check` in
order. Repairs remain in the working tree and reject the commit until explicitly
reviewed and staged. Neither the wrapper nor its hook stages repairs automatically. Push
validation requires a clean candidate and runs the declared audit, check, and test
steps. CI enforces generation, repair, formatting, both check contexts, and tests on
integration pull requests and pushes; generated or repaired drift fails CI.

The canonical test runner resolves its testmon selection in one collection process
before starting parallel workers. That pass registers new test IDs as unexecuted
placeholders, so worker startup sees a consistent inventory after tests are added or
renamed. Only the subsequent execution records test outcomes and coverage dependencies.

Repository checkpoints reuse the current commit when the staged tree is unchanged. A
merge commit that records two parents is a separate Git operation and is not suppressed
by this content-checkpoint rule.

New projects declare their dependency provenance with `codegen new --flext-source`: the
value is a direct Git requirement for the configured infrastructure distribution,
including its HTTPS URL and ref. The scaffold's `project.flext_source` is validated
before filesystem effects and supplies the first generated dependency declarations.
Subsequent generation reads the existing checkout's declared Git sources. The
repository's own integration branch comes from its typed workspace declaration.
Attached-member discovery uses the same configured branch preference as root discovery,
including when the member is loaded directly.

To validate an unpublished dependency from a dedicated checkout, use
`flext-infra workspace flext-binding` with the consumer root, source checkout, and
consumer interpreter. The binding includes the source repository's own package as well
as its declared members, intersects them with the consumer's runtime, optional, and
development dependencies, and changes only that interpreter's environment. Committed
dependency declarations remain the publication contract.
