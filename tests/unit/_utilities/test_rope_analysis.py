"""Tests for Rope semantic analysis helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import u
from flext_infra.detectors.facade_scanner import FlextInfraScanner


class TestsFlextInfraRopeAnalysis:
    """Behavior contract for Rope-backed semantic analysis."""

    def test_assignment_strings_resolve_local_registry_with_rope(
        self, tmp_path: Path
    ) -> None:
        """Read declarative module registries from Rope-owned assignments."""
        project = tmp_path / "demo-project"
        package_dir = project / "tests"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        registry_path = package_dir / "conftest.py"
        _ = registry_path.write_text(
            "pytest_plugins: tuple[str, ...] = (\n"
            '    "tests.unit.fixtures",\n'
            '    "tests.unit.fixtures_git",\n'
            ")\n",
            encoding="utf-8",
        )
        dynamic_registry_path = package_dir / "dynamic_registry.py"
        _ = dynamic_registry_path.write_text(
            "pytest_plugins = build_plugins()\n", encoding="utf-8"
        )
        triple_registry_path = package_dir / "triple_registry.py"
        _ = triple_registry_path.write_text(
            'pytest_plugins = ("""tests.unit.fixtures""",)\n', encoding="utf-8"
        )
        invalid_registry_path = package_dir / "invalid_registry.py"
        _ = invalid_registry_path.write_text(
            'pytest_plugins = ("tests.unit.bad-name",)\n', encoding="utf-8"
        )
        scalar_registry_path = package_dir / "scalar_registry.py"
        _ = scalar_registry_path.write_text(
            'pytest_plugins = ("tests.unit.fixtures")\n', encoding="utf-8"
        )
        list_registry_path = package_dir / "list_registry.py"
        _ = list_registry_path.write_text(
            'pytest_plugins = ["tests.unit.fixtures"]\n', encoding="utf-8"
        )
        string_registry_path = package_dir / "string_registry.py"
        _ = string_registry_path.write_text(
            'pytest_plugins = "tests.unit.fixtures"\n', encoding="utf-8"
        )

        with u.Infra.open_project(project) as rope_project:
            # NOTE (multi-agent): preserve Rope's optional boundary while proving
            # every fixture path exists before exercising registry semantics.
            resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, registry_path)
            )
            registry = u.Infra.get_module_registry_imports(
                rope_project, resource, "pytest_plugins"
            )
            missing = u.Infra.get_module_registry_imports(
                rope_project, resource, "missing_registry"
            )
            dynamic_resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, dynamic_registry_path)
            )
            with pytest.raises(
                ValueError,
                match=(
                    "Declarative assignment must be a plain string, literal list, "
                    "or tuple"
                ),
            ):
                _ = u.Infra.get_module_registry_imports(
                    rope_project, dynamic_resource, "pytest_plugins"
                )
            triple_resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, triple_registry_path)
            )
            with pytest.raises(
                ValueError, match="Declarative assignment requires plain string"
            ):
                _ = u.Infra.get_module_registry_imports(
                    rope_project, triple_resource, "pytest_plugins"
                )
            invalid_resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, invalid_registry_path)
            )
            with pytest.raises(
                ValueError, match="Declarative assignment requires dotted import"
            ):
                _ = u.Infra.get_module_registry_imports(
                    rope_project, invalid_resource, "pytest_plugins"
                )
            scalar_resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, scalar_registry_path)
            )
            with pytest.raises(
                ValueError, match="Declarative assignment requires a tuple comma"
            ):
                _ = u.Infra.get_module_registry_imports(
                    rope_project, scalar_resource, "pytest_plugins"
                )
            list_resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, list_registry_path)
            )
            list_registry = u.Infra.get_module_registry_imports(
                rope_project, list_resource, "pytest_plugins"
            )
            string_resource = tm.not_none(
                u.Infra.get_resource_from_path(rope_project, string_registry_path)
            )
            string_registry = u.Infra.get_module_registry_imports(
                rope_project, string_resource, "pytest_plugins"
            )

        tm.that(registry, eq=("tests.unit.fixtures", "tests.unit.fixtures_git"))
        tm.that(missing, eq=())
        tm.that(list_registry, eq=("tests.unit.fixtures",))
        tm.that(string_registry, eq=("tests.unit.fixtures",))

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
