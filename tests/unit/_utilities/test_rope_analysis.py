"""Tests for Rope semantic analysis helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import u
from flext_infra.detectors.facade_scanner import FlextInfraScanner

from pathlib import Path



class TestsFlextInfraRopeAnalysis:
    """Behavior contract for Rope-backed semantic analysis."""

    def test_facade_scanner_reads_facade_with_imported_superclass(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        _ = (package_dir / "constants.py").write_text(
            "from __future__ import annotations\n"
            "from flext_cli import FlextCliConstants\n\n"
            "class DemoProjectConstants(FlextCliConstants):\n"
            "    class Demo:\n"
            "        VALUE = 'ok'\n\n"
            "c = DemoProjectConstants\n"
            "__all__ = ['DemoProjectConstants', 'c']\n",
            encoding="utf-8",
        )

        with u.Infra.open_project(project) as rope_project:
            statuses = FlextInfraScanner.scan_project(
                project_root=project, rope_project=rope_project
            )

        constants_status = next(status for status in statuses if status.family == "c")
        tm.that(constants_status.exists, eq=True)
        tm.that(constants_status.class_name, eq="DemoProjectConstants")
        model_context = u.Infra.contextual_runtime_alias_sources(
            project_root=project, file_path=package_dir / "_models" / "brand.py"
        )
        settings_context = u.Infra.contextual_runtime_alias_sources(
            project_root=project, file_path=package_dir / "settings.py"
        )
        tm.that(model_context["m"], eq=frozenset({"flext_cli"}))
        tm.that(settings_context["m"], eq=frozenset({"flext_cli"}))

    def test_contextual_runtime_sources_resolve_parent_facade_alias_base(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        _ = (package_dir / "constants.py").write_text(
            "from __future__ import annotations\n"
            "from flext_cli import c\n\n"
            "class DemoProjectConstants(c):\n"
            "    class Demo:\n"
            "        VALUE = 'ok'\n\n"
            "c = DemoProjectConstants\n"
            "__all__ = ['DemoProjectConstants', 'c']\n",
            encoding="utf-8",
        )

        parent_packages = u.Infra.resolve_parent_constants_mro(
            package_dir, return_module=True
        )
        model_context = u.Infra.contextual_runtime_alias_sources(
            project_root=project, file_path=package_dir / "_utilities" / "brand.py"
        )
        base_context = u.Infra.contextual_runtime_alias_sources(
            project_root=project, file_path=package_dir / "base.py"
        )

        tm.that(parent_packages, contains="flext_cli")
        tm.that(model_context["u"], eq=frozenset({"flext_cli"}))
        tm.that(base_context["s"], eq=frozenset({"flext_cli"}))

    def test_contextual_runtime_sources_resolve_transitive_parent_facades(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        grandparent_pkg = workspace / "demo-grandparent" / "src" / "demo_grandparent"
        parent_pkg = workspace / "demo-parent" / "src" / "demo_parent"
        child_project = workspace / "demo-child"
        child_pkg = child_project / "src" / "demo_child"
        for project_name, package_dir in (
            ("demo-grandparent", grandparent_pkg),
            ("demo-parent", parent_pkg),
            ("demo-child", child_pkg),
        ):
            package_dir.mkdir(parents=True)
            project = workspace / project_name
            _ = (project / "pyproject.toml").write_text(
                f"[project]\nname='{project_name}'\n", encoding="utf-8"
            )
            _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
            _ = (package_dir / "__init__.py").write_text(
                "from .constants import c\n", encoding="utf-8"
            )
        _ = (grandparent_pkg / "constants.py").write_text(
            "from __future__ import annotations\n"
            "from flext_core import c\n\n"
            "class DemoGrandparentConstants(c):\n"
            "    pass\n\n"
            "c = DemoGrandparentConstants\n",
            encoding="utf-8",
        )
        _ = (parent_pkg / "constants.py").write_text(
            "from __future__ import annotations\n"
            "from demo_grandparent import c\n\n"
            "class DemoParentConstants(c):\n"
            "    pass\n\n"
            "c = DemoParentConstants\n",
            encoding="utf-8",
        )
        _ = (child_pkg / "constants.py").write_text(
            "from __future__ import annotations\n"
            "from demo_parent import c\n\n"
            "class DemoChildConstants(c):\n"
            "    pass\n\n"
            "c = DemoChildConstants\n",
            encoding="utf-8",
        )

        base_context = u.Infra.contextual_runtime_alias_sources(
            project_root=child_project, file_path=child_pkg / "base.py"
        )

        tm.that(base_context["s"], contains="demo_parent")
        tm.that(base_context["s"], contains="demo_grandparent")
