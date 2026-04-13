"""Tests for lazy_init code generation: aliases, type checking, file output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra as mod
from flext_infra import FlextInfraCodegenGeneration
from tests import t, u


class TestGenerateTypeChecking:
    """Test generate_type_checking function."""

    def test_with_empty_groups(self) -> None:
        """Test with no imports returns header + FlextTypes only."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="if _t.TYPE_CHECKING:")
        tm.that(any("FlextTypes" in line for line in lines), eq=True)

    def test_with_empty_groups_no_flext_types(self) -> None:
        """Test with no imports and no FlextTypes returns empty list."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=False,
        )
        tm.that(lines, eq=[])

    def test_with_single_module(self) -> None:
        """Test with single module."""
        groups = {"module": [("Test", "Test")]}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(" ".join(lines), contains="from module import")

    def test_with_aliased_imports(self) -> None:
        """Test with aliased imports."""
        groups = {"module": [("c", "FlextConstants"), ("m", "FlextModels")]}
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        joined = " ".join(lines)
        tm.that(
            joined, contains="from module import FlextConstants as c, FlextModels as m"
        )

    def test_with_long_import_line(self) -> None:
        """Test wraps long import lines."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["module"] = [
            ("VeryLongClassName1", "VeryLongClassName1"),
            ("VeryLongClassName2", "VeryLongClassName2"),
            ("VeryLongClassName3", "VeryLongClassName3"),
        ]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(any("module" in line for line in lines), eq=True)

    def test_with_multiple_modules(self) -> None:
        """Test multiple type-checking imports are emitted."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["alpha_pkg.module"] = [("Test1", "Test1")]
        groups["beta_pkg.module"] = [("Test2", "Test2")]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        joined = "\n".join(lines)
        tm.that(joined, contains="from alpha_pkg.module import Test1")
        tm.that(joined, contains="from beta_pkg.module import Test2")


class TestGenerateFile:
    """Test public lazy-init file generation behavior."""

    def test_with_flext_core_package(self) -> None:
        """Test uses correct lazy import for flext_core."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "flext_core",
        )
        tm.that(
            content,
            contains="from flext_core.lazy import build_lazy_import_map, install_lazy_exports",
        )

    def test_with_other_package(self) -> None:
        """Test uses correct lazy import for non-core packages."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "other_pkg",
        )
        tm.that(
            content,
            contains="from flext_core.lazy import build_lazy_import_map, install_lazy_exports",
        )

    def test_with_inline_constants(self) -> None:
        """Test includes inline constants."""
        exports = ["__version__", "Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants = {"__version__": "1.0.0"}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains='__version__ = "1.0.0"')

    def test_with_eager_runtime_imports(self) -> None:
        """Test version-like exports are imported eagerly at runtime."""
        exports = ["FlextVersion", "__version__"]
        filtered: t.Infra.LazyImportMap = {}
        inline_constants: t.StrMapping = {}
        eager_imports: t.Infra.LazyImportMap = {
            "FlextVersion": ("test_pkg.__version__", "FlextVersion"),
            "__version__": ("test_pkg.__version__", "__version__"),
        }
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            eager_imports=eager_imports,
        )
        tm.that(
            content,
            contains="from test_pkg.__version__ import FlextVersion, __version__",
        )
        tm.that(content, contains="_LAZY_IMPORTS = build_lazy_import_map(")
        tm.that(content, lacks="merge_lazy_imports(")
        tm.that(content, contains="build_lazy_import_map(")
        tm.that(content, contains='        "FlextVersion",')
        tm.that(content, contains='        "__version__",')

    def test_skips_wildcard_runtime_modules_in_type_checking(self) -> None:
        """Test wildcard runtime imports are not duplicated in TYPE_CHECKING."""
        exports = ["VERSION", "__version__", "Test"]
        filtered: t.Infra.LazyImportMap = {
            "VERSION": ("test_pkg.__version__", "VERSION"),
            "__version__": ("test_pkg.__version__", "__version__"),
            "Test": ("test_pkg.models", "Test"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            wildcard_runtime_modules=("test_pkg.__version__",),
        )
        tm.that(content, contains="from test_pkg.__version__ import *")
        tm.that(content, lacks="from test_pkg.__version__ import VERSION")
        tm.that(content, lacks="from test_pkg.__version__ import __version__")

    def test_ignores_docstring_source(self) -> None:
        """Generated __init__.py files should not preserve package docstrings."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, lacks='"""Test module."""')

    def test_has_autogen_header(self) -> None:
        """Test generated file starts with autogen header."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="AUTO-GENERATED")

    def test_has_lazy_imports_with_exports(self) -> None:
        """Test generated file registers exports in _LAZY_IMPORTS."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="install_lazy_exports")
        tm.that(content, contains='"Alpha"')
        tm.that(content, contains='"Beta"')

    def test_typevars_stay_lazy_exports(self) -> None:
        """TypeVar-like exports stay lazy while remaining visible to static analysis."""
        exports = ["FlextTypes", "T", "U"]
        filtered = {
            "FlextTypes": ("test_pkg.typings", "FlextTypes"),
            "T": ("test_pkg.typings", "T"),
            "U": ("test_pkg.typings", "U"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="if _t.TYPE_CHECKING:")
        tm.that(
            content,
            contains="from test_pkg.typings import FlextTypes, T, U",
        )
        tm.that(content, contains='        ".typings": (')
        tm.that(content, contains='            "T",')
        tm.that(content, contains='            "U",')

    def test_root_namespace_emits_static_analysis_hints(self) -> None:
        """Root namespace __init__.py keeps TYPE_CHECKING and __all__."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains="if _t.TYPE_CHECKING:")
        tm.that(content, contains="import typing as _t")
        tm.that(content, contains="__all__: list[str] = [")
        tm.that(
            content, contains="install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)"
        )

    def test_root_namespace_writes___all___after_lazy_loader(self) -> None:
        """Root namespace places ``__all__`` after ``install_lazy_exports``."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(
            content.rfind("__all__: list[str] = [")
            > content.rfind("install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)"),
            eq=True,
        )

    def test_root_namespace_type_checking_uses_source_modules(self) -> None:
        """Root namespace TYPE_CHECKING must target real source modules."""
        exports = ["Alpha", "Beta"]
        filtered = {
            "Alpha": ("test_pkg._constants.base", "Alpha"),
            "Beta": ("test_pkg._models.base", "Beta"),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            child_packages_for_tc=("test_pkg._constants", "test_pkg._models"),
        )
        tm.that(content, contains="from test_pkg._constants.base import Alpha")
        tm.that(content, contains="from test_pkg._models.base import Beta")
        tm.that(content, lacks="from test_pkg._constants import Alpha")
        tm.that(content, lacks="from test_pkg._models import Beta")

    def test_root_namespace_normalizes_private_local_module_targets(self) -> None:
        """Root namespace never emits unqualified private-package imports."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha", "Beta"],
            {
                "Alpha": ("_constants.base", "Alpha"),
                "Beta": ("_models.base", "Beta"),
            },
            {},
            "test_pkg",
        )
        tm.that(content, contains="from test_pkg._constants.base import Alpha")
        tm.that(content, contains="from test_pkg._models.base import Beta")
        tm.that(content, contains='"._constants.base": ("Alpha",)')
        tm.that(content, contains='"._models.base": ("Beta",)')
        tm.that(content, lacks="from _constants")
        tm.that(content, lacks="from _models")
        tm.that(content, lacks='"_constants.base"')
        tm.that(content, lacks='"_models.base"')

    def test_subpackage_generated_init_includes_package_docstring(self) -> None:
        """Generated subpackage __init__.py files include the package docstring."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha"],
            {"Alpha": ("test_pkg.tools.alpha", "Alpha")},
            {},
            "test_pkg.tools",
        )
        tm.that(content, contains='"""Tools package."""')

    def test_subpackage_keeps_module_entries_in_lazy_imports(self) -> None:
        """Subpackage module entries remain importable through _LAZY_IMPORTS."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["test_base"],
            {"test_base": ("tests.unit._models.test_base", "")},
            {},
            "tests.unit._models",
        )
        tm.that(content, contains='".test_base": ("test_base",)')
        tm.that(content, contains="publish_all=False")
        tm.that(content, lacks="__all__: list[str] = [")

    def test_subpackage_omits_type_checking_for_internal_exports(self) -> None:
        """Subpackage __init__.py does not emit static imports for internals."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["ExamplesFlextCoreModelsEx00"],
            {
                "ExamplesFlextCoreModelsEx00": (
                    "examples._models.ex00",
                    "ExamplesFlextCoreModelsEx00",
                ),
            },
            {},
            "examples._models",
        )
        tm.that(content, contains='".ex00": ("ExamplesFlextCoreModelsEx00",)')
        tm.that(content, lacks="if _t.TYPE_CHECKING:")
        tm.that(content, lacks="from _models")
        tm.that(content, lacks="from examples._models.ex00 import")

    def test_root_namespace_type_checking_skips_module_reexport_names(self) -> None:
        """Root namespace TYPE_CHECKING must omit module/package compatibility names."""
        exports = ["_constants", "api", "constants"]
        filtered = {
            "_constants": ("test_pkg", "_constants"),
            "api": ("test_pkg.api", ""),
            "constants": ("test_pkg.constants", ""),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, lacks="import test_pkg.api as api")
        tm.that(content, lacks="import test_pkg.constants as constants")
        tm.that(content, lacks="from test_pkg import _constants")
        tm.that(content, lacks="from test_pkg import api")
        tm.that(content, lacks="from test_pkg import constants")

    def test_root_namespace_omits_module_and_directory_exports(self) -> None:
        """Root namespace omits compatibility module/directory names entirely."""
        exports = ["Alpha", "_constants", "api", "constants", "tools"]
        filtered = {
            "Alpha": ("test_pkg._utilities.alpha", "Alpha"),
            "_constants": ("test_pkg._constants", ""),
            "api": ("test_pkg.api", ""),
            "constants": ("test_pkg.constants", ""),
            "tools": ("test_pkg.tools", ""),
        }
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            child_packages_for_lazy=("test_pkg._constants", "test_pkg.tools"),
            child_packages_for_tc=("test_pkg._constants", "test_pkg.tools"),
        )
        tm.that(content, contains='"._utilities.alpha": ("Alpha",)')
        tm.that(content, lacks='"_constants": "test_pkg._constants"')
        tm.that(content, lacks='"api": "test_pkg.api"')
        tm.that(content, lacks='"constants": "test_pkg.constants"')
        tm.that(content, lacks='"tools": "test_pkg.tools"')
        tm.that(content, contains='    "Alpha",')
        tm.that(content, lacks='    "_constants",')
        tm.that(content, lacks='    "api",')
        tm.that(content, lacks='    "constants",')
        tm.that(content, lacks='    "tools",')

    def test_root_namespace_uses_relative_child_package_paths(self) -> None:
        """Root merge list uses relative child package paths for local children."""
        exports = ["Alpha"]
        filtered = {"Alpha": ("test_pkg.models", "Alpha")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            child_packages_for_lazy=("test_pkg._constants", "test_pkg.services"),
        )
        tm.that(content, contains='"._constants"')
        tm.that(content, contains='".services"')
        tm.that(content, contains="exclude_names=(")
        tm.that(content, contains="module_name=__name__")
        tm.that(content, lacks='"test_pkg._constants"')
        tm.that(content, lacks='"test_pkg.services"')
        tm.that(content, lacks="_LAZY_IMPORTS.pop(")

    def test_subpackage_omits_static_analysis_hints(self) -> None:
        """Non-root package __init__.py keeps only _LAZY_IMPORTS + lazy loader."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            inline_constants,
            "test_pkg.transformers",
        )
        tm.that(content, lacks="if _t.TYPE_CHECKING:")
        tm.that(content, lacks="import typing as _t")
        tm.that(content, lacks="__all__: list[str] = [")
        tm.that(
            content,
            contains=(
                "install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, "
                "publish_all=False)"
            ),
        )


class TestRunRuffFix:
    """Test public ruff post-processing utility behavior."""

    def test_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handles nonexistent files gracefully."""
        nonexistent = tmp_path / "nonexistent.py"
        u.Infra.run_ruff_fix(nonexistent)

    def test_runs_ruff_check_and_format(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated files are lint-fixed and formatted."""
        generated = tmp_path / "__init__.py"
        generated.write_text("__all__=[]\n", encoding="utf-8")
        u.Infra.run_ruff_fix(generated)
        tm.that(generated.read_text(encoding="utf-8"), eq="__all__ = []\n")

    def test_raises_when_ruff_postprocess_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generator fails when ruff post-processing fails."""
        generated = tmp_path / "__init__.py"
        generated.write_text("def broken(:\n", encoding="utf-8")
        with pytest.raises(ValueError, match="ruff"):
            u.Infra.run_ruff_fix(generated)


def test_codegen_init_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(mod, "nonexistent_xyz_attribute")
