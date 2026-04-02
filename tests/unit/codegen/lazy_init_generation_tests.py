"""Tests for lazy_init code generation: aliases, type checking, file output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra.codegen as mod
from flext_core import r
from flext_infra import FlextInfraCodegenGeneration, FlextInfraCodegenLazyInit
from tests import t, u

_resolve_aliases: Callable[[Mapping[str, tuple[str, str]]], None] = getattr(
    FlextInfraCodegenLazyInit,
    "_resolve_aliases",
)
_generate_file = FlextInfraCodegenGeneration.generate_file
_run_ruff_fix: Callable[[Path], None] = getattr(
    FlextInfraCodegenLazyInit,
    "_run_ruff_fix",
)


class TestResolveAliases:
    """Test _resolve_aliases function."""

    def test_resolves_c_alias(self) -> None:
        """Test resolving 'c' alias to Constants class."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        _resolve_aliases(lazy_map)
        tm.that(lazy_map, contains="c")
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_does_not_overwrite_canonical_existing(self) -> None:
        """Test that canonical alias pointing to correct facade is preserved."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "c": ("pkg.constants", "FlextConstants"),
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        _resolve_aliases(lazy_map)
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_overwrites_non_canonical_existing(self) -> None:
        """Test that non-canonical alias is replaced with canonical facade."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "c": ("pkg.custom", "CustomConst"),
            "FlextConstants": ("pkg.constants", "FlextConstants"),
        }
        _resolve_aliases(lazy_map)
        tm.that(lazy_map["c"], eq=("pkg.constants", "FlextConstants"))

    def test_resolves_multiple_aliases(self) -> None:
        """Test resolving multiple aliases at once."""
        lazy_map: MutableMapping[str, tuple[str, str]] = {
            "FlextConstants": ("pkg.constants", "FlextConstants"),
            "FlextModels": ("pkg.models", "FlextModels"),
            "FlextTypes": ("pkg.typings", "FlextTypes"),
        }
        _resolve_aliases(lazy_map)
        tm.that(lazy_map, contains="c")
        tm.that(lazy_map, contains="m")
        tm.that(lazy_map, contains="t")


class TestGenerateTypeChecking:
    """Test generate_type_checking function."""

    def test_with_empty_groups(self) -> None:
        """Test with no imports returns header + FlextTypes only."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = u.Infra.generate_type_checking(groups)
        tm.that(lines, contains="if _TYPE_CHECKING:")
        tm.that(any("FlextTypes" in line for line in lines), eq=True)

    def test_with_empty_groups_no_flext_types(self) -> None:
        """Test with no imports and no FlextTypes returns empty list."""
        groups: Mapping[str, Sequence[tuple[str, str]]] = {}
        lines = u.Infra.generate_type_checking(
            groups,
            include_flext_types=False,
        )
        tm.that(lines, eq=[])

    def test_with_single_module(self) -> None:
        """Test with single module."""
        groups = {"module": [("Test", "Test")]}
        lines = u.Infra.generate_type_checking(groups)
        tm.that(" ".join(lines), contains="from module import")

    def test_with_aliased_imports(self) -> None:
        """Test with aliased imports."""
        groups = {"module": [("c", "FlextConstants"), ("m", "FlextModels")]}
        lines = u.Infra.generate_type_checking(groups)
        joined = " ".join(lines)
        tm.that(joined, contains="from module import *")

    def test_with_long_import_line(self) -> None:
        """Test wraps long import lines."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["module"] = [
            ("VeryLongClassName1", "VeryLongClassName1"),
            ("VeryLongClassName2", "VeryLongClassName2"),
            ("VeryLongClassName3", "VeryLongClassName3"),
        ]
        lines = u.Infra.generate_type_checking(groups)
        tm.that(any("module" in line for line in lines), eq=True)

    def test_with_multiple_modules_spacing(self) -> None:
        """Test blank lines between different top-level package groups."""
        groups: MutableMapping[str, Sequence[tuple[str, str]]] = defaultdict(list)
        groups["alpha_pkg.module"] = [("Test1", "Test1")]
        groups["beta_pkg.module"] = [("Test2", "Test2")]
        lines = u.Infra.generate_type_checking(groups)
        tm.that(lines, contains="")


class TestGenerateFile:
    """Test _generate_file function."""

    def test_with_flext_core_package(self) -> None:
        """Test uses correct lazy import for flext_core."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = _generate_file("", exports, filtered, inline_constants, "flext_core")
        tm.that(content, contains="flext_core.lazy")

    def test_with_other_package(self) -> None:
        """Test uses correct lazy import for non-core packages."""
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = _generate_file("", exports, filtered, inline_constants, "other_pkg")
        tm.that(content, contains="from flext_core import install_lazy_exports")

    def test_with_inline_constants(self) -> None:
        """Test includes inline constants."""
        exports = ["__version__", "Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants = {"__version__": "1.0.0"}
        content = _generate_file("", exports, filtered, inline_constants, "test_pkg")
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
        content = _generate_file(
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
        tm.that(content, contains="_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {")

    def test_with_docstring(self) -> None:
        """Test preserves docstring."""
        docstring = '"""Test module."""'
        exports = ["Test"]
        filtered = {"Test": ("module", "Test")}
        inline_constants: t.StrMapping = {}
        content = _generate_file(
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
        content = _generate_file("", exports, filtered, inline_constants, "test_pkg")
        tm.that(content, contains="AUTO-GENERATED")

    def test_has_lazy_imports_with_exports(self) -> None:
        """Test generated file registers exports in _LAZY_IMPORTS."""
        exports = ["Alpha", "Beta"]
        filtered = {"Alpha": ("mod", "Alpha"), "Beta": ("mod", "Beta")}
        inline_constants: t.StrMapping = {}
        content = _generate_file("", exports, filtered, inline_constants, "test_pkg")
        tm.that(content, contains="install_lazy_exports")
        tm.that(content, contains='"Alpha"')
        tm.that(content, contains='"Beta"')


class TestRunRuffFix:
    """Test _run_ruff_fix function."""

    def test_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handles nonexistent files gracefully."""
        nonexistent = tmp_path / "nonexistent.py"
        _run_ruff_fix(nonexistent)  # Should not raise

    def test_runs_ruff_check_and_format(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test generated files are lint-fixed and formatted."""
        generated = tmp_path / "__init__.py"
        generated.write_text("__all__=[]\n", encoding="utf-8")
        commands: list[list[str]] = []

        def _run_checked(
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
        ) -> r[bool]:
            _ = (cwd, timeout, env)
            commands.append(list(cmd))
            return r[bool].ok(True)

        monkeypatch.setattr(u.Infra, "run_checked", _run_checked)
        _run_ruff_fix(generated)
        tm.that(len(commands), eq=2)
        tm.that(commands[0], eq=["ruff", "check", "--fix", "--quiet", str(generated)])
        tm.that(commands[1], eq=["ruff", "format", "--quiet", str(generated)])

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

        monkeypatch.setattr(u.Infra, "run_checked", _run_checked)
        with pytest.raises(ValueError, match="ruff format failed"):
            _run_ruff_fix(generated)


def test_codegen_init_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(mod, "nonexistent_xyz_attribute")
