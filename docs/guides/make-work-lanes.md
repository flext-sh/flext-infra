# Make Work Lanes

`make work WHAT=start` derives a GitFlow kind from the Beads issue type when `KIND` is omitted. Epics and features use `feature`; bugs use `bugfix`; tasks and chores use the project default `feature`. Explicit `KIND` remains authoritative. Hotfix and release lanes require an explicit kind.

`EPIC=<bead>` creates a child lane from the current registered epic branch. The child lives at `<epic-worktree>/.worktrees/<slug>`, targets the epic branch in its pull request, and rejects a separate `BASE`.

Lane updates merge an advanced base with a non-fast-forward merge commit. Provisioning metadata is registered before setup so an identical start command can resume a failed lane. An epic lane cannot finish while Git still registers child lanes below it.
