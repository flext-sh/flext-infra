"""Baseline resolution checks the declared integration line against live Git.

The workspace declares ONE versioned integration line
(``codegen.branch_policy.integration_branch``); resolution reads the
published remote-tracking ref for exactly that line. A repository that does
not publish the declared line fails loud — there is no conventional-name
list to probe and no default to invent.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import tm, u


class TestsFlextInfraRepositoryBaselineBranch:
    """Contract for resolving one repository's declared integration baseline."""

    @staticmethod
    def _seed_remote_branch(repository_root: Path, branch: str) -> None:
        """Publish one remote-tracking branch exactly as a real clone would."""
        tm.ok(
            u.Cli.run_checked(
                ["git", "update-ref", f"refs/remotes/origin/{branch}", "HEAD"],
                cwd=repository_root,
            ),
        )

    @staticmethod
    def _delete_published_references(repository_root: Path) -> None:
        """Drop every published remote-tracking reference one clone carries."""
        seeded = u.Cli.capture(
            ["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"],
            cwd=repository_root,
        )
        tm.ok(seeded)
        for reference in seeded.value.split():
            tm.ok(
                u.Cli.run_checked(
                    ["git", "update-ref", "-d", reference],
                    cwd=repository_root,
                ),
            )

    def test_baseline_resolves_the_declared_published_line(
        self,
        infra_git_repo: Path,
    ) -> None:
        """The declared line resolves when published Git carries it."""
        self._delete_published_references(infra_git_repo)
        declared = config.Infra.codegen.branch_policy.integration_branch
        self._seed_remote_branch(infra_git_repo, declared)

        resolved = u.Infra.repository_baseline_branch(
            infra_git_repo,
            declared_branch=declared,
        )

        tm.ok(resolved)
        tm.that(resolved.value, eq=declared)

    @staticmethod
    def test_baseline_fails_loud_without_the_declared_line(
        tmp_path: Path,
    ) -> None:
        """A checkout that does not publish the declared line never guesses."""
        empty = tmp_path / "no-declared-line"
        empty.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.run_checked(["git", "init"], cwd=empty))
        declared = config.Infra.codegen.branch_policy.integration_branch

        resolved = u.Infra.repository_baseline_branch(
            empty,
            declared_branch=declared,
        )

        tm.fail(resolved)
        tm.that(str(resolved.error), has=f"declared {declared}")
