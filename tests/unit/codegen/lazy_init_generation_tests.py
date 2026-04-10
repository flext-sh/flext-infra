"""Tests for lazy_init code generation: aliases, type checking, file output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra as mod
from flext_infra import FlextInfraCodegenGeneration
from tests import r, t, u


class TestResolveAliases:
    """Test public alias resolution utility behavior."""

    def test_resolves_c_alias(self, tmp_path: Path) -> None:
        """Test resolving 'c' alias to Constants class."""
        pkg_dir = tmp_path / "src" / "pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=pkg_dir)
        tm.that(lazy_map, contains="c")
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_does_not_overwrite_canonical_existing(self, tmp_path: Path) -> None:
        """Test that canonical alias pointing to correct facade is preserved."""
        pkg_dir = tmp_path / "src" / "pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "c": ("pkg.constants", "FlextConstants"),
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=pkg_dir)
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_overwrites_non_canonical_existing(self, tmp_path: Path) -> None:
        """Test that non-canonical alias is replaced with canonical facade."""
        pkg_dir = tmp_path / "src" / "pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "c": ("pkg.custom", "CustomConst"),
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=pkg_dir)
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_resolves_multiple_aliases(self, tmp_path: Path) -> None:
        """Test resolving multiple aliases at once."""
        pkg_dir = tmp_path / "src" / "pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
            "FlextModels": ("pkg.models", "FlextModels"),
            "FlextTypes": ("pkg.typings", "FlextTypes"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=pkg_dir)
        tm.that(lazy_map, contains="c")
        tm.that(lazy_map, contains="m")
        tm.that(lazy_map, contains="t")

    def test_subpackage_does_not_add_runtime_aliases(self, tmp_path: Path) -> None:
        """Subpackages keep _LAZY_IMPORTS free of runtime aliases."""
        pkg_dir = tmp_path / "src" / "pkg" / "tools"
        pkg_dir.mkdir(parents=True)
        _ = (tmp_path / "src" / "pkg" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        _ = (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
            "FlextModels": ("pkg.models", "FlextModels"),
            "FlextTypes": ("pkg.typings", "FlextTypes"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=pkg_dir)
        tm.that(lazy_map, lacks="c")
        tm.that(lazy_map, lacks="m")
        tm.that(lazy_map, lacks="t")


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

    def test_with_multiple_modules_spacing(self) -> None:
        """Test blank lines between different top-level package groups."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["alpha_pkg.module"] = [("Test1", "Test1")]
        groups["beta_pkg.module"] = [("Test2", "Test2")]
        lines = FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="")


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
        tm.that(content, contains="from flext_core import install_lazy_exports")

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
        tm.that(content, contains="from flext_core import install_lazy_exports")

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
        tm.that(content, contains="_LAZY_IMPORTS = {")

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
        """TypeVar-like exports from typings stay lazy and avoid runtime import cycles."""
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
        tm.that(content, lacks="from test_pkg.typings import T, U")
        tm.that(content, contains='"T": ".typings"')
        tm.that(content, contains='"U": ".typings"')

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
        tm.that(content, contains="__all__ = [")
        tm.that(
            content, contains="install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)"
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

    def test_subpackage_generated_init_omits_package_docstrings(self) -> None:
        """Generated subpackage __init__.py files should omit package docstrings."""
        content = FlextInfraCodegenGeneration.generate_file(
            ["Alpha"],
            {"Alpha": ("test_pkg.tools.alpha", "Alpha")},
            {},
            "test_pkg.tools",
        )
        tm.that(content, lacks='"""')

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
        tm.that(content, contains='"Alpha": "._utilities.alpha"')
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
        tm.that(content, lacks="__all__ = [")
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
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test generated files are lint-fixed and formatted."""
        generated = tmp_path / "__init__.py"
        generated.write_text("__all__=[]\n", encoding="utf-8")
        commands: MutableSequence[t.StrSequence] = []

        def _run_checked(
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
        ) -> r[bool]:
            _ = (cwd, timeout, env)
            commands.append(tuple(cmd))
            return r[bool].ok(True)

        u.Infra.run_ruff_fix(generated)
        tm.that(len(commands), eq=2)
        tm.that(
            commands[0],
            eq=("ruff", "check", "--fix", "--quiet", str(generated)),
        )
        tm.that(
            commands[1],
            eq=("ruff", "format", "--quiet", str(generated)),
        )

    def test_raises_when_ruff_postprocess_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test generator fails when ruff post-processing fails."""
        generated = tmp_path / "__init__.py"
        generated.write_text("__all__=[]\n", encoding="utf-8")
        call_count = 0

        def _run_checked(
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
        ) -> r[bool]:
            nonlocal call_count
            _ = (cmd, cwd, timeout, env)
            call_count += 1
            if call_count == 1:
                return r[bool].ok(True)
            return r[bool].fail("ruff format failed")

        with pytest.raises(ValueError, match="ruff format failed"):
            u.Infra.run_ruff_fix(generated)


def test_codegen_init_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(mod, "nonexistent_xyz_attribute")
