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
from tests import r, t, u

import flext_infra.codegen as mod


class TestResolveAliases:
    """Test public alias resolution utility behavior."""

    def test_resolves_c_alias(self) -> None:
        """Test resolving 'c' alias to Constants class."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=Path("/workspace/pkg"))
        tm.that(lazy_map, contains="c")
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_does_not_overwrite_canonical_existing(self) -> None:
        """Test that canonical alias pointing to correct facade is preserved."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "c": ("pkg.constants", "FlextConstants"),
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=Path("/workspace/pkg"))
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_overwrites_non_canonical_existing(self) -> None:
        """Test that non-canonical alias is replaced with canonical facade."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "c": ("pkg.custom", "CustomConst"),
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=Path("/workspace/pkg"))
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_resolves_multiple_aliases(self) -> None:
        """Test resolving multiple aliases at once."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
            "FlextModels": ("pkg.models", "FlextModels"),
            "FlextTypes": ("pkg.typings", "FlextTypes"),
        }
        u.Infra().resolve_aliases(lazy_map, pkg_dir=Path("/workspace/pkg"))
        tm.that(lazy_map, contains="c")
        tm.that(lazy_map, contains="m")
        tm.that(lazy_map, contains="t")


class TestGenerateTypeChecking:
    """Test generate_type_checking function."""

    def test_with_empty_groups(self) -> None:
        """Test with no imports returns header + FlextTypes only."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = mod.FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="if _t.TYPE_CHECKING:")
        tm.that(any("FlextTypes" in line for line in lines), eq=True)

    def test_with_empty_groups_no_flext_types(self) -> None:
        """Test with no imports and no FlextTypes returns empty list."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = mod.FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=False,
        )
        tm.that(lines, eq=[])

    def test_with_single_module(self) -> None:
        """Test with single module."""
        groups = {"module": [("Test", "Test")]}
        lines = mod.FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(" ".join(lines), contains="from module import")

    def test_with_aliased_imports(self) -> None:
        """Test with aliased imports."""
        groups = {"module": [("c", "FlextConstants"), ("m", "FlextModels")]}
        lines = mod.FlextInfraCodegenGeneration.generate_type_checking(groups)
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
        lines = mod.FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(any("module" in line for line in lines), eq=True)

    def test_with_multiple_modules_spacing(self) -> None:
        """Test blank lines between different top-level package groups."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["alpha_pkg.module"] = [("Test1", "Test1")]
        groups["beta_pkg.module"] = [("Test2", "Test2")]
        lines = mod.FlextInfraCodegenGeneration.generate_type_checking(groups)
        tm.that(lines, contains="")


class TestGenerateFile:
    """Test public lazy-init file generation behavior."""

    def test_with_flext_core_package(self) -> None:
        """Test uses correct lazy import for flext_core."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
            exports,
            filtered,
            inline_constants,
            "flext_core",
        )
        tm.that(content, contains="from flext_core.lazy import  install_lazy_exports")

    def test_with_other_package(self) -> None:
        """Test uses correct lazy import for non-core packages."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
            exports,
            filtered,
            inline_constants,
            "other_pkg",
        )
        tm.that(content, contains="from flext_core.lazy import  install_lazy_exports")

    def test_with_inline_constants(self) -> None:
        """Test includes inline constants."""
        exports = ["__version__", "Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants = {"__version__": "1.0.0"}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
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
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
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
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            wildcard_runtime_modules=("test_pkg.__version__",),
        )
        tm.that(content, contains="from test_pkg.__version__ import *")
        tm.that(content, lacks="from test_pkg.__version__ import VERSION")
        tm.that(content, lacks="from test_pkg.__version__ import __version__")

    def test_with_docstring(self) -> None:
        """Test preserves docstring."""
        docstring = '"""Test module."""'
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            docstring,
            exports,
            filtered,
            inline_constants,
            "test_pkg",
        )
        tm.that(content, contains=docstring)

    def test_has_autogen_header(self) -> None:
        """Test generated file starts with autogen header."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
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
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
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
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
            exports,
            filtered,
            inline_constants,
            "test_pkg",
            eager_typevar_names=frozenset({"T", "U"}),
        )
        tm.that(content, lacks="from test_pkg.typings import T, U")
        tm.that(content, contains='"T": ("test_pkg.typings", "T")')
        tm.that(content, contains='"U": ("test_pkg.typings", "U")')

    def test_root_namespace_emits_static_analysis_hints(self) -> None:
        """Root namespace __init__.py keeps TYPE_CHECKING and __all__."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
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

    def test_subpackage_omits_static_analysis_hints(self) -> None:
        """Non-root package __init__.py keeps only _LAZY_IMPORTS + lazy loader."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = mod.FlextInfraCodegenGeneration.generate_file(
            "",
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

        monkeypatch.setattr(u.Cli, "run_checked", _run_checked)
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

        monkeypatch.setattr(u.Cli, "run_checked", _run_checked)
        with pytest.raises(ValueError, match="ruff format failed"):
            u.Infra.run_ruff_fix(generated)


def test_codegen_init_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(mod, "nonexistent_xyz_attribute")
