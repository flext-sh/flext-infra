"""Native governance classification follows project facts, without declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraDetectedProjectKind:
    """Exercise the public configuration boundary against real project inputs."""

    @staticmethod
    def test_dependency_change_updates_kind_without_yaml_changes(
        tmp_path: Path,
    ) -> None:
        """A YAML memo cannot freeze facts owned by native package metadata."""
        u.Tests.write_native_resolution_project(tmp_path, "ordinary-project")
        before = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        tm.that(before.kind, eq=c.Infra.ProjectKind.INTERNAL)
        u.Tests.write_native_resolution_project(
            tmp_path, "ordinary-project", dependencies=(c.Infra.PKG_CORE,)
        )
        after = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        tm.that(after.kind, eq=c.Infra.ProjectKind.INTERNAL_FLEXT)
        tm.that(after.sources, eq=before.sources)

    @staticmethod
    def test_native_imports_identify_a_flext_consumer(tmp_path: Path) -> None:
        """Native source imports establish consumption independently of metadata."""
        u.Tests.write_native_resolution_project(tmp_path, "import-consumer")
        source = tmp_path / "src" / "import_consumer" / "__init__.py"
        source.write_text("from flext_core import m\n", encoding=c.DEFAULT_ENCODING)
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.INTERNAL_FLEXT,
        )

    @staticmethod
    def test_composition_uses_child_dependency_facts(tmp_path: Path) -> None:
        """An ordinary workspace is governed when its composed child uses FLEXT."""
        u.Tests.write_native_resolution_project(tmp_path, "ordinary-workspace")
        child = tmp_path / "member"
        u.Tests.write_native_resolution_project(
            child, "member", dependencies=(c.Infra.PKG_CORE,)
        )
        (tmp_path / c.Infra.GITMODULES).write_text(
            '[submodule "member"]\n'
            "\tpath = member\n"
            "\turl = https://github.example/owner/member.git\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.INTERNAL_FLEXT,
        )

    @staticmethod
    def test_distinct_native_upstream_preserves_fork_governance(tmp_path: Path) -> None:
        """A third-party fork is proven by its actual native upstream identity."""
        u.Tests.write_native_resolution_project(tmp_path, "upstream-project")
        u.Tests.git_bootstrap(tmp_path, ("init",))
        for name, owner in (("origin", "consumer"), ("upstream", "upstream")):
            u.Tests.git_bootstrap(
                tmp_path,
                ("remote", "add", name, f"https://github.example/{owner}/project.git"),
            )
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.THIRD_PARTY_FORK,
        )
