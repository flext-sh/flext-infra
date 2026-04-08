"""Tests for centralized deps subcommand dispatch.

Validates subcommand mapping, help/error paths, and return-value
normalization using real imports and pytest monkeypatch.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from types import ModuleType

import pytest
from flext_tests import tm
from tests import t

from flext_infra import FlextInfraCliDeps, deps


def _fake_module(return_value: t.Infra.InfraValue = 0) -> ModuleType:
    """Create a real ModuleType with a main() returning *return_value*."""
    mod = ModuleType("fake_subcommand")
    setattr(mod, "main", lambda: return_value)
    return mod


def _patch_dispatch(
    mp: pytest.MonkeyPatch,
    argv: t.StrSequence,
    ret: t.Infra.InfraValue = 0,
) -> None:
    """Patch sys.argv and lazy-exported deps modules for dispatch tests."""
    mp.setattr(sys, "argv", argv)
    export_name = FlextInfraCliDeps._SUBCOMMAND_MODULES["detect"].rsplit(
        ".",
        maxsplit=1,
    )[-1]
    mp.setattr(deps, export_name, _fake_module(ret))


class TestSubcommandMapping:
    """Test subcommand mapping completeness."""

    EXPECTED_SUBCOMMAND_MODULES: t.StrMapping = {
        "detect": "flext_infra.deps.detector",
        "extra-paths": "flext_infra.deps.extra_paths",
        "internal-sync": "flext_infra.deps.internal_sync",
        "modernize": "flext_infra.deps.modernizer",
        "path-sync": "flext_infra.deps.path_sync",
    }

    def test_subcommands_count(self) -> None:
        """Test correct number of subcommands."""
        tm.that(len(FlextInfraCliDeps._SUBCOMMAND_MODULES), eq=5)

    @pytest.mark.parametrize(
        ("name", "module"),
        list(EXPECTED_SUBCOMMAND_MODULES.items()),
        ids=list(EXPECTED_SUBCOMMAND_MODULES.keys()),
    )
    def test_subcommand_mapping(self, name: str, module: str) -> None:
        """Test each subcommand maps to correct module."""
        tm.that(
            name in FlextInfraCliDeps._SUBCOMMAND_MODULES,
            eq=True,
            msg=f"Missing subcommand: {name}",
        )
        tm.that(FlextInfraCliDeps._SUBCOMMAND_MODULES[name], eq=module)

    @pytest.mark.parametrize("name", list(EXPECTED_SUBCOMMAND_MODULES.keys()))
    def test_subcommand_module_importable(self, name: str) -> None:
        """Test each subcommand module can be imported."""
        module = getattr(
            deps,
            FlextInfraCliDeps._SUBCOMMAND_MODULES[name].rsplit(".", maxsplit=1)[-1],
        )
        tm.that(hasattr(module, "main"), eq=True, msg=f"{name} module has no main()")


class TestMainHelpAndErrors:
    """Test main function help and error handling."""

    def test_main_with_help_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with -h flag returns 0."""
        monkeypatch.setattr(sys, "argv", ["prog", "-h"])
        tm.that(FlextInfraCliDeps.run(), eq=0)

    def test_main_with_no_arguments(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with no arguments returns 0 after help."""
        monkeypatch.setattr(sys, "argv", ["prog"])
        result = FlextInfraCliDeps.run()
        tm.that(result, eq=0)

    def test_main_with_unknown_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test main with unknown subcommand returns parser exit code."""
        monkeypatch.setattr(sys, "argv", ["prog", "unknown"])
        tm.that(FlextInfraCliDeps.run(), eq=2)


class TestMainReturnValues:
    """Test main function return value normalization."""

    @pytest.mark.parametrize(
        ("return_val", "expected"),
        [
            (0, 0),
            (None, 0),
            (False, 0),
            (42, 42),
            (True, 1),
        ],
        ids=["zero", "none", "false", "nonzero", "true"],
    )
    def test_return_value_normalization(
        self,
        monkeypatch: pytest.MonkeyPatch,
        return_val: t.Infra.InfraValue,
        expected: int,
    ) -> None:
        """Test _main_impl normalizes subcommand return values."""
        _patch_dispatch(monkeypatch, ["prog", "detect", "--workspace", "."], return_val)
        result = FlextInfraCliDeps.run()
        tm.that(result, eq=expected)
