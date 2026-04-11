"""Tests for lazy-init package discovery and planning behavior."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from tests import c, m, t, u


class TestsFlextInfraLazyInitHelpers:
    """Behavior tests for the public lazy-init plan contract."""

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path]:
        return u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )

    @staticmethod
    def _plan(
        workspace_root: Path,
        package_root: Path,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> m.Infra.LazyInitPlan:
        rope_root = u.Infra.rope_workspace_root(workspace_root)
        with u.Infra.open_project(rope_root) as project:
            return u.Infra(workspace_root).build_lazy_init_plan(
                package_root,
                project=project,
                dir_exports=dir_exports,
            )

    def test_discover_package_from_standard_roots(self) -> None:
        assert (
            u.Infra.discover_package_from_file(
                Path("/workspace/src/test_pkg/__init__.py"),
            )
            == "test_pkg"
        )
        assert (
            u.Infra.discover_package_from_file(
                Path("/workspace/tests/unit/__init__.py"),
            )
            == "tests.unit"
        )
        assert (
            u.Infra.discover_package_from_file(
                Path("/workspace/examples/tests/__init__.py"),
            )
            == "examples.tests"
        )

    def test_root_plan_uses_real_classes_and_aliases(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )

        plan = self._plan(
            workspace_root,
            package_root,
            {},
        )

        assert plan.action == "write"
        assert plan.lazy_map["FlextDemoModels"] == (
            "flext_demo.models",
            "FlextDemoModels",
        )
        assert plan.lazy_map["m"] == ("flext_demo.models", "m")

    def test_private_modules_do_not_export_from_root(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "_internal.py").write_text(
            "from __future__ import annotations\n\nclass FlextDemoInternal:\n    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        plan = self._plan(
            workspace_root,
            package_root,
            {},
        )

        assert "FlextDemoInternal" not in plan.lazy_map

    def test_explicit_all_exports_local_alias_without_leaking_assignments(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "api.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemo:\n"
            "    pass\n\n"
            "demo = FlextDemo()\n"
            "hidden = FlextDemo()\n\n"
            '__all__ = ["FlextDemo", "demo"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        plan = self._plan(
            workspace_root,
            package_root,
            {},
        )

        assert plan.lazy_map["FlextDemo"] == ("flext_demo.api", "FlextDemo")
        assert plan.lazy_map["demo"] == ("flext_demo.api", "demo")
        assert "hidden" not in plan.lazy_map

    def test_child_exports_bubble_real_symbols_only(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        child_dir = package_root / "services"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        plan = self._plan(
            workspace_root,
            package_root,
            {
                str(child_dir): {
                    "FlextDemoService": (
                        "flext_demo.services.service",
                        "FlextDemoService",
                    ),
                    "main": ("flext_demo.services.cli", "main"),
                    "BLUE": ("flext_demo.services.colors", "BLUE"),
                    "m": ("flext_demo.services.models", "m"),
                },
            },
        )

        assert plan.lazy_map["FlextDemoService"] == (
            "flext_demo.services.service",
            "FlextDemoService",
        )
        assert "main" not in plan.lazy_map
        assert plan.lazy_map["BLUE"] == ("flext_demo.services.colors", "BLUE")
        assert "m" not in plan.lazy_map

    def test_tests_root_aliases_follow_export_hierarchy(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__ = ["d"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoConstants:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        tests_support_root = (
            tmp_path / "flext-tests" / c.Infra.DEFAULT_SRC_DIR / "flext_tests"
        )
        tests_support_root.mkdir(parents=True)
        tests_support_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__ = ["d", "td"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        tests_support_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestsConstants:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        tests_root = workspace_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        tests_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_demo.constants import FlextDemoConstants\n"
            "from flext_tests.constants import FlextTestsConstants\n\n"
            "class TestsFlextDemoConstants("
            "FlextDemoConstants, FlextTestsConstants"
            "):\n"
            "    pass\n\n"
            "c = TestsFlextDemoConstants\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        child_dir = tests_root / "unit"
        child_dir.mkdir()

        plan = self._plan(
            workspace_root,
            tests_root,
            {
                str(child_dir): {
                    "Child": ("tests.unit.child", "Child"),
                    "td": ("flext_demo", "td"),
                },
            },
        )

        assert plan.lazy_map["d"] == ("flext_demo", "d")
        assert plan.lazy_map["td"] == ("flext_tests", "td")
        assert plan.lazy_map["Child"] == ("tests.unit.child", "Child")

    def test_root_aliases_follow_transitive_parent_exports_from_source(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-meltano",
            package_name="flext_meltano",
        )
        core_root = tmp_path / "flext-core" / c.Infra.DEFAULT_SRC_DIR / "flext_core"
        core_root.mkdir(parents=True)
        core_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        core_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            core_root / "result.py",
            class_name="FlextCoreResult",
            alias="r",
            docstring="Result.",
        )
        core_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextCoreConstants:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cli_root = tmp_path / "flext-cli" / c.Infra.DEFAULT_SRC_DIR / "flext_cli"
        cli_root.mkdir(parents=True)
        cli_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-cli"\nversion = "0.1.0"\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__ = ["c"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_core.constants import FlextCoreConstants\n\n"
            "class FlextCliConstants(FlextCoreConstants):\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import c\n\n"
            "class FlextMeltanoConstants(c):\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        plan = self._plan(
            workspace_root,
            package_root,
            {},
        )

        assert plan.lazy_map["r"] == ("flext_cli", "r")

    def test_root_aliases_use_ast_fallback_when_rope_class_scan_is_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            FlextInfraUtilitiesRopeAnalysis,
            "get_class_info",
            staticmethod(lambda *_args, **_kwargs: []),
        )
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-meltano",
            package_name="flext_meltano",
        )
        core_root = tmp_path / "flext-core" / c.Infra.DEFAULT_SRC_DIR / "flext_core"
        core_root.mkdir(parents=True)
        core_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        core_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            core_root / "result.py",
            class_name="FlextCoreResult",
            alias="r",
            docstring="Result.",
        )
        core_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextCoreConstants:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cli_root = tmp_path / "flext-cli" / c.Infra.DEFAULT_SRC_DIR / "flext_cli"
        cli_root.mkdir(parents=True)
        cli_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-cli"\nversion = "0.1.0"\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__ = ["c"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_core.constants import FlextCoreConstants\n\n"
            "class FlextCliConstants(FlextCoreConstants):\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import c\n\n"
            "class FlextMeltanoConstants(c):\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        plan = self._plan(
            workspace_root,
            package_root,
            {},
        )

        assert plan.lazy_map["r"] == ("flext_cli", "r")

    def test_duplicate_public_export_raises(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "alpha.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (package_root / "beta.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        with pytest.raises(ValueError, match="export collision"):
            self._plan(workspace_root, package_root, {})
