# Durable Git state capture

<!-- TOC START -->

- [Git primitives and lane publication](#git-primitives-and-lane-publication)
- [Recovery Branches](#recovery-branches)

<!-- TOC END -->

`u.Infra` owns scoped WIP capture. Callers select literal repository-relative paths in
`m.Infra.GitWorktreeStateRequest`; directories include their tracked and nonignored
untracked descendants. An empty path tuple captures nothing. Nested repositories retain
independent capture ownership.

`git_is_inside_work_tree` asks native `rev-parse --is-inside-work-tree` at the
requested directory. Discovering its repository does not make Git control storage
or a staged preview beneath that storage part of the working tree.

`git_snapshot_worktree_state` measures the original HEAD, index entries, raw working
bytes, symlink text and permissions without modifying the source index. Unmerged,
intent-to-add, assume-unchanged and skip-worktree entries fail explicitly.
`git_verify_worktree_state` returns `ok(False)` for different layers in the same
repository at the same HEAD; identity mismatches and read failures return failures.

`git_checkpoint_worktree_state` retains separate index and working trees in a dedicated
Git reference. The working commit has the original HEAD and the index checkpoint as
parents and records the typed snapshot. Requested retained commits also become parents:
callers use the child repository's checkpoint to retain original parent gitlink HEAD,
index and working OIDs in that child's object database. Parent tree pointers alone do
not retain child objects. Repeating a request verifies the existing checkpoint; a
divergent reference is never overwritten. Temporary indexes live alongside the
repository's shared Git storage, never in a borrowed environment or the source index.

`git_apply_worktree_checkpoint` copies only those durable bytes into a sibling worktree.
Preflight permits the original baseline or the already-applied captured state for each
owned entry, enabling an interrupted operation to resume without overwriting unrelated
work. Gitlink OIDs are retained in trees and indexes; submodule directories are not
copied or reset. Their repositories must retain their own checkpoints and reconcile
their working HEAD independently. Clean destination regular files are recognized by Git
content and executable mode; their other permission bits need not match the source.
Applying the checkpoint restores the captured permission bits. Cleanup preserves
captured non-executable permission bits on surviving regular files while restoring
HEAD's executable mode. Git cannot recover historical permission bits it never stored.

After saving an evolved candidate, `git_verify_worktree_checkpoint_commit` checks the
original checkpoint independently and verifies the destination's current saved
descendant and clean owned scope. Candidate content may intentionally have changed after
capture. `git_publish_worktree_checkpoint` publishes the original reference with an
ordinary atomic push and checks its exact remote advertisement. It returns
`GitWorktreeCheckpointPublication`, binding the remote name, endpoint, reference and
object ID. Credential-bearing endpoints are rejected before they can enter a receipt.
Push retains Git's ordinary fast-forward concurrency rules; it never forces a reference
update. Publishing a branch alone does not preserve this reference remotely.

Only then may `git_cleanup_worktree_state` restore the owned source paths. Its required
`publication` argument is verified against the live endpoint and remote reference before
effects; configuration drift or a missing reference fails closed.
`git_verify_worktree_checkpoint_publication` provides the same live proof before
retiring a lane. Cleanup rejects changed source entries or unresolved nested worktrees
before effects and accepts already-completed cleanup entries on resumption. Staged
additions are removed from the source index without attempting to restore a nonexistent
HEAD path. Checkpoint references remain reachable after cleanup and lane retirement, so
staged-only content survives Git garbage collection.

Transitions acquire the canonical Git-root codegen journal lease and use guarded
physical file and symlink operations with per-entry content and identity checks.
Cooperative writers must use that same lease. This is not an atomic filesystem
transaction against arbitrary external writers; detected drift fails while the durable
checkpoint remains available for recovery.

The unscoped `git_copy_worktree_state` remains a copy primitive for existing generation
transactions: it preflights a pristine sibling at the same HEAD and applies separate
worktree and index patches. WIP uses durable scoped checkpoints to avoid capturing live
files that appeared after its ownership snapshot.

## Git primitives and lane publication

Branch, worktree, reference and remote-branch operations run the native Git
operation and fail as Git fails. None inspects stash state, lane ownership or the
integration tip. Each keeps the rule its own operation needs:

- `git_push_upstream` is a plain, never-forced push: a diverged remote branch
  rejects it.
- `git_commit` uses native Git with the elected index and the worktree's
  effective hooks. It returns the object ID reported by that invocation
  after verifying the elected HEAD and parent (`flext-drts0.6`).
- `git_create_branch` refuses a branch that already exists.
- `git_delete_ref` is a compare-and-swap on the expected object ID.
- `git_delete_remote_branch` requires the observed object ID and deletes on that
  lease only.
- `git_remove_clean_worktree` refuses an unregistered, locked or dirty worktree and
  a dirty nested submodule; it never forces removal or prunes other registrations.

Automated lane publication (`u.Infra.git_publish_lane`, used by `make
release-version` and `make propagate`) owns one deterministic protocol branch
(`release/next`, the propagation lane). It starts only from a clean checkout on the
declared integration branch and continues that branch when it already exists
locally or on the remote.

Continuing the lane merges the base in with `git merge --no-ff`. A full generated
projection is declared `-merge linguist-generated` in `.gitattributes`, so Git
never combines two renderings of it and the lane's earlier rendering always
conflicts with the base's (Git reports "Cannot merge binary files"). When every
conflicted path carries both attributes, the merge concludes with the base's
rendering and the producing step regenerates it from the merged sources; any other
conflict keeps the merge state and fails with the original error.

The lane then refreshes its pull request, resolved by head, base and `open` state.
A merged or closed pull request on the same head, such as the previous release, is
history and is never edited: with none open, the lane opens a new one. Several open
pull requests on one lane fail loud.

## Recovery Branches

`git_create_checkpoint_branch(checkpoint, publication, branch)` creates a history
alias of an actual checkpoint only after revalidating its live independent remote
retention and original scoped index/working bytes. It never switches HEAD, creates
a worktree, accepts a caller-selected start, or carries uncaptured WIP. Creation is
CAS-protected against an existing branch and uses the same writer lease as capture.

`git_publish_checkpoint_branch` publishes only that exact captured commit without
force and verifies its live advertisement. `git_delete_checkpoint_branch` removes
only the remote alias on the exact retained-object lease, while rechecking that the
independent checkpoint remains published. Alias cleanup is not checkpoint retirement
or managed lane integration approval. The original source tree and index remain
unchanged; checkpoint scope remains explicit, not an assertion of global ownership.
