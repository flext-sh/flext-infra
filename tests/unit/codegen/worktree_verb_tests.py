"""Contract tests for the make-managed development-lane verb."""

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
        """Every generated project receives the governed worktree route.

        Declaring it in `extra_verbs` would make it repository-local, which
        would defeat the purpose: every project must expose the same lane
        surface.
        """
        tm.that(self._verb("worktree").name, eq="worktree")

    def test_worktree_defaults_to_a_read_only_selector(self) -> None:
        """The default operation reports state without mutating the repository.

        `list` is the only selector that reports state without touching the
        worktree registry, so it is the safe default.
        """
        verb = self._verb("worktree")
        tm.that(verb.whats[0], eq="list")

    def test_mutating_operations_own_the_apply_guard(self) -> None:
        """Read-only list remains usable without granting mutation authority.

        Guarding at verb level would force `APPLY=Y` onto `list`. The mutating
        selectors enforce the guard individually in their own recipes instead.
        """
        verb = self._verb("worktree")
        tm.that(verb.apply_guarded, eq=False)
