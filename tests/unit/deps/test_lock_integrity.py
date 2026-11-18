"""Committed generated TOML lock integrity verification tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m
from flext_infra.deps import FlextInfraLockIntegrityVerifier
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


@c.Tests.MARK.usefixtures("repository")
class TestsFlextInfraDepsLockIntegrity:
    """Validate committed generated lock verification through its public model."""

    @u.Tests.fixture
    @staticmethod
    def repository(
        tmp_path: Path,
    ) -> None:
        """Every lock scenario starts from an initialized Git repository."""
        u.Tests.initialize_git_repo(tmp_path)

    @staticmethod
    def _write_uv_lock(root: Path, content: str) -> None:
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(root))
        tm.ok(u.Cli.ensure_dir(context.lock_path.parent))
        tm.ok(u.Cli.atomic_write_text_file(context.lock_path, content))

    @staticmethod
    def _verifier(repository_root: Path) -> FlextInfraLockIntegrityVerifier:
        """Build the public verifier command for one repository root.

        Returns:
            The resulting ``FlextInfraLockIntegrityVerifier``.

        """
        return FlextInfraLockIntegrityVerifier(repository_root=repository_root)

    def test_healthy_locks_verify_green(self, tmp_path: Path) -> None:
        """Parseable locks without repeated sections verify successfully."""
        (tmp_path / c.Infra.MISE_LOCK_FILENAME).write_text(
            '[tools."github:kucherenko/jscpd"]\nversion = "5.3.3"\n',
            encoding="utf-8",
        )
        self._write_uv_lock(
            tmp_path,
            'version = 1\n[[package]]\nname = "filelock"\nversion = "4.0.6"\n',
        )
        result = self._verifier(tmp_path).execute()
        tm.ok(result)
        tm.ok(result.value)

    def test_duplicated_sections_fail_with_file_and_keys(self, tmp_path: Path) -> None:
        """A merge-concatenated lock fails naming the file and duplicated keys."""
        (tmp_path / c.Infra.MISE_LOCK_FILENAME).write_text(
            '[tools."github:kucherenko/jscpd".options]\n'
            'asset_pattern = "jscpd-linux-x64-gnu.tar.gz"\n'
            "\n"
            '[tools."github:kucherenko/jscpd".options]\n'
            'asset_pattern = "jscpd-darwin-x64.tar.gz"\n',
            encoding="utf-8",
        )
        self._write_uv_lock(
            tmp_path,
            "version = 1\n",
        )
        error = tm.fail(self._verifier(tmp_path).execute())
        tm.that(error, has=c.Infra.MISE_LOCK_FILENAME)
        tm.that(error, has="duplicated sections")
        tm.that(error, has='tools."github:kucherenko/jscpd".options')

    def test_unparseable_lock_fails_with_parser_cause(self, tmp_path: Path) -> None:
        """A lock that is not TOML fails with the strict parser cause."""
        (tmp_path / c.Infra.MISE_LOCK_FILENAME).write_text(
            "not toml at all\n",
            encoding="utf-8",
        )
        self._write_uv_lock(
            tmp_path,
            "version = 1\n",
        )
        error = tm.fail(self._verifier(tmp_path).execute())
        tm.that(error, has=c.Infra.MISE_LOCK_FILENAME)

    def test_missing_locks_fail_loud(self, tmp_path: Path) -> None:
        """A repository root without any committed generated lock fails loud."""
        error = tm.fail(self._verifier(tmp_path).execute())
        tm.that(error, has="missing committed generated lock")

    def test_root_lock_does_not_replace_the_selected_view(self, tmp_path: Path) -> None:
        """A stale legacy lock cannot turn an absent selected lock into success."""
        for filename in (c.Infra.MISE_LOCK_FILENAME, c.Infra.UV_LOCK_FILENAME):
            (tmp_path / filename).write_text("version = 1\n", encoding="utf-8")

        tm.fail(
            self._verifier(tmp_path).execute(), has="missing committed generated lock"
        )

    def test_verify_pin_convergence_passes_on_single_repo(self, tmp_path: Path) -> None:
        """A single repository with valid Git pins in uv.lock passes convergence."""
        sha_a = "a" * 40
        repo = "https://github.com/flext-sh/flext-core.git?rev=0.12.0-dev"
        self._write_uv_lock(
            tmp_path,
            f'[[package]]\nname = "flext-core"\nsource = '
            f'{{ git = "{repo}#{sha_a}" }}\n',
        )
        tm.ok(
            FlextInfraLockIntegrityVerifier.verify_pin_convergence(
                m.Infra.WorkspaceRequest(repository_root=tmp_path),
            ),
        )

    @staticmethod
    def test_verify_pin_convergence_fails_on_divergent_shas(tmp_path: Path) -> None:
        """Divergent Git SHAs across two governed uv.lock files fail loudly."""
        sha_a = "a" * 40
        sha_b = "b" * 40
        repo = "https://github.com/flext-sh/flext-core.git?rev=0.12.0-dev"
        member_a = tmp_path / "pkg-a"
        member_b = tmp_path / "pkg-b"
        for member in (member_a, member_b):
            member.mkdir()
            u.Tests.initialize_git_repo(member)
            (member / c.Infra.MAKEFILE_FILENAME).write_text("all:\n", encoding="utf-8")
            (member / c.Infra.PYPROJECT_FILENAME).write_text(
                f'[project]\nname = "{member.name}"\nversion = "0.1.0"\n',
                encoding="utf-8",
            )
        (tmp_path / ".gitmodules").write_text(
            '[submodule "pkg-a"]\n\tpath = pkg-a\n\turl = https://example.com/pkg-a.git\n'
            '[submodule "pkg-b"]\n\tpath = pkg-b\n\turl = https://example.com/pkg-b.git\n',
            encoding="utf-8",
        )
        (member_a / c.Infra.UV_LOCK_FILENAME).write_text(
            f'[[package]]\nname = "flext-core"\nsource = '
            f'{{ git = "{repo}#{sha_a}" }}\n',
            encoding="utf-8",
        )
        (member_b / c.Infra.UV_LOCK_FILENAME).write_text(
            f'[[package]]\nname = "flext-core"\nsource = '
            f'{{ git = "{repo}#{sha_b}" }}\n',
            encoding="utf-8",
        )
        tm.fail(
            FlextInfraLockIntegrityVerifier.verify_pin_convergence(
                m.Infra.WorkspaceRequest(repository_root=tmp_path),
            ),
            has="git pin divergence",
        )
