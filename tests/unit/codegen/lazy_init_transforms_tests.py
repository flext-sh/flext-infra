"""Tests for lazy_init transform functions: AST scanning, filtering, merging.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from tests import u


class TestScanPublicDefs:
    """Test public export scanning behavior."""

    def test_finds_classes(self, tmp_path: Path) -> None:
        """Test scanning finds public classes."""
        (tmp_path / "module.py").write_text("class PublicClass:\n    pass\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "mod")
        tm.that(index, contains="PublicClass")

    def test_skips_private(self, tmp_path: Path) -> None:
        """Test scanning skips private names."""
        (tmp_path / "module.py").write_text("class _PrivateClass:\n    pass\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "mod")
        tm.that(index, excludes="_PrivateClass")

    def test_finds_functions(self, tmp_path: Path) -> None:
        """Test scanning finds public functions."""
        (tmp_path / "module.py").write_text("def public_func() -> None:\n    pass\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "mod")
        tm.that(index, contains="public_func")

    def test_does_not_export_module_name(self, tmp_path: Path) -> None:
        """Top-level module names are not exported as compatibility entries."""
        (tmp_path / "module.py").write_text("class PublicClass:\n    pass\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "mod")
        tm.that(index, excludes="module")

    def test_finds_assignments(self, tmp_path: Path) -> None:
        """Test scanning finds public assignments."""
        (tmp_path / "module.py").write_text("MY_CONST = 42\n")
        index = u.Infra.build_sibling_export_index(tmp_path, "mod")
        tm.that(index, contains="MY_CONST")


class TestShouldBubbleUp:
    """Test bubble-up filtering for child exports."""

    @staticmethod
    def _merge_single_export(tmp_path: Path, name: str) -> dict[str, tuple[str, str]]:
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir(exist_ok=True)
        lazy_map: dict[str, tuple[str, str]] = {}
        u.Infra.merge_child_exports(
            tmp_path,
            lazy_map,
            {str(sub_dir): {name: ("pkg.sub.module", name)}},
        )
        return lazy_map

    def test_public_class_name(self, tmp_path: Path) -> None:
        """Test that public class names bubble up."""
        tm.that(
            self._merge_single_export(tmp_path, "FlextInfraModels"),
            contains="FlextInfraModels",
        )

    def test_private_name_filtered(self, tmp_path: Path) -> None:
        """Test that private names are filtered."""
        tm.that(self._merge_single_export(tmp_path, "_internal"), excludes="_internal")

    def test_main_filtered(self, tmp_path: Path) -> None:
        """Test that 'main' entry point is filtered."""
        tm.that(self._merge_single_export(tmp_path, "main"), excludes="main")

    def test_all_caps_filtered(self, tmp_path: Path) -> None:
        """Test that ALL_CAPS constants are filtered."""
        tm.that(self._merge_single_export(tmp_path, "BLUE"), excludes="BLUE")
        tm.that(
            self._merge_single_export(tmp_path, "SYM_ARROW"),
            excludes="SYM_ARROW",
        )

    def test_legacy_output_wrapper_is_filtered(self, tmp_path: Path) -> None:
        """Legacy output wrappers must not bubble to package root exports."""
        tm.that(self._merge_single_export(tmp_path, "output"), excludes="output")

    def test_single_letter_aliases_are_filtered(self, tmp_path: Path) -> None:
        """Single-letter runtime aliases must not bubble to package roots."""
        tm.that(self._merge_single_export(tmp_path, "c"), excludes="c")
        tm.that(self._merge_single_export(tmp_path, "e"), excludes="e")


class TestMergeChildExports:
    """Test public child-export merge behavior."""

    def test_merges_child_exports(self, tmp_path: Path) -> None:
        """Test that child exports are merged into parent."""
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        lazy_map: dict[str, tuple[str, str]] = {}
        dir_exports = {
            str(sub_dir): {
                "SubService": ("pkg.sub.service", "SubService"),
            },
        }
        u.Infra.merge_child_exports(tmp_path, lazy_map, dir_exports)
        tm.that(lazy_map, contains="SubService")
        tm.that(lazy_map["SubService"], eq=("pkg.sub.service", "SubService"))

    def test_duplicate_child_export_raises(self, tmp_path: Path) -> None:
        """Duplicate exports must abort instead of silently overwriting."""
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        lazy_map: dict[str, tuple[str, str]] = {
            "Model": ("pkg.models", "Model"),
        }
        dir_exports = {
            str(sub_dir): {
                "Model": ("pkg.sub.models", "Model"),
            },
        }
        with pytest.raises(ValueError, match="export collision"):
            u.Infra.merge_child_exports(tmp_path, lazy_map, dir_exports)

    def test_filters_all_caps(self, tmp_path: Path) -> None:
        """Test that ALL_CAPS constants don't bubble up."""
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        lazy_map: dict[str, tuple[str, str]] = {}
        dir_exports = {
            str(sub_dir): {
                "BLUE": ("pkg.sub.colors", "BLUE"),
                "Service": ("pkg.sub.service", "Service"),
            },
        }
        u.Infra.merge_child_exports(tmp_path, lazy_map, dir_exports)
        tm.that(lazy_map, excludes="BLUE")
        tm.that(lazy_map, contains="Service")

    def test_does_not_export_child_directory_name(self, tmp_path: Path) -> None:
        """Child package names are not exported as compatibility entries."""
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        lazy_map: dict[str, tuple[str, str]] = {}
        dir_exports = {
            str(sub_dir): {
                "SubService": ("pkg.sub.service", "SubService"),
            },
        }
        u.Infra.merge_child_exports(tmp_path, lazy_map, dir_exports)
        tm.that(lazy_map, excludes="sub")


class TestExtractVersionExports:
    """Test public version export extraction."""

    def test_extracts_string_constants(self, tmp_path: Path) -> None:
        """Test extracting __version__ as inline constant."""
        (tmp_path / "__version__.py").write_text('__version__ = "1.0.0"\n')
        inline, _ = u.Infra.extract_version_exports(tmp_path, "test_pkg")
        tm.that(inline, contains="__version__")
        tm.that(inline["__version__"], eq="1.0.0")

    def test_extracts_non_string_as_lazy(self, tmp_path: Path) -> None:
        """Test extracting __version_info__ as lazy import."""
        (tmp_path / "__version__.py").write_text(
            '__version__ = "1.0.0"\n__version_info__ = (1, 0, 0)\n',
        )
        inline, lazy = u.Infra.extract_version_exports(tmp_path, "test_pkg")
        tm.that(inline, contains="__version__")
        tm.that(lazy, contains="__version_info__")
        tm.that(
            lazy["__version_info__"],
            eq=("test_pkg.__version__", "__version_info__"),
        )

    def test_no_version_file(self, tmp_path: Path) -> None:
        """Test returns empty when __version__.py doesn't exist."""
        inline, lazy = u.Infra.extract_version_exports(tmp_path, "test_pkg")
        tm.that(inline, eq={})
        tm.that(lazy, eq={})
