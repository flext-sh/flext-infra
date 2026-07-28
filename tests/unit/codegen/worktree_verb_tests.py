"""Contract tests for the make-managed development-lane verb."""

from __future__ import annotations

from flext_tests import tm

from flext_infra import config


class TestsCodegenWorktreeVerb:
    """The worktree lifecycle is part of the canonical public Make surface."""

    def test_worktree_is_a_canonical_public_verb(self) -> None:
        """Every generated project receives the governed worktree route."""
        verbs = {verb.name: verb for verb in config.Infra.codegen.make.verbs}

        tm.that("worktree" in verbs, eq=True)

    def test_worktree_defaults_to_a_read_only_selector(self) -> None:
        """The default operation reports state without mutating the repository."""
        verbs = {verb.name: verb for verb in config.Infra.codegen.make.verbs}
        worktree = verbs["worktree"]

        tm.that(worktree.default_what, eq="list")

    def test_mutating_operations_own_the_apply_guard(self) -> None:
        """Read-only list remains usable without granting mutation authority."""
        verbs = {verb.name: verb for verb in config.Infra.codegen.make.verbs}
        worktree = verbs["worktree"]

        tm.that(worktree.apply_guarded, eq=False)
