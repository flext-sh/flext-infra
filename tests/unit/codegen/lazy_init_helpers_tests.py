"""Behavior tests for public lazy-init generation."""

from __future__ import annotations

from pathlib import Path

from tests import c, u


class TestsFlextInfraLazyInitHelpers:
    """Validate lazy-init through the public service surface only."""

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path]:
        workspace: tuple[Path, Path] = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        return workspace

    @staticmethod
    def _generated_init(package_root: Path) -> str:
        return package_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )

    def test_discover_package_from_standard_roots(self) -> None:
        assert (
            u.Infra.package_name(
                Path("/workspace/src/test_pkg/__init__.py"),
            )
            == "test_pkg"
        )
        assert (
            u.Infra.package_name(
                Path("/workspace/tests/unit/__init__.py"),
            )
            == "tests.unit"
        )
        assert (
            u.Infra.package_name(
                Path("/workspace/examples/tests/__init__.py"),
            )
            == "examples.tests"
        )

    def test_root_generation_uses_real_classes_and_aliases(
        self, tmp_path: Path
    ) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = self._generated_init(package_root)

        assert '"FlextDemoModels"' in init_content
        assert '"m"' in init_content
        assert "_LAZY_IMPORTS" in init_content

    def test_private_modules_do_not_export_from_root(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "_internal.py").write_text(
            "from __future__ import annotations\n\nclass FlextDemoInternal:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        assert "FlextDemoInternal" not in self._generated_init(package_root)

    def test_explicit_all_exports_keep_public_aliases_only(
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
            '__all__: list[str] = ["FlextDemo", "demo"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = self._generated_init(package_root)

        assert '"FlextDemo"' in init_content
        assert '"demo"' in init_content
        assert "hidden" not in init_content

    def test_child_exports_bubble_public_symbols_only(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        child_dir = package_root / "services"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (child_dir / "service.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoService:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoService"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child_dir / "colors.py").write_text(
            'from __future__ import annotations\n\nBLUE = "blue"\n\n__all__: list[str] = ["BLUE"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (child_dir / "cli.py").write_text(
            'from __future__ import annotations\n\ndef main() -> str:\n    return "ok"\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            child_dir / "models.py",
            class_name="FlextDemoServicesModels",
            alias="m",
            docstring="Models.",
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = self._generated_init(package_root)

        assert "FlextDemoService" in init_content
        assert '"BLUE"' in init_content
        assert '"main"' not in init_content
        assert '"m": ("flext_demo.services.models", "m")' not in init_content

    def test_tests_root_aliases_follow_export_hierarchy(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: list[str] = ["d"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoConstants:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_support_root = (
            tmp_path / "flext-tests" / c.Infra.DEFAULT_SRC_DIR / "flext_tests"
        )
        tests_support_root.mkdir(parents=True)
        tests_support_root.parent.parent.joinpath(
            c.Infra.PYPROJECT_FILENAME
        ).write_text(
            '[project]\nname = "flext-tests"\nversion = "0.1.0"\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_support_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: list[str] = ["d", "td"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_support_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestsConstants:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextTestsConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_root = workspace_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        tests_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_demo import FlextDemoConstants\n"
            "from flext_tests import FlextTestsConstants\n\n"
            "class TestsFlextDemoConstants("
            "FlextDemoConstants, FlextTestsConstants"
            "):\n"
            "    pass\n\n"
            "c = TestsFlextDemoConstants\n\n"
            '__all__: list[str] = ["TestsFlextDemoConstants", "c"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        child_dir = tests_root / "unit"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (child_dir / "child.py").write_text(
            "from __future__ import annotations\n\n"
            "class Child:\n"
            "    pass\n\n"
            '__all__: list[str] = ["Child"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = tests_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert '"d"' in init_content
        assert '"td"' in init_content

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
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        core_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
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
            "    pass\n\n"
            '__all__: list[str] = ["FlextCoreConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        cli_root = tmp_path / "flext-cli" / c.Infra.DEFAULT_SRC_DIR / "flext_cli"
        cli_root.mkdir(parents=True)
        cli_root.parent.parent.joinpath(c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-cli"\nversion = "0.1.0"\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: list[str] = ["c"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        cli_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import FlextCoreConstants\n\n"
            "class FlextCliConstants(FlextCoreConstants):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextCliConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import c\n\n"
            "class FlextMeltanoConstants(c):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextMeltanoConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = self._generated_init(package_root)

        assert '"r"' in init_content

    def test_nested_tests_namespace_exports_local_symbols_only(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        package_root.joinpath(c.Infra.RESULT_PY).write_text(
            "from __future__ import annotations\n\nclass FlextDemoResult:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_unit_root = workspace_root / c.Infra.DIR_TESTS / "unit"
        tests_unit_root.mkdir(parents=True)
        tests_unit_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        tests_unit_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoUnitConstants:\n"
            "    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tests_unit_root.joinpath(c.Infra.MODELS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoUnitModels:\n"
            "    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = tests_unit_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert "TestsFlextDemoUnitConstants" in init_content
        assert "TestsFlextDemoUnitModels" in init_content
        assert "publish_all=False" in init_content

    def test_root_exports_symbols_from_deep_descendant_packages(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        deep_dir = package_root / "services" / "http"
        deep_dir.mkdir(parents=True)
        (package_root / "services" / c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        deep_dir.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        deep_dir.joinpath("transport.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoHttpTransport:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoHttpTransport"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 0
        init_content = self._generated_init(package_root)

        assert "FlextDemoHttpTransport" in init_content

    def test_duplicate_public_export_returns_error(self, tmp_path: Path) -> None:
        workspace_root, package_root = self._workspace(tmp_path)
        (package_root / "alpha.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (package_root / "beta.py").write_text(
            "from __future__ import annotations\n\nclass Shared:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        assert u.Infra.Tests.run_lazy_init(workspace_root) == 1
        assert not self._generated_init(package_root).startswith(c.Infra.AUTOGEN_HEADER)
