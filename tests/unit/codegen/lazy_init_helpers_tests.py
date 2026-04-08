"""Tests for lazy_init helper functions: package inference, docstrings, exports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm
from tests import u


def _extract_exports(source: str) -> tuple[bool, Sequence[str]]:
    for name, value_str in u.Infra.get_module_level_assignments(source):
        if name == "__all__":
            return True, tuple(re.findall(r'["\']([^"\']+)["\']', value_str))
    return False, ()


class TestInferPackage:
    """Test infer_package function."""

    def test_src_path(self) -> None:
        """Test inference from src/ path."""
        path = Path("/workspace/src/test_pkg/__init__.py")
        tm.that(u.Infra.discover_package_from_file(path), eq="test_pkg")

    def test_deeply_nested_src_path(self) -> None:
        """Test inference from deeply nested src/ path."""
        path = Path("/workspace/src/a/b/c/d/__init__.py")
        tm.that(u.Infra.discover_package_from_file(path), eq="a.b.c.d")

    def test_tests_path(self) -> None:
        """Test inference from tests/ path."""
        path = Path("/workspace/tests/unit/__init__.py")
        tm.that(u.Infra.discover_package_from_file(path), eq="tests.unit")

    def test_examples_nested_tests_path(self) -> None:
        """Test inference preserves examples package before nested tests."""
        path = Path("/workspace/examples/tests/__init__.py")
        tm.that(
            u.Infra.discover_package_from_file(path),
            eq="examples.tests",
        )

    def test_docs_tools_path(self) -> None:
        """Test inference preserves docs namespace packages."""
        path = Path("/workspace/docs/architecture/tools/__init__.py")
        tm.that(
            u.Infra.discover_package_from_file(path),
            eq="docs.architecture.tools",
        )

    def test_without_src_directory(self) -> None:
        """Test when path doesn't contain /src/."""
        path = Path("/workspace/lib/test/__init__.py")
        tm.that(u.Infra.discover_package_from_file(path), eq="")


class TestReadExistingDocstring:
    """Test public docstring discovery utility."""

    def test_with_docstring(self, tmp_path: Path) -> None:
        """Test extracting docstring from existing __init__.py."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text('"""Package docstring."""\nx = 1\n')
        result = u.Infra.read_existing_docstring(init_file)
        tm.that(result, contains="Package docstring")

    def test_without_docstring(self, tmp_path: Path) -> None:
        """Test returns empty when no docstring exists."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text("x = 1\ny = 2\n")
        result = u.Infra.read_existing_docstring(init_file)
        tm.that(result, eq="")

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test returns empty when file doesn't exist."""
        init_file = tmp_path / "__init__.py"
        result = u.Infra.read_existing_docstring(init_file)
        tm.that(result, eq="")

    def test_with_syntax_error(self, tmp_path: Path) -> None:
        """Test returns empty on syntax error."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text("invalid syntax ][")
        result = u.Infra.read_existing_docstring(init_file)
        tm.that(result, eq="")

    def test_with_single_quotes(self, tmp_path: Path) -> None:
        """Test preserves single-quote docstring style."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text("'''Module docstring.'''\nx = 1\n")
        result = u.Infra.read_existing_docstring(init_file)
        tm.that(result, contains="Module docstring")


