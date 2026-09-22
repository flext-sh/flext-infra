# Generated merge policy

`make gen` derives `.gitattributes` from the publication plan. Fully managed
artifacts and lazy initializer outputs receive `-merge linguist-generated`.
Mixed authored/generated files retain ordinary text merging. The attributes
file itself remains text-mergeable so it cannot block its own policy update.

When generated files conflict, first resolve the source and configuration
conflicts, then run `make gen`. Review and stage the regenerated result before
committing. Never resolve generated conflicts by choosing an entire branch's
version. `make audit` rejects stale generated attributes as generation drift.

Generation publishes attributes in the same transaction as the managed outputs
and checks their fixed point before committing the transaction. Repeated
generation must preserve the same bytes. Git runtime configuration and hook
activation belong to AI Hub; generation does not install hooks or merge drivers.

Repository checkpoints reuse the current commit when the staged tree is
unchanged. A merge commit that records two parents is a separate Git operation
and is not suppressed by this content-checkpoint rule.
