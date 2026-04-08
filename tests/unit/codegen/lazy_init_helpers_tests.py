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
        (tmp_path / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["Foo", "Bar"]\n\nclass Foo: pass\nclass Bar: pass\n',
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="Foo")
        tm.that(index, contains="Bar")
        tm.that(index["Foo"], eq=("test_pkg.models", "Foo"))

    def test_without_all_falls_back_to_ast(self, tmp_path: Path) -> None:
        """Test scanning sibling files without __all__ uses AST."""
        (tmp_path / "service.py").write_text(
            "class PublicService:\n    pass\n\ndef public_func():\n    pass\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="PublicService")
        tm.that(index, contains="public_func")

    def test_skips_init_and_main(self, tmp_path: Path) -> None:
        """Test that __init__.py and __main__.py are skipped."""
        (tmp_path / "__init__.py").write_text('__all__ = ["Init"]\n')
        (tmp_path / "__main__.py").write_text("def main(): pass\n")
        (tmp_path / "models.py").write_text(
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

    def test_skips_version_file(self, tmp_path: Path) -> None:
        """Test that __version__.py is skipped (handled separately)."""
        (tmp_path / "__version__.py").write_text('__version__ = "1.0.0"\n')
        (tmp_path / "models.py").write_text(
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
        (tmp_path / "alpha.py").write_text("def main() -> None:\n    pass\n")
        (tmp_path / "beta.py").write_text("def main() -> None:\n    pass\n")
        with pytest.raises(ValueError, match="export collision"):
            u.Infra.build_sibling_export_index(tmp_path, "test_pkg")

    def test_typings_allows_typevar_and_canonical_alias(self, tmp_path: Path) -> None:
        """Type variables stay allowed only inside typings namespace modules."""
        (tmp_path / "typings.py").write_text(
            "from typing import TypeVar\n\n"
            'TValue = TypeVar("TValue")\n\n'
            "class ProjectTypes:\n    pass\n\n"
            "t = ProjectTypes\n",
        )
        index = u.Infra.build_sibling_export_index(tmp_path, "test_pkg")
        tm.that(index, contains="ProjectTypes")
        tm.that(index, contains="t")

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
        with pytest.raises(ValueError, match="must start with|must end with"):
            u.Infra.build_sibling_export_index(src_dir, "test_pkg")


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
