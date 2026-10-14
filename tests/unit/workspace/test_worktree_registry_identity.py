"""Authenticate primary worktree identity through real Git storage metadata.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, m, tm, u


class TestsFlextInfraWorktreeRegistryIdentity:
    """A storage-only registry row requires a verified checkout and backlink."""

    @staticmethod
    def _attached(tmp_path: Path) -> tuple[Path, Path, Path]:
        source = tmp_path / "source"
        parent = tmp_path / "parent"
        source.mkdir()
        parent.mkdir()
        u.Tests.initialize_git_repo(source)
        u.Tests.initialize_git_repo(parent)
        tm.ok(
            u.Cli.run_checked(
                (
                    c.Infra.GIT,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    str(source),
                    "member",
                ),
                cwd=parent,
            ),
        )
        primary = parent / "member"
        linked = tmp_path / "linked"
        tm.ok(
            u.Cli.run_checked(
                (
                    c.Infra.GIT,
                    "worktree",
                    "add",
                    "--detach",
                    str(linked),
                    c.Infra.GIT_HEAD,
                ),
                cwd=primary,
            ),
        )
        common = Path(
            tm.ok(
                u.Cli.capture(
                    (
                        c.Infra.GIT,
                        "rev-parse",
                        c.Infra.GIT_REV_PARSE_ABSOLUTE_PATHS,
                        "--git-common-dir",
                    ),
                    cwd=linked,
                ),
            ).strip(),
        )
        return primary, linked, common

    @staticmethod
    def _set_primary(common: Path, linked: Path, value: str) -> None:
        tm.ok(
            u.Cli.run_checked(
                (
                    c.Infra.GIT,
                    "config",
                    "--file",
                    str(common / "config"),
                    "core.worktree",
                    value,
                ),
                cwd=linked,
            ),
        )

    @pytest.mark.parametrize("absolute", [False, True])
    def test_linked_submodule_authenticates_its_configured_primary(
        self, tmp_path: Path, absolute: bool
    ) -> None:
        """Relative and absolute common-config paths identify the same real checkout."""
        primary, linked, common = self._attached(tmp_path)
        if absolute:
            self._set_primary(common, linked, str(primary))
        config_before = (common / "config").read_bytes()
        pointer_before = (primary / c.Infra.GIT_DIR).read_bytes()
        registry_before = tm.ok(
            u.Cli.capture((c.Infra.GIT, "worktree", "list", "--porcelain"), cwd=linked),
        )

        from_linked = tm.ok(
            u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=linked)),
        )
        from_primary = tm.ok(
            u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=primary)),
        )

        tm.that(
            tuple(entry.path for entry in from_linked.entries),
            eq=(primary.resolve(), linked.resolve()),
        )
        tm.that(from_linked.entries, eq=from_primary.entries)
        tm.that(
            tm.ok(
                u.Infra.git_primary_worktree_root(
                    m.Infra.GitRepoRequest(repo_root=linked),
                ),
            ).primary_root,
            eq=primary.resolve(),
        )
        tm.that((common / "config").read_bytes(), eq=config_before)
        tm.that((primary / c.Infra.GIT_DIR).read_bytes(), eq=pointer_before)
        tm.that(
            tm.ok(
                u.Cli.capture(
                    (c.Infra.GIT, "worktree", "list", "--porcelain"), cwd=linked
                ),
            ),
            eq=registry_before,
        )

    @pytest.mark.parametrize(
        "defect",
        [
            "missing-config",
            "empty-config",
            "foreign-storage",
            "missing-checkout",
            "gitfile",
        ],
    )
    def test_unproven_storage_primary_remains_a_failure(
        self, tmp_path: Path, defect: str
    ) -> None:
        """A missing declaration or broken checkout binding cannot authenticate storage."""
        primary, linked, common = self._attached(tmp_path)
        if defect == "missing-config":
            tm.ok(
                u.Cli.run_checked(
                    (
                        c.Infra.GIT,
                        "config",
                        "--file",
                        str(common / "config"),
                        "--unset",
                        "core.worktree",
                    ),
                    cwd=linked,
                ),
            )
        elif defect == "empty-config":
            self._set_primary(common, linked, "")
        elif defect == "foreign-storage":
            foreign = tmp_path / "foreign"
            foreign.mkdir()
            u.Tests.initialize_git_repo(foreign)
            self._set_primary(common, linked, str(foreign))
        elif defect == "missing-checkout":
            self._set_primary(common, linked, str(tmp_path / "absent"))
        else:
            (primary / c.Infra.GIT_DIR).write_text(
                f"gitdir: {tmp_path / 'absent-storage'}\n",
                encoding=c.DEFAULT_ENCODING,
            )

        tm.fail(u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=linked)))
        tm.that(linked.is_dir(), eq=True)

    @pytest.mark.parametrize("bare", [False, True])
    def test_regular_and_bare_registries_preserve_native_identity(
        self, tmp_path: Path, bare: bool
    ) -> None:
        """Ordinary primary rows and explicitly bare storage keep their native meaning."""
        source = tmp_path / "source"
        source.mkdir()
        u.Tests.initialize_git_repo(source)
        owner = source
        if bare:
            owner = tmp_path / "bare"
            tm.ok(
                u.Cli.run_checked(
                    (c.Infra.GIT, "clone", "--bare", str(source), str(owner)),
                    cwd=tmp_path,
                ),
            )
        linked = tmp_path / "linked"
        tm.ok(
            u.Cli.run_checked(
                (
                    c.Infra.GIT,
                    "worktree",
                    "add",
                    "--detach",
                    str(linked),
                    c.Infra.GIT_HEAD,
                ),
                cwd=owner,
            ),
        )

        report = tm.ok(
            u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=linked)),
        )

        tm.that(report.entries[0].path, eq=owner.resolve())
        tm.that(report.entries[0].bare, eq=bare)
        tm.that(report.entries[1].path, eq=linked.resolve())
