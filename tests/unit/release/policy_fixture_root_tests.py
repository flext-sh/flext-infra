"""Contract test for how release fixtures locate workspace-owned policy files.

The release workspace fixture copies workspace-owned policy files (build
constraints, gitleaks config) into a temporary workspace. It has to find them
first, and it must keep finding them regardless of where the repository is
checked out.

Counting parent directories encodes the checkout depth into the test suite. A
linked worktree adds path segments, so a positional lookup silently resolves to
a directory that holds no policy file and every release test fails with
FileNotFoundError -- a failure that says nothing about the code under test.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c
from tests import u


class TestsReleasePolicyFixtureRoot:
    """Policy sources are located by discovery, not by parent counting."""

    def test_policy_sources_resolve_from_the_checkout_in_use(self) -> None:
        """The fixture's policy sources must exist for the current checkout.

        This is the invariant the release suite depends on. It holds in a plain
        clone and must equally hold in a linked worktree, where the repository
        sits deeper in the filesystem.
        """
        workspace_root = u.Tests.release_policy_root()

        for policy_path in (
            c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH,
            c.Infra.RELEASE_GITLEAKS_CONFIG_PATH,
        ):
            tm.that((workspace_root / policy_path).is_file(), eq=True)

    def test_policy_root_is_not_derived_by_counting_parents(self) -> None:
        """A fixed parent index cannot be correct for every checkout layout.

        `tests/utilities.py` -> parents[2] resolves to the workspace root only
        when the repository is exactly two levels below it. Inside
        `<repo>/.worktrees/<lane>/` the same index lands mid-path.
        """
        positional = Path(u.Tests.__module__.replace(".", "/"))
        tm.that(u.Tests.release_policy_root(), ne=positional)
