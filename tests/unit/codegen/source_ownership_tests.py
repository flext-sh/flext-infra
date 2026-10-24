"""Declared project queries and immutable dependency payload boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraCodegenLazyInit
from tests import c, m, p, tm, u


class TestsFlextInfraSourceOwnership:
    """Exercise the native source reader through its public planning facade."""

    @staticmethod
    @pytest.mark.parametrize("width", ["short", "wrapped"])
    def test_future_local_exports_keep_the_elected_package_resource(
        tmp_path: Path, installed_dependency_path: Path, width: str
    ) -> None:
        """An ambient regular package cannot replace an elected future declaration."""
        root = u.Tests.git_repository(tmp_path / "planned")
        package_name = "future_owned"
        if width == "wrapped":
            limit = u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff", "line-length", int
            )
            while len(f"    from {package_name}._constants.settings import (") <= limit:
                package_name += "_x"
        provider = installed_dependency_path / package_name
        provider.mkdir()
        (provider / c.Infra.INIT_PY).write_text(
            "__all__ = []\n", encoding=c.DEFAULT_ENCODING
        )
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'future-owned'\nversion = '1.0.0'\n"
            "authors = [{name = 'Native Source Test'}]\n"
            "license = 'MIT'\n"
            "[tool.hatch.build.targets.wheel]\n"
            f"packages = ['src/{package_name}']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / package_name
        settings = package / "_constants" / "settings.py"
        planned = {
            settings: (
                "class FlextFutureOwnedSettingsConstants: pass\n"
                "c = FlextFutureOwnedSettingsConstants\n"
                "__all__ = ['FlextFutureOwnedSettingsConstants', 'c']\n"
            ),
        }
        with u.Infra.facade_source_project(root, planned_sources=planned) as (
            project,
            _,
        ):
            tm.that(project.source_query(settings, "isfile"), eq=True)
            tm.that(
                Path(tm.not_none(project.find_module(package_name)).real_path),
                eq=provider,
            )
            analysis = tm.ok(
                FlextInfraCodegenLazyInit(repository_root=root).plan_files(
                    source_project=project
                )
            )
            tm.that(analysis.issues, eq=())
            target = next(
                file
                for file in analysis.files
                if file.path == settings.parent / c.Infra.INIT_PY
            )
            text = tm.not_none(target.desired_content).decode(c.DEFAULT_ENCODING)
            tm.that(text, contains="FlextFutureOwnedSettingsConstants")
            tm.fail(package.exists())

    @staticmethod
    @pytest.mark.parametrize(
        "surface",
        [
            c.Infra.CodegenConformSurface.LAZY_INIT,
            c.Infra.CodegenConformSurface.FACADES,
        ],
    )
    def test_scoped_publication_leaves_unselected_tracked_content(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        surface: c.Infra.CodegenConformSurface,
    ) -> None:
        """Scoped generation publishes once and never touches unselected content."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(root))
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        utilities = package / c.Infra.UTILITIES_PY
        u.Tests.write_lazy_init_namespace_module(
            utilities, class_name=f"{layout.class_stem}{family.suffix}", alias="u"
        )
        owner = package / family.directory
        owner.mkdir()
        (owner / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (owner / "reader.py").write_text(
            "class Reader:\n"
            "    @staticmethod\n"
            "    def read() -> int:\n"
            "        return 1\n"
            "__all__ = ['Reader']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        guide = root / "docs" / "guides" / "execution-context.md"
        guide.parent.mkdir(parents=True)
        guide.write_text("# Original unselected guide\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.git_bootstrap(root, ("add", "--", str(guide.relative_to(root))))
        tm.ok(
            u.Tests.create_python_environment(
                root,
                dependency_projects=u.Tests.python_dependency_projects(root),
                session_runtime=session_runtime,
            )
        )
        request = m.Infra.CodegenGenerateRequest(
            root=root,
            what=surface,
            module=(
                package.name
                if surface == c.Infra.CodegenConformSurface.LAZY_INIT
                else f"{package.name}.{utilities.stem}"
            ),
        )
        tm.ok(infra.codegen_generate(request))
        target = (
            package / c.Infra.INIT_PY
            if surface == c.Infra.CodegenConformSurface.LAZY_INIT
            else utilities
        )
        published = target.read_bytes()
        tm.ok(infra.codegen_generate(request))
        tm.that(target.read_bytes(), eq=published)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.utilities import u\n"
                f"assert u.__name__ == {f'{layout.class_stem}{family.suffix}'!r}\n"
                + (
                    "assert u.read() == 1\n"
                    if surface == c.Infra.CodegenConformSurface.FACADES
                    else f"import {package.name} as package\nassert package.u is u\n"
                )
                + "print('consumed')\n",
                python_paths=(str(layout.src_dir),),
                cwd=root,
            ),
            eq=["consumed"],
        )
        tm.that(
            guide.read_text(encoding=c.DEFAULT_ENCODING),
            eq="# Original unselected guide\n",
        )

    @staticmethod
    @pytest.mark.parametrize("nested", [False, True])
    def test_dependency_membership_is_not_project_ownership(
        tmp_path: Path, *, nested: bool
    ) -> None:
        """The elected runtime has the same query boundary inside or outside root."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        runtime = (root if nested else tmp_path) / "dependency_runtime"
        runtime.mkdir()
        source = runtime / "provider.py"
        source.write_text("class Provider:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        candidate = runtime / "new_package" / "__init__.py"
        with (
            tm.scope(python_paths=(str(runtime),)),
            u.Infra.facade_source_project(root) as (project, sources),
        ):
            tm.fail(project.source_query(candidate, "isfile"))
            tm.that(project.source_children(runtime), has=source)
            tm.that(project.source_text(source), eq="class Provider:\n    pass\n")
            tm.fail(any(path.is_relative_to(runtime) for path in sources))
            tm.that(project.source_query(package / "absent.py", "isfile"), eq=False)
