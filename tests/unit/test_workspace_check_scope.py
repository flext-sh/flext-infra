"""Tests that the workspace-root check surface covers every declared member.

A workspace root that lints only its own src/ and tests/ cannot validate the
members it orchestrates, so a global gate degrades into a root-only gate and
member regressions ship unnoticed.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

import flext_infra
from flext_infra import c, config


class TestsFlextInfraWorkspaceCheckScope:
    def test_workspace_root_check_paths_cover_every_member(self) -> None:
        """The generated root Makefile lints the members, not only itself."""
        # Members come from the workspace manifest SSOT, never a literal list.
        members = tuple(
            repository.path.as_posix()
            for repository in config.Infra.codegen.repositories
            if repository.role == c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        tm.that(bool(members), eq=True)

        template = (
            Path(flext_infra.__file__).resolve().parent
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        ).read_text(encoding="utf-8")

        # RUFF_PATHS/MYPY_PATHS must expand over the members for the root
        # profile instead of being pinned to the root's own src/tests.
        tm.that(template, has="WORKSPACE_CHECK_PATHS")
