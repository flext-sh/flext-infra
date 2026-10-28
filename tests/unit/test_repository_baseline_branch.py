"""Baseline resolution checks the declared integration line against live Git.

The workspace declares ONE versioned integration line
(``codegen.branch_policy.integration_branch``); resolution reads the
published ref for exactly that name — the remote-tracking branch or the
recorded release tag a consumer may pin. A repository that does not
publish the declared line fails loud — there is no conventional-name
list to probe and no default to invent — and a name published as both
branch and tag is ambiguous and fails loud.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

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

        tm.ok(resolved, eq=declared)

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

    @staticmethod
    def _seed_tag(repository_root: Path, tag: str) -> None:
        """Publish one recorded release tag exactly as a real clone would."""
        tm.ok(
            u.Cli.run_checked(
                ["git", "update-ref", f"refs/tags/{tag}", "HEAD"],
                cwd=repository_root,
            ),
        )

    def test_baseline_resolves_a_recorded_release_tag_line(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A consumer pinning a recorded release tag resolves the same way."""
        self._delete_published_references(infra_git_repo)
        declared = config.Infra.codegen.branch_policy.integration_branch
        self._seed_tag(infra_git_repo, declared)

        resolved = u.Infra.repository_baseline_branch(
            infra_git_repo,
            declared_branch=declared,
        )

        tm.ok(resolved, eq=declared)

    def test_baseline_fails_loud_when_the_line_is_ambiguous(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A name published as both branch and tag is ambiguous, never guessed."""
        self._delete_published_references(infra_git_repo)
        declared = config.Infra.codegen.branch_policy.integration_branch
        self._seed_remote_branch(infra_git_repo, declared)
        self._seed_tag(infra_git_repo, declared)

        resolved = u.Infra.repository_baseline_branch(
            infra_git_repo,
            declared_branch=declared,
        )

        tm.fail(resolved)
        tm.that(str(resolved.error), has="ambiguous")
