"""Tests for Rope semantic analysis helpers."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import u
from flext_infra.detectors.facade_scanner import FlextInfraScanner


class TestsFlextInfraRopeAnalysis:
    """Behavior contract for Rope-backed semantic analysis."""

    def test_facade_scanner_reads_facade_with_imported_superclass(
        self,
        tmp_path: Path,
    ) -> None:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n",
            encoding="utf-8",
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
                project_root=project,
                rope_project=rope_project,
            )

        constants_status = next(status for status in statuses if status.family == "c")
        tm.that(constants_status.exists, eq=True)
        tm.that(constants_status.class_name, eq="DemoProjectConstants")
        model_context = u.Infra.contextual_runtime_alias_sources(
            project_root=project,
            file_path=package_dir / "_models" / "brand.py",
        )
        settings_context = u.Infra.contextual_runtime_alias_sources(
            project_root=project,
            file_path=package_dir / "settings.py",
        )
        tm.that(model_context["m"], eq=frozenset({"flext_cli"}))
        tm.that(settings_context["m"], eq=frozenset({"flext_cli"}))
