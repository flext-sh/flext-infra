# Next session: finish flext-ezljc plan (flext-infra)

Work in worktree cwd only (no cd, env -C, make -C). Never git restore/reset/stash/rebase, --no-verify, force-push or --admin. Stage explicit paths; commit/PR text from files. Commit+push need no manual gates: hooks run setup/check, integration CI decides. DONE = merged at 0.12.0-dev, CI green, active at runtime. Long runs in background. Keep update_plan todo, plan file `/home/marlonsc/flext/.kilo/plans/1795222544305-flext-ezljc-rope-consolidator-continuation.md` (tick only the top TODO) and artifact https://claude.ai/artifact/McPdBpocA5CVYaJu4Fusto updated per phase.

## State
- Branch `fix/flext-4wa0l-setup-trust-first` (worktree `/home/marlonsc/flext/flext-infra/worktrees/flext-ezljc`) pushed with commit "fix(make): provision setup without inherited Mise overrides (flext-4wa0l)": Makefile.j2 runs `_setup_provision` under `env -u MISE_*`; Makefile regenerated. The push reported `[new branch]`: check whether PR #2752 still exists for that branch; open a new PR to 0.12.0-dev if not. Merge on green with a merge commit.
- Merged earlier: flext-infra #2750 #2751 #2753; flext #738 #741 #742; agents #389 #396 #405.

## TODO
1. Land flext-4wa0l (above); close bead.
2. flext-3gjbc Phase A (native testmon, DB = `<root>/.testmondata`): uncommitted in worktree `/home/marlonsc/flext/flext-infra/worktrees/flext-3gjbc` (branch fix/flext-3gjbc-testmon-native, −928/+98, 27 files). Merge 0.12.0-dev tip in, make setup, commit, push, PR, merge.
3. Phase B + flext-bga5y: redesign before code. Open findings: residue in `_utilities/pytest_collection.py` and `_constants/check.py`; prove `--testmon-forceselect` + `-m` under xdist `-n`; config-YAML digest needs a definite native replacement (not drop); slow+ordinary in one process conflicts with per-marker-scope testmon env; bounding FULL at 240 s is a policy change — ask operator; budget arg required only in `cli_routes_workspace.py:117`; option name is `flext_slow_timeout_seconds`.
4. flext-m6igj (alias test >2 s, first Rope analysis): in rope fork `externaldata.py` `_plan_context`, compute direct writes (incl. unpacked targets via ast.walk) before the global scan and return early when empty; add `if not plans: return None` in `import_source_name`. Measure; split the test only if still >2 s.
5. Runtime proof: cold `make tests` within 240 s / 20 s slow / 2 s per test.
6. Close beads flext-4wa0l, 3gjbc, bga5y, m6igj, q7be8 / aihub-fw6dz; rig sweep after aihub-d8cc7; retire worktrees only via `ai-hub wip sweep` or ancestry proof.
