"""The root dev group provisions declared members without sharing their locks.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import tm, u


class TestsFlextInfraCodegenWorkspaceMemberGroup:
    """Tests for ``FlextInfraCodegenWorkspaceMemberGroup``."""

    @staticmethod
    def test_activation_producers_do_not_reinstall_the_declared_graph(
        tmp_path: Path,
    ) -> None:
        """Projection repair precedes provenance; only setup provisions dependencies."""
        root, _ = u.Tests.render_make_environment(tmp_path, c.Infra.MakeProfile.WORKSPACE)
        rendered = (root / "Makefile").read_text(encoding="utf-8")
        for verb in config.Infra.codegen.make.verbs:
            if verb.produces_activation:
                prerequisite = next(
                    line
                    for line in rendered.splitlines()
                    if line.startswith(f"{verb.name}:")
                )
                tm.that("_builtin_require_interpreter" in prerequisite, eq=True)
                tm.that("_builtin_require_environment" in prerequisite, eq=False)
        tm.that("LOCAL_EDITABLE_FLAGS" in rendered, eq=False)
        environment = rendered.split("_builtin_require_environment:", 1)[1].split(
            "\nendif", 1
        )[0]
        tm.that("pip install" in environment, eq=False)
        tm.that("sync --project" in environment, eq=False)

    @staticmethod
    @pytest.mark.slow
    def test_workspace_root_group_survives_conform_at_a_fixed_point(
        tmp_path: Path,
    ) -> None:
        """Real root conform declares every attached member and converges."""
        root = tmp_path / "workspace"
        _ = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        root_pyproject = root / c.PYPROJECT_FILENAME
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(repository_root=root, request=request)
        first = tm.ok(service.plan(request))
        members = first.workspace.subprojects
        tm.that(len(members), eq=1)
        rendered = u.Tests.codegen_file_text(
            next(item for item in first.files if item.path == root_pyproject),
        )
        sources = u.Tests.toml_table_at(rendered, "tool", "uv", "sources")
        for member in members:
            tm.that(
                sources[member.distribution],
                eq={"path": member.path.as_posix(), "editable": member.editable},
            )
            tm.that(
                member.distribution
                in {
                    u.Infra.dep_name(line)
                    for line in u.Tests.toml_strings_at(
                        rendered, "dependency-groups", "dev"
                    )
                },
                eq=True,
            )
        tm.that("workspace" in u.Tests.toml_table_at(rendered, "tool", "uv"), eq=False)
        tm.that(
            "workspace" in u.Tests.toml_table_at(rendered, c.Infra.DEPENDENCY_GROUPS),
            eq=False,
        )
        root_pyproject.write_text(rendered, encoding="utf-8")
        second = tm.ok(service.plan(request))
        tm.that(
            u.Tests.codegen_file_text(
                next(item for item in second.files if item.path == root_pyproject),
            ),
            eq=rendered,
        )
