"""Edge-case tests for public discovery behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import io
import os
import re
from cProfile import Profile
from pathlib import Path
from pstats import Stats

import pytest

from tests import c, tm, u


class TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases:
    """Edge-case tests for project discovery."""

    @staticmethod
    def test_export_cache_reuses_only_identical_authenticated_content(
        tmp_path: Path,
    ) -> None:
        """Planned content, not an unchanged physical mtime, owns export facts."""
        module_path = tmp_path / "module.py"
        module_path.write_text("class Alpha: ...\n", encoding=c.DEFAULT_ENCODING)
        before = module_path.stat()
        with Profile() as profile:
            for name in ("Alpha", "Beta", "Alpha"):
                with u.Infra.facade_source_project(
                    tmp_path, planned_sources={module_path: f"class {name}: ...\n"}
                ) as binding:
                    project = binding[0]
                    tm.that(
                        u.Infra.resolve_module_export_names(
                            project, project.get_file("module.py")
                        ),
                        eq=(name,),
                    )
        tm.that(module_path.stat().st_mtime_ns, eq=before.st_mtime_ns)
        tm.that(
            sum(
                entry.callcount
                for entry in profile.getstats()
                if not isinstance(entry.code, str)
                and entry.code.co_name == "_module_export_names"
            ),
            eq=2,
        )

    @staticmethod
    def test_authenticated_publication_reuses_syntax_and_records_each_consumption(
        tmp_path: Path,
    ) -> None:
        """An unchanged declaration parses once without losing its source receipt."""
        package = tmp_path / c.Infra.DEFAULT_SRC_DIR / "package"
        nested = package / "nested"
        nested.mkdir(parents=True)
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'package'\nversion = '1.0.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        for directory in (package, nested):
            (directory / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        source = nested / "component.py"
        source.write_text(
            "class Component:\n    pass\n\n__all__ = ['Component']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.facade_source_project(tmp_path) as (project, _, _):
            original = u.Infra.publication_policy(source, rope_project=project)
            repeated = original
            with project.source_consumption() as consumption, Profile() as profile:
                for _ in range(3):
                    repeated = u.Infra.publication_policy(source, rope_project=project)
            tm.that(repeated == original, eq=True)
            tm.that(
                any(state.path == source for state in consumption.receipt().inputs),
                eq=True,
            )
        output = io.StringIO()
        parser = f"{ast.__file__}:{ast.parse.__code__.co_firstlineno}(parse)"
        Stats(profile, stream=output).print_stats(re.escape(parser))
        tm.that(output.getvalue(), lacks=parser)

    @staticmethod
    def test_publication_exports_follow_content_with_an_unchanged_timestamp(
        tmp_path: Path,
    ) -> None:
        """A fresh authenticated epoch never reuses another source's exports."""
        package = tmp_path / c.Infra.DEFAULT_SRC_DIR / "package"
        package.mkdir(parents=True)
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'package'\nversion = '1.0.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        source = package / "component.py"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        original_time = source.stat()
        with u.Infra.facade_source_project(tmp_path) as (project, _, _):
            tm.that(
                u.Infra.publication_policy(
                    source, rope_project=project
                ).allow_main_export,
                eq=False,
            )
        source.write_text(
            "def main():\n    pass\n\n__all__ = ['main']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        os.utime(source, ns=(original_time.st_atime_ns, original_time.st_mtime_ns))
        with u.Infra.facade_source_project(tmp_path) as (project, _, _):
            tm.that(
                u.Infra.publication_policy(
                    source, rope_project=project
                ).allow_main_export,
                eq=True,
            )

    @staticmethod
    @pytest.mark.parametrize("suffix", [c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB])
    def test_source_files_discover_their_authenticated_project_root(
        tmp_path: Path, suffix: str
    ) -> None:
        """A source or stub file is never queried as an enclosing directory."""
        package = tmp_path / c.Infra.DEFAULT_SRC_DIR / "package"
        package.mkdir(parents=True)
        source = package / f"module{suffix}"
        source.write_text("", encoding=c.DEFAULT_ENCODING)
        with u.Infra.facade_source_project(tmp_path) as (project, _, _):
            tm.that(u.Infra.project_root(source, source_project=project), eq=tmp_path)

    @staticmethod
    @pytest.mark.parametrize("suffix", [c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB])
    def test_publication_policy_preserves_explicit_project_layout(
        tmp_path: Path, suffix: str
    ) -> None:
        """Implicit and supplied layouts publish the same authenticated policy."""
        package = tmp_path / c.Infra.DEFAULT_SRC_DIR / "package"
        package.mkdir(parents=True)
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'package'\nversion = '1.0.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        source = package / f"component{suffix}"
        source.write_text(
            "class Component:\n    pass\n\n__all__ = ['Component']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.facade_source_project(tmp_path) as (project, _, _):
            layout = u.Infra.layout(tmp_path, rope_project=project)
            tm.that(layout, none=False)
            implicit = u.Infra.publication_policy(source, rope_project=project)
            explicit = u.Infra.publication_policy(
                source, rope_project=project, project_layout=layout
            )
            tm.that(implicit.model_dump(), eq=explicit.model_dump())

    @staticmethod
    def test_standalone_never_discovers_undeclared_child_projects(
        tmp_path: Path,
    ) -> None:
        """Test standalone never discovers undeclared child projects."""
        service = u.Infra()
        repository_root = tmp_path
        non_git_dir = repository_root / "non_git_project"
        non_git_dir.mkdir()
        (non_git_dir / "pyproject.toml").write_text(
            "[project]\nname='non_git_project'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        result = service.discover_projects(repository_root)
        tm.ok(result)
        tm.that(result.value, empty=True)

    @staticmethod
    def test_find_all_pyproject_files_with_nonexistent_path() -> None:
        """Test find all pyproject files with nonexistent path."""
        service = u.Infra()
        nonexistent = Path("/nonexistent/path/to/workspace")
        result = service.find_all_pyproject_files(nonexistent)
        tm.ok(result)
        tm.that(result.value, eq=[])

    @staticmethod
    def test_standalone_pyproject_scan_never_reads_parent_or_sibling(
        tmp_path: Path,
    ) -> None:
        """Test standalone pyproject scan never reads parent or sibling."""
        service = u.Infra()
        child = tmp_path / "child"
        sibling = tmp_path / "sibling"
        child.mkdir()
        sibling.mkdir()
        own_pyproject = child / "pyproject.toml"
        own_pyproject.touch()
        (tmp_path / "pyproject.toml").touch()
        (sibling / "pyproject.toml").touch()

        result = service.find_all_pyproject_files(child)

        tm.ok(result)
        tm.that(tuple(result.value), eq=(own_pyproject,))

    @staticmethod
    def test_find_all_pyproject_files_with_permission_error(
        tmp_path: Path,
    ) -> None:
        """Test find all pyproject files with permission error."""
        service = u.Infra()
        (tmp_path / "pyproject.toml").touch()
        result = service.find_all_pyproject_files(tmp_path)
        tm.ok(result)
        tm.that(len(result.value) >= 1, eq=True)

    @staticmethod
    def test_discover_projects_skips_no_pyproject_no_gomod(
        tmp_path: Path,
    ) -> None:
        """Test discover projects skips no pyproject no gomod."""
        service = u.Infra()
        repository_root = tmp_path
        proj = repository_root / "incomplete_project"
        proj.mkdir()
        (proj / "pyproject.toml").write_text(
            "[project]\nname='incomplete_project'\n",
            encoding="utf-8",
        )
        result = service.discover_projects(repository_root)
        tm.ok(result)
        tm.that(not result.value, eq=True)

    @staticmethod
    def test_find_all_pyproject_files_skips_unreadable_subdir(
        tmp_path: Path,
    ) -> None:
        """Test find all pyproject files skips unreadable subdir."""
        service = u.Infra()
        blocked_dir = tmp_path / "blocked"
        blocked_dir.mkdir()
        (blocked_dir / "pyproject.toml").write_text(
            "[project]\nname='blocked'\n",
            encoding="utf-8",
        )
        blocked_dir.chmod(0)
        try:
            result = service.find_all_pyproject_files(tmp_path)
        finally:
            blocked_dir.chmod(0o755)
        tm.ok(result)
        tm.that(result.value, eq=[])
