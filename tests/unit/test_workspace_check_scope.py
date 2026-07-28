"""Tests that the workspace-root check surface covers every declared member.

A workspace root that lints only its own src/ and tests/ cannot validate the
members it orchestrates, so a global gate degrades into a root-only gate and
member regressions ship unnoticed.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_infra import c, config
from flext_tests import tm


class TestsFlextInfraWorkspaceCheckScope:
    def test_workspace_root_check_orchestrates_every_member(self) -> None:
        """The root check delegates to the manifest-backed member orchestrator."""
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

        tm.that(
            template, has="WORKSPACE_MEMBERS :={% for member in workspace_members %}"
        )
        tm.that(
            template,
            has="@$(WORKSPACE_ORCHESTRATE) --verb check $(ORCHESTRATE_PROJECT_ARGS)",
        )
        tm.that(template, has="ALLOWED_PROJECTS := . $(WORKSPACE_MEMBERS)")
