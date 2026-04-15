"""Tests for public lazy-init generation behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, t, u


class TestProcessDirectory:
    """Test public lazy-init generation scenarios."""

    def test_generates_init_from_sibling_files(self, tmp_path: Path) -> None:
        """generate_inits() generates __init__.py from sibling exports."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert '".models": (' in init_content
        assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in init_content
        assert (
            f'"{c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS}"' in init_content
        )

    def test_check_only_does_not_write(self, tmp_path: Path) -> None:
        """check_only mode reports without creating __init__.py."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )
        original_init = (package_root / "__init__.py").read_text(encoding="utf-8")

        result = u.Infra.Tests.run_lazy_init(workspace_root, check_only=True)

        assert result == 0
        assert (package_root / "__init__.py").read_text(
            encoding="utf-8"
        ) == original_init

    def test_skips_directory_without_package(self, tmp_path: Path) -> None:
        """Directories outside canonical package roots are skipped."""
        random_dir = tmp_path / "random"
        random_dir.mkdir()
        (random_dir / "models.py").write_text("class Model: pass\n")

        result = u.Infra.Tests.run_lazy_init(tmp_path)

        assert result == 0
        assert not (random_dir / "__init__.py").exists()

    def test_does_not_generate_src_wrapper_init(self, tmp_path: Path) -> None:
        """The ``src/`` layout directory is not an importable package surface."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )
        src_init = workspace_root / c.Infra.DEFAULT_SRC_DIR / c.Infra.INIT_PY

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        assert not src_init.exists()

    def test_removes_stale_generated_non_importable_init(self, tmp_path: Path) -> None:
        """Existing generated wrapper inits are removed when no package is importable."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )
        src_init = workspace_root / c.Infra.DEFAULT_SRC_DIR / c.Infra.INIT_PY
        src_init.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            "from __future__ import annotations\n\n"
            "from _models.base import FlextDemoModels\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        assert not src_init.exists()

    def test_root_local_aliases_replace_parent_aliases(
        self,
        tmp_path: Path,
    ) -> None:
        """Root generation keeps aliases redefined by local facade modules."""
        parent_project = tmp_path / "flext-parent"
        parent_package = parent_project / c.Infra.DEFAULT_SRC_DIR / "flext_parent"
        child_project = tmp_path / "flext-child"
        child_package = child_project / c.Infra.DEFAULT_SRC_DIR / "flext_child"
        for project, project_name in (
            (parent_project, "flext-parent"),
            (child_project, "flext-child"),
        ):
            project.mkdir(parents=True)
            (project / c.Infra.PYPROJECT_FILENAME).write_text(
                f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n',
                encoding=c.Infra.ENCODING_DEFAULT,
            )
        parent_package.mkdir(parents=True)
        child_package.mkdir(parents=True)
        (parent_package / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (child_package / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        for module_name, alias, suffix in (
            ("models.py", "m", "Models"),
            ("typings.py", "t", "Types"),
            ("utilities.py", "u", "Utilities"),
        ):
            parent_class = f"FlextParent{suffix}"
            child_class = f"FlextChild{suffix}"
            (parent_package / module_name).write_text(
                "from __future__ import annotations\n\n"
                f"class {parent_class}:\n"
                "    pass\n\n"
                f"{alias} = {parent_class}\n"
                f'__all__: list[str] = ["{parent_class}", "{alias}"]\n',
                encoding=c.Infra.ENCODING_DEFAULT,
            )
            (child_package / module_name).write_text(
                "from __future__ import annotations\n\n"
                f"from flext_parent.{Path(module_name).stem} import {parent_class}, {alias}\n\n"
                f"class {child_class}({parent_class}):\n"
                "    pass\n\n"
                f"{alias} = {child_class}\n"
                f'__all__: list[str] = ["{child_class}", "{alias}"]\n',
                encoding=c.Infra.ENCODING_DEFAULT,
            )

        result = u.Infra.Tests.run_lazy_init(tmp_path)

        assert result == 0
        init_content = (child_package / c.Infra.INIT_PY).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        for module_key, alias, class_name in (
            ('".models": (', "m", "FlextChildModels"),
            ('".typings": (', "t", "FlextChildTypes"),
            ('".utilities": (', "u", "FlextChildUtilities"),
        ):
            section = init_content.split(module_key, maxsplit=1)[1].split(
                "),",
                maxsplit=1,
            )[0]
            assert f'"{alias}"' in section
            assert f'"{class_name}"' in section
        assert "flext_parent.models" not in init_content
        assert "flext_parent.typings" not in init_content
        assert "flext_parent.utilities" not in init_content

    def test_leaf_package_uses_direct_lazy_map(self, tmp_path: Path) -> None:
        """Packages without child packages do not emit merge-only arguments."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        mcp_dir = package_root / "mcp"
        mcp_dir.mkdir(parents=True)
        (mcp_dir / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (mcp_dir / "tools.py").write_text(
            "from __future__ import annotations\n\n"
            "def quality_tool() -> str:\n"
            '    return "ok"\n\n'
            '__all__: list[str] = ["quality_tool"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (mcp_dir / c.Infra.INIT_PY).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        assert "_LAZY_IMPORTS = build_lazy_import_map(" in init_content
        assert "merge_lazy_imports" not in init_content
        assert "exclude_names=" not in init_content
        assert "module_name=__name__" not in init_content

    def test_includes_child_exports(self, tmp_path: Path) -> None:
        """Parent package includes exports discovered from child packages."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        sub_dir = package_root / "sub"
        sub_dir.mkdir(parents=True)
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            sub_dir / "service.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_ALIAS,
            docstring="Service.",
        )
        (sub_dir / "registry.py").write_text(
            "from __future__ import annotations\n\n"
            "ALL_STREAMS = {}\n\n"
            '__all__: list[str] = ["ALL_STREAMS"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        parent_init = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in parent_init
        assert (
            c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_CLASS in parent_init
        )
        assert "ALL_STREAMS" in parent_init

    @pytest.mark.parametrize(
        ("surface", "family_dir", "file_name", "class_name"),
        [
            ("tests", "_models", "mixins.py", "TestsFlextDemoModelsMixins"),
            (
                "examples",
                "_utilities",
                "helpers.py",
                "ExamplesFlextDemoUtilitiesHelpers",
            ),
            ("scripts", "_protocols", "base.py", "ScriptsFlextDemoProtocolsBase"),
        ],
    )
    def test_surface_root_includes_private_family_exports(
        self,
        tmp_path: Path,
        surface: str,
        family_dir: str,
        file_name: str,
        class_name: str,
    ) -> None:
        """Governed surface roots merge canonical exports from private family packages."""
        workspace_root, _package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        surface_dir = workspace_root / surface
        family_root = surface_dir / family_dir
        family_root.mkdir(parents=True)
        (surface_dir / c.Infra.INIT_PY).write_text("")
        (family_root / c.Infra.INIT_PY).write_text("")
        (family_root / file_name).write_text(f"class {class_name}:\n    pass\n")

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (surface_dir / c.Infra.INIT_PY).read_text(
            encoding="utf-8",
        )
        assert class_name in init_content

    def test_generates_examples_tests_module_paths(self, tmp_path: Path) -> None:
        """Test nested examples/tests packages keep the examples prefix."""
        workspace_root, _package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            package_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.ROOT_PACKAGE_NAME,
        )
        examples_tests_dir = workspace_root / "examples" / "tests"
        examples_tests_dir.mkdir(parents=True)
        u.Infra.Tests.write_lazy_init_namespace_module(
            examples_tests_dir / "utilities.py",
            class_name=(
                c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_CLASS
            ),
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_ALIAS,
            docstring="Example tests.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (examples_tests_dir / "__init__.py").read_text(encoding="utf-8")
        assert (
            c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_CLASS
            in init_content
        )
        assert (
            f'"{c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_ALIAS}"'
            in init_content
        )

    def test_generates_tests_root_with_static_analysis_hints(
        self,
        tmp_path: Path,
    ) -> None:
        """Test tests/ wrappers get the same static hints as src/ wrappers."""
        workspace_root, _package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            package_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.ROOT_PACKAGE_NAME,
        )
        tests_dir = workspace_root / "tests"
        tests_dir.mkdir(parents=True)
        u.Infra.Tests.write_lazy_init_namespace_module(
            tests_dir / "typings.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_ALIAS,
            docstring="Typings.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (tests_dir / "__init__.py").read_text(encoding="utf-8")
        assert "if _t.TYPE_CHECKING:" in init_content
        assert "__all__: list[str] = [" in init_content
        assert c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_CLASS in init_content
        assert (
            f'"{c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_ALIAS}"'
            in init_content
        )

    def test_subpackage_keeps_module_entries_without_symbol_exports(
        self, tmp_path: Path
    ) -> None:
        """Generated subpackages keep importable modules without leaking internals."""
        workspace_root, _package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            package_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.ROOT_PACKAGE_NAME,
        )
        tests_dir = workspace_root / "tests"
        unit_dir = tests_dir / "unit"
        unit_dir.mkdir(parents=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (unit_dir / "__init__.py").write_text("", encoding="utf-8")
        u.Infra.Tests.write_lazy_init_namespace_module(
            unit_dir / "typings.py",
            class_name="TestsFlextDemoUnitTypes",
            alias="t",
            docstring="Typings.",
        )
        (unit_dir / "test_api.py").write_text(
            "def test_smoke() -> None:\n    pass\n",
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (unit_dir / "__init__.py").read_text(encoding="utf-8")
        assert "TestsFlextDemoUnitTypes" in init_content
        assert '".test_api": ("test_api",)' in init_content
        assert "test_smoke" not in init_content

    def test_generates_fixture_package_and_reexports_fixture_functions(
        self,
        tmp_path: Path,
    ) -> None:
        """Fixture packages are generated automatically and merged into the root."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        fixture_dir = package_root / "_fixtures"
        fixture_dir.mkdir()
        (fixture_dir / "settings.py").write_text(
            "from __future__ import annotations\n\n"
            "def reset_settings() -> None:\n"
            "    return None\n\n"
            "def settings() -> None:\n"
            "    return None\n\n"
            "def settings_factory() -> None:\n"
            "    return None\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        fixture_init = (fixture_dir / "__init__.py").read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        root_init = (package_root / "__init__.py").read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        assert '"reset_settings"' in fixture_init
        assert '"settings"' in fixture_init
        assert '"settings_factory"' in fixture_init
        assert '"reset_settings"' in root_init
        assert '"settings"' in root_init
        assert '"settings_factory"' in root_init

    def test_handles_version_file(self, tmp_path: Path) -> None:
        """Version exports are preserved in generated public wrappers."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )
        u.Infra.Tests.write_lazy_init_version_module(package_root)

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert (
            "from "
            f"{c.Infra.Tests.Fixtures.Codegen.LazyInit.PACKAGE_NAME}.__version__ "
            "import *"
        ) in content
        assert '".__version__": (' in content
        assert '"__version__"' in content
        assert '"__version_info__"' in content

    def test_root_settings_without_explicit_all_still_exports_class(
        self,
        tmp_path: Path,
    ) -> None:
        """Root settings.py without __all__ still exports its facade settings class."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        (package_root / "settings.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoSettings:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (package_root / "__init__.py").read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        assert '".settings": (' in init_content
        assert '"FlextDemoSettings"' in init_content

    def test_private_family_base_without_all_keeps_class_export(
        self,
        tmp_path: Path,
    ) -> None:
        """Private family base.py without __all__ still exports class from _typings."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        typings_dir = package_root / "_typings"
        typings_dir.mkdir(parents=True)
        (typings_dir / "base.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoBaseTypesMixin:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        typings_init = (typings_dir / "__init__.py").read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        assert '".base": (' in typings_init
        assert '"FlextDemoBaseTypesMixin"' in typings_init

    def test_root_package_includes_settings_class_without_explicit_all(
        self,
        tmp_path: Path,
    ) -> None:
        """Root generation keeps concrete settings classes even without ``__all__``."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )
        (package_root / "settings.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoSettings:\n"
            "    pass\n",
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert '".settings": ("FlextDemoSettings",)' in content
        assert '    "FlextDemoSettings",' in content

    def test_internal_family_package_keeps_class_exports_without_explicit_all(
        self,
        tmp_path: Path,
    ) -> None:
        """Private family packages must not require ``__all__`` on member modules."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        constants_dir = package_root / "_constants"
        constants_dir.mkdir(parents=True)
        (constants_dir / "__init__.py").write_text("", encoding="utf-8")
        (constants_dir / "base.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoConstantsBase:\n"
            "    pass\n",
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        content = (constants_dir / "__init__.py").read_text(encoding="utf-8")
        assert '".base": ("FlextDemoConstantsBase",)' in content
        assert "publish_all=False" in content


__all__: t.StrSequence = []