class TestBuildSiblingExportIndex:
    """Test public sibling export discovery utility."""

    def test_with_all_exports(self, tmp_path: Path) -> None:
        """Test scanning sibling files with __all__."""
        (tmp_path / "public_api.py").write_text(
            '"""Models."""\n\n__all__ = ["Foo", "Bar"]\n\nclass Foo: pass\nclass Bar: pass\n',
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="Foo")
        tm.that(index, contains="Bar")
        tm.that(index["Foo"], eq=("test_pkg.public_api", "Foo"))

    def test_without_all_falls_back_to_ast(self, tmp_path: Path) -> None:
        """Test scanning sibling files without __all__ uses AST."""
        (tmp_path / "public_api.py").write_text(
            "class PublicService:\n    pass\n\ndef public_func():\n    pass\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="PublicService")
        tm.that(index, contains="public_func")

    def test_skips_init_and_main(self, tmp_path: Path) -> None:
        """Test that __init__.py and __main__.py are skipped."""
        (tmp_path / "__init__.py").write_text('__all__ = ["Init"]\n')
        (tmp_path / "__main__.py").write_text("def main(): pass\n")
        (tmp_path / "public_api.py").write_text(
            '__all__ = ["Model"]\nclass Model: pass\n',
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, excludes="Init")
        tm.that(index, excludes="main")
        tm.that(index, contains="Model")

    def test_skips_private_files(self, tmp_path: Path) -> None:
        """Test that _private.py files are skipped."""
        (tmp_path / "_internal.py").write_text("class Internal: pass\n")
        (tmp_path / "public.py").write_text("class Public: pass\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, excludes="Internal")
        tm.that(index, contains="Public")

    def test_skips_private_files_inside_nested_packages(self, tmp_path: Path) -> None:
        """Private underscore modules must stay hidden even in nested packages."""
        (tmp_path / "_hidden_manager.py").write_text(
            "class HiddenManager:\n    pass\n",
        )
        (tmp_path / "managers.py").write_text("class PublicManager:\n    pass\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg.services")
        tm.that(index, excludes="HiddenManager")
        tm.that(index, excludes="_hidden_manager")
        tm.that(index, contains="PublicManager")

    def test_skips_version_file(self, tmp_path: Path) -> None:
        """Test that __version__.py is skipped (handled separately)."""
        (tmp_path / "__version__.py").write_text('__version__ = "1.0.0"\n')
        (tmp_path / "public_api.py").write_text(
            '__all__ = ["Model"]\nclass Model: pass\n',
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, excludes="__version__")
        tm.that(index, contains="Model")

    def test_handles_syntax_error_gracefully(self, tmp_path: Path) -> None:
        """Test that syntax errors in sibling files are skipped."""
        (tmp_path / "broken.py").write_text("def broken(][: pass\n")
        (tmp_path / "good.py").write_text(
            '__all__ = ["Good"]\nclass Good: pass\n',
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="Good")

    def test_preserves_docs_module_path(self, tmp_path: Path) -> None:
        """Test docs package exports keep their namespace-qualified module path."""
        tools_dir = tmp_path / "docs" / "architecture" / "tools"
        tools_dir.mkdir(parents=True)
        (tools_dir / "validate_docs.py").write_text(
            '__all__ = ["ArchitectureValidator"]\nclass ArchitectureValidator: pass\n',
        )
        index = u.Infra.build_sibling_export_index(
            tools_dir,
            "docs.architecture.tools",
        )
        tm.that(
            index["ArchitectureValidator"],
            eq=("docs.architecture.tools.validate_docs", "ArchitectureValidator"),
        )

    def test_duplicate_public_export_raises(self, tmp_path: Path) -> None:
        """Conflicting public exports must abort lazy-init generation."""
        (tmp_path / "alpha.py").write_text("def run() -> None:\n    pass\n")
        (tmp_path / "beta.py").write_text("def run() -> None:\n    pass\n")
        with pytest.raises(ValueError, match="export collision"):
            u.Infra.build_sibling_export_index(tmp_path, "test_pkg")

    def test_main_is_never_indexed_as_public_export(self, tmp_path: Path) -> None:
        """Package scanners must exclude main() from non-entrypoint modules."""
        (tmp_path / "audit.py").write_text(
            '__all__ = ["main", "AuditRunner"]\n\n'
            "def main() -> None:\n    pass\n\n"
            "class AuditRunner:\n    pass\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, excludes="main")
        tm.that(index, contains="AuditRunner")

    def test_main_is_indexed_from_cli_module(self, tmp_path: Path) -> None:
        """Canonical cli.py modules may export main()."""
        (tmp_path / "cli.py").write_text(
            '__all__ = ["main", "CliRunner"]\n\n'
            "def main() -> int:\n    return 0\n\n"
            "class CliRunner:\n    pass\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="main")
        tm.that(index["main"], eq=("test_pkg.cli", "main"))
        tm.that(index, contains="CliRunner")

    def test_main_is_indexed_from_main_module(self, tmp_path: Path) -> None:
        """Canonical main.py modules may export main()."""
        (tmp_path / "main.py").write_text(
            "def main() -> int:\n    return 0\n\nclass CliRunner:\n    pass\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="main")
        tm.that(index["main"], eq=("test_pkg.main", "main"))
        tm.that(index, contains="CliRunner")

    def test_typings_allows_typevar_and_canonical_alias(self, tmp_path: Path) -> None:
        """Type variables stay allowed only inside typings namespace modules."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "typings.py").write_text(
            "from typing import TypeVar\n\n"
            'TValue = TypeVar("TValue")\n\n'
            "class TestPkgTypes:\n    pass\n\n"
            "t = TestPkgTypes\n",
        )
        index = u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")
        tm.that(index, contains="TestPkgTypes")
        tm.that(index, contains="t")
        tm.that(index, contains="TValue")

    def test_non_typings_typevar_is_allowed_but_not_auto_exported(
        self,
        tmp_path: Path,
    ) -> None:
        """Loose TypeVars are allowed at module level but do not auto-export."""
        (tmp_path / "base.py").write_text(
            "from typing import TypeVar\n\n"
            'T = TypeVar("T")\n\n'
            "class ProjectServiceBase:\n    pass\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="ProjectServiceBase")
        tm.that(index, excludes="T")

    def test_fixture_modules_allow_pytest_fixtures_without_namespace_class(
        self,
        tmp_path: Path,
    ) -> None:
        """Private _fixtures packages may expose pytest fixtures without facade classes."""
        fixtures_dir = tmp_path / "_fixtures"
        fixtures_dir.mkdir()
        (fixtures_dir / "__init__.py").write_text("")
        (fixtures_dir / "settings.py").write_text(
            "from collections.abc import Iterator\n"
            "from typing import TypeVar\n\n"
            "import pytest\n\n"
            "T = TypeVar('T')\n\n"
            "@pytest.fixture(autouse=True)\n"
            "def reset_settings() -> Iterator[None]:\n"
            "    yield\n\n"
            "@pytest.fixture\n"
            "def settings() -> Iterator[None]:\n"
            "    yield\n\n"
            "@pytest.fixture\n"
            "def settings_factory() -> Iterator[None]:\n"
            "    yield\n",
        )
        index = u.Infra.build_sibling_export_index(fixtures_dir, "test_pkg._fixtures")
        tm.that(index, contains="settings")
        tm.that(index, contains="reset_settings")
        tm.that(index, contains="settings_factory")
        tm.that(index, excludes="T")
        tm.that(
            index["reset_settings"],
            eq=("test_pkg._fixtures.settings", "reset_settings"),
        )
        tm.that(index["settings"], eq=("test_pkg._fixtures.settings", "settings"))
        tm.that(
            index["settings_factory"],
            eq=("test_pkg._fixtures.settings", "settings_factory"),
        )

    def test_logger_is_never_bubbled_as_public_export(self) -> None:
        """Logger must stay internal even when generation scans package exports."""
        tm.that(u.Infra.should_bubble_up("logger"), eq=False)

    def test_parent_index_skips_nested_package_internals(self, tmp_path: Path) -> None:
        """Parent package scanning must ignore files owned by nested child packages."""
        for package_name, class_name in (
            ("_oid", "TestPkgOidConstants"),
            ("_oud", "TestPkgOudConstants"),
        ):
            package_dir = tmp_path / package_name
            package_dir.mkdir()
            (package_dir / "__init__.py").write_text("")
            (package_dir / "constants.py").write_text(
                f"class {class_name}:\n    pass\n\nc = {class_name}\n",
            )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, excludes="c")
        tm.that(index, excludes="TestPkgOidConstants")
        tm.that(index, excludes="TestPkgOudConstants")

    def test_test_fixture_packages_only_export_module_names(
        self, tmp_path: Path
    ) -> None:
        """tests.fixtures packages must keep invalid fixture symbols private."""
        (tmp_path / "rule0_a.py").write_text("class DuplicateFixture:\n    pass\n")
        (tmp_path / "rule0_b.py").write_text("class DuplicateFixture:\n    pass\n")
        index = u.Infra.build_sibling_export_index(
            tmp_path,
            "tests.fixtures.namespace_validator",
        )
        tm.that(index, eq={})
        tm.that(index, excludes="DuplicateFixture")

    def test_generic_test_modules_export_only_module_names(
        self, tmp_path: Path
    ) -> None:
        """Generic tests/unit modules must not bubble helper symbols to package root."""
        (tmp_path / "test_factory.py").write_text(
            "def get_global_factory() -> object:\n"
            "    return object()\n\n"
            "class TestFactory:\n"
            "    pass\n",
        )

        index = u.Infra.build_sibling_export_index(tmp_path, "tests.unit")

        tm.that(index, eq={})
        tm.that(index, excludes="get_global_factory")
        tm.that(index, excludes="TestFactory")

    def test_helpers_rejects_wrong_canonical_alias(self, tmp_path: Path) -> None:
        """Only the canonical alias for a namespace file may stay at module level."""
        (tmp_path / "helpers.py").write_text(
            "class ProjectHelpers:\n    pass\n\nu = ProjectHelpers\n",
        )
        with pytest.raises(ValueError, match="canonical alias"):
            u.Infra.build_sibling_export_index(tmp_path, "test_pkg")

    def test_base_rejects_loose_objects_and_multiple_classes(
        self,
        tmp_path: Path,
    ) -> None:
        """Base-like modules must fail fast on loose objects and extra classes."""
        (tmp_path / "base.py").write_text(
            "def helper() -> None:\n    pass\n\n"
            "class ProjectServiceBase:\n    pass\n\n"
            "class ProjectCommandContext:\n    pass\n",
        )
        with pytest.raises(ValueError, match="exactly one outer class"):
            u.Infra.build_sibling_export_index(tmp_path, "test_pkg")

    def test_public_namespace_rejects_wrong_class_name(self, tmp_path: Path) -> None:
        """Project-root namespace files must keep the canonical class pattern."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "utilities.py").write_text(
            "class UtilityBag:\n    pass\n\nu = UtilityBag\n"
        )
        with pytest.raises(ValueError, match=r"must start with|must end with"):
            u.Infra.build_sibling_export_index(src_dir, "test_pkg")

    def test_private_family_modules_accept_private_family_tokens(
        self,
        tmp_path: Path,
    ) -> None:
        """Private family mixins accept family markers in middle or suffix."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        family_specs = (
            ("_constants", "base.py", "TestPkgConstantsBase"),
            ("_protocols", "base.py", "TestPkgProtocolsBase"),
            ("_typings", "base.py", "TestPkgTypingBase"),
            ("_utilities", "base.py", "TestPkgUtilitiesBase"),
            ("_models", "generic.py", "TestPkgGenericModels"),
        )
        for directory, file_name, class_name in family_specs:
            target_dir = pkg_dir / directory
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / file_name).write_text(f"class {class_name}:\n    pass\n")

        index = u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")

        for _, _, class_name in family_specs:
            tm.that(index, contains=class_name)

    def test_private_typings_allows_local_type_checking_alias_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """TYPE_CHECKING may import only canonical aliases from the local root."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        typings_dir = pkg_dir / "_typings"
        typings_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (typings_dir / "services.py").write_text(
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from test_pkg import m, p\n\n"
            "class TestPkgServiceTypes:\n"
            "    pass\n",
        )

        index = u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")

        tm.that(index, contains="TestPkgServiceTypes")

    def test_private_typings_rejects_type_checking_else_branch(
        self,
        tmp_path: Path,
    ) -> None:
        """TYPE_CHECKING blocks with else remain forbidden."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        typings_dir = pkg_dir / "_typings"
        typings_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (typings_dir / "services.py").write_text(
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from test_pkg import m\n"
            "else:\n"
            "    from test_pkg import p\n\n"
            "class TestPkgServiceTypes:\n"
            "    pass\n",
        )

        with pytest.raises(ValueError, match="disallowed top-level If"):
            u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")

    def test_private_typings_rejects_noncanonical_type_checking_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """TYPE_CHECKING blocks must import only c/m/t/p/u from the local root."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        typings_dir = pkg_dir / "_typings"
        typings_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (typings_dir / "services.py").write_text(
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from tests import m\n\n"
            "class TestPkgServiceTypes:\n"
            "    pass\n",
        )

        with pytest.raises(ValueError, match="disallowed top-level If"):
            u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")

    def test_private_typings_rejects_wrong_alias_in_type_checking_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """TYPE_CHECKING blocks reject non-canonical alias names."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        typings_dir = pkg_dir / "_typings"
        typings_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (typings_dir / "services.py").write_text(
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from test_pkg import x\n\n"
            "class TestPkgServiceTypes:\n"
            "    pass\n",
        )

        with pytest.raises(ValueError, match="disallowed top-level If"):
            u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")

    def test_root_cli_allows_main_and_main_guard(self, tmp_path: Path) -> None:
        """Root cli.py may keep the entrypoint function and __main__ guard."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
        pkg_dir = tmp_path / "src" / "test_pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "cli.py").write_text(
            "class TestPkgCli:\n"
            "    @classmethod\n"
            "    def run(cls) -> int:\n"
            "        return 0\n\n"
            "def main() -> int:\n"
            "    return TestPkgCli.run()\n\n"
            'if __name__ == "__main__":\n'
            "    main()\n",
        )

        index = u.Infra.build_sibling_export_index(pkg_dir, "test_pkg")

        tm.that(index, contains="TestPkgCli")
        tm.that(index, excludes="main")

    def test_root_api_allows_canonical_singleton_alias(self, tmp_path: Path) -> None:
        """Root api.py may keep the derived singleton alias for the facade."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-demo"\n')
        pkg_dir = tmp_path / "src" / "flext_demo"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "api.py").write_text(
            "class FlextDemo:\n"
            "    @classmethod\n"
            "    def get_instance(cls) -> 'FlextDemo':\n"
            "        return cls()\n\n"
            "demo = FlextDemo.get_instance()\n",
        )

        index = u.Infra.build_sibling_export_index(pkg_dir, "flext_demo")

        tm.that(index, contains="FlextDemo")
        tm.that(index, contains="demo")

    def test_root_api_rejects_noncanonical_singleton_alias(
        self,
        tmp_path: Path,
    ) -> None:
        """Root api.py must not keep ad-hoc singleton alias names."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-demo"\n')
        pkg_dir = tmp_path / "src" / "flext_demo"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "api.py").write_text(
            "class FlextDemo:\n"
            "    @classmethod\n"
            "    def get_instance(cls) -> 'FlextDemo':\n"
            "        return cls()\n\n"
            "service = FlextDemo.get_instance()\n",
        )

        with pytest.raises(ValueError, match="disallowed top-level assignment"):
            u.Infra.build_sibling_export_index(pkg_dir, "flext_demo")

    def test_base_allows_service_alias_pointing_to_outer_class(
        self,
        tmp_path: Path,
    ) -> None:
        """base.py may keep `s` only when it aliases the outer ServiceBase class."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-demo"\n')
        pkg_dir = tmp_path / "src" / "flext_demo"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "base.py").write_text(
            "class FlextDemoServiceBase:\n    pass\n\ns = FlextDemoServiceBase\n",
        )

        index = u.Infra.build_sibling_export_index(pkg_dir, "flext_demo")

        tm.that(index, contains="FlextDemoServiceBase")
        tm.that(index, contains="s")

    def test_public_subpackage_exports_public_classes_from_private_modules(
        self,
        tmp_path: Path,
    ) -> None:
        """Nested public packages keep public class exports from `_*.py` files."""
        pkg_dir = tmp_path / "codegen"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "_codegen_generation.py").write_text(
            "class TestPkgCodegenGeneration:\n    pass\n",
        )

        index = u.Infra.build_sibling_export_index(pkg_dir, "test_pkg.codegen")

        tm.that(index, contains="TestPkgCodegenGeneration")
        tm.that(index, excludes="_codegen_generation")


class TestExtractExports:
    """Test extract_exports function."""

    def test_with_list_all(self) -> None:
        """Test __all__ as list."""
        code = '__all__ = ["Foo", "Bar"]'
        has_all, exports = _extract_exports(code)
        tm.that(has_all, eq=True)
        tm.that(exports, eq=("Foo", "Bar"))

    def test_with_tuple_all(self) -> None:
        """Test __all__ as tuple."""
        code = '__all__ = ("Foo", "Bar")'
        has_all, exports = _extract_exports(code)
        tm.that(has_all, eq=True)
        tm.that(exports, eq=("Foo", "Bar"))

    def test_with_non_string_elements(self) -> None:
        """Test ignores non-string elements."""
        code = '__all__ = ["Foo", 123, "Bar"]'
        has_all, exports = _extract_exports(code)
        tm.that(has_all, eq=True)
        tm.that(exports, eq=("Foo", "Bar"))

    def test_without_all(self) -> None:
        """Test when __all__ is missing."""
        code = "x = 1"
        has_all, exports = _extract_exports(code)
        tm.that(not has_all, eq=True)
        tm.that(exports, eq=())
