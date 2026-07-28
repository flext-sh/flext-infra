"""Contract tests for the make-managed development-lane verb.

A development lane is where feature, bugfix and hotfix work is executed. The
lane must be reachable through the canonical Make surface, so that consumers
never call `git worktree` directly, and it must live inside the repository it
belongs to.

These tests pin the declarative contract only. The lane lifecycle itself is
exercised by the service tests; here we prove that the generated Make surface
exposes it at all, and that it cannot be invoked destructively by accident.
"""

from __future__ import annotations

from flext_infra import config, m
from flext_tests import tm


class TestsCodegenWorktreeVerb:
    """The `worktree` verb is part of the canonical public Make surface."""

    def _verb(self, name: str) -> m.Infra.MakeVerbSpec:
        matches = tuple(
            verb for verb in config.Infra.codegen.make.verbs if verb.name == name
        )
        tm.that(matches, len=1)
        return matches[0]

    def test_worktree_is_a_canonical_public_verb(self) -> None:
        """Lanes are created through `make`, so the verb must be canonical.

        Declaring it in `extra_verbs` would make it repository-local, which
        would defeat the purpose: every project must expose the same lane
        surface.
        """
        tm.that(self._verb("worktree").name, eq="worktree")

    def test_worktree_defaults_to_a_read_only_selector(self) -> None:
        """`make worktree` with no WHAT must never mutate a repository.

        `list` is the only selector that reports state without touching the
        worktree registry, so it is the safe default.
        """
        verb = self._verb("worktree")
        tm.that(verb.default_what, eq="list")

    def test_worktree_is_not_verb_level_apply_guarded(self) -> None:
        """The read-only default must not demand APPLY=Y.

        Guarding at verb level would force `APPLY=Y` onto `list`. The mutating
        selectors enforce the guard individually in their own recipes instead.
        """
        verb = self._verb("worktree")
        tm.that(verb.apply_guarded, eq=False)
