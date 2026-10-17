"""Test detector init behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import m
from flext_infra.deps import FlextInfraDependencyDetectionService
from tests import c, t, tm, u


class TestsFlextInfraDepsDetectorInit:
    """Test flext infra deps detector init behavior."""

    @staticmethod
    def test_detect_command_normalizes_public_fields(tmp_path: Path) -> None:
        """Verify detect command normalizes public fields."""
        output_path = tmp_path / "out.json"
        params = m.Infra.DetectCommand(
            repository_root=tmp_path,
            apply=False,
            no_pip_check=True,
            output_format="json",
            output=str(output_path),
            quiet=True,
            no_fail=True,
            typings=True,
            apply_typings=True,
            limits="/custom/limits.toml",
        )
        tm.that(params.repository_root, eq=tmp_path.resolve())
        tm.that(params.no_pip_check, eq=True)
        tm.that(params.dry_run, eq=True)
        tm.that(params.output_format, eq="json")
        tm.that(str(params.output_path), eq=str(output_path.resolve()))
        tm.that(params.quiet, eq=True)
        tm.that(params.no_fail, eq=True)
        tm.that(params.typings, eq=True)
        tm.that(params.apply_typings, eq=True)
        tm.that(str(params.limits_path), eq=str(Path("/custom/limits.toml").resolve()))

    @staticmethod
    @pytest.mark.parametrize(
        "members",
        [(), ("flext-a",), ("flext-a", "flext-b", "flext-c")],
    )
    def test_detect_command_discovers_its_complete_declared_scope(
        tmp_path: Path, members: t.StrSequence
    ) -> None:
        """Standalone and workspace detection discover every declared project."""
        workspace = u.Tests.create_docs_workspace(tmp_path, project_names=members)
        u.Tests.write_package_init(
            workspace
            / c.Infra.DEFAULT_SRC_DIR
            / u.Infra.project_package_name(workspace),
            '"""Dependency detection fixture package."""\n',
        )
        params = m.Infra.DetectCommand(repository_root=workspace)
        projects = tm.ok(
            FlextInfraDependencyDetectionService.discover_project_paths(
                params.repository_root,
            ),
        )
        tm.that(
            projects,
            eq=sorted((workspace, *(workspace / member for member in members))),
        )

    @staticmethod
    def test_detect_command_excludes_undeclared_neighbor_projects(
        tmp_path: Path,
    ) -> None:
        """A complete declared scope does not adopt an unrelated local checkout."""
        workspace = u.Tests.create_docs_workspace(
            tmp_path,
            project_names=("flext-a",),
        )
        u.Tests.write_package_init(
            workspace
            / c.Infra.DEFAULT_SRC_DIR
            / u.Infra.project_package_name(workspace),
            '"""Dependency detection fixture package."""\n',
        )
        unlisted = u.Tests.mk_project(workspace, "unlisted", with_src=True)
        params = m.Infra.DetectCommand(repository_root=workspace)
        projects = tm.ok(
            FlextInfraDependencyDetectionService.discover_project_paths(
                params.repository_root,
            ),
        )
        tm.that(projects, eq=sorted((workspace, workspace / "flext-a")))
        tm.that(unlisted in projects, eq=False)
