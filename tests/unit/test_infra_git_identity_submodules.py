"""Submodule facts reported by the canonical Git identity probe.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, u
from flext_tests import tm
from tests import u as test_u


class TestInfraGitIdentitySubmodules:
    """Report a superproject from the index, never from ``status --porcelain``.

    Gitlink modes (``160000``) appear only in the index listing. ``git status
    --porcelain`` emits XY status codes and paths and never a file mode, so
    deriving submodule facts from it silently reported every superproject as
    having no submodules.
    """

    @staticmethod
    def _repo(root: Path) -> Path:
        """Initialize one real Git repository carrying a single commit."""
        root.mkdir(parents=True, exist_ok=True)
        test_u.Tests.initialize_git_repo(root)
        return root

    @classmethod
    def _superproject(cls, tmp_path: Path) -> Path:
        """Build a real superproject whose index carries a gitlink entry."""
        child = cls._repo(tmp_path / "child")
        parent = cls._repo(tmp_path / "parent")
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(parent),
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "--quiet",
                str(child),
                "vendored",
            ])
        )
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(parent),
                "commit",
                "--quiet",
                "-m",
                "add submodule",
            ])
        )
        return parent

    def test_superproject_reports_its_submodules(self, tmp_path: Path) -> None:
        """A repository holding a gitlink is recognized as a superproject."""
        parent = self._superproject(tmp_path)
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=parent)))
        tm.that(identity.has_submodules, eq=True)

    def test_plain_repository_reports_no_submodules(self, tmp_path: Path) -> None:
        """A repository without any gitlink reports no submodules."""
        plain = self._repo(tmp_path / "plain")
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=plain)))
        tm.that(identity.has_submodules, eq=False)

    def test_submodule_checkout_is_not_a_superproject(self, tmp_path: Path) -> None:
        """The nested checkout is a submodule, and owns none of its own."""
        parent = self._superproject(tmp_path)
        identity = tm.ok(
            u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=parent / "vendored"))
        )
        tm.that(identity.has_submodules, eq=False)
        tm.that(identity.is_submodule, eq=True)
