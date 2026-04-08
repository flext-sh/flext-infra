"""Tests for centralized deps dispatch, structlog, argv, and imports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import MutableSequence
from types import ModuleType

import pytest
from flext_tests import tm
from tests import t

from flext_infra import FlextInfraCliDeps, deps


def _fake_module(return_value: t.Infra.InfraValue = 0) -> ModuleType:
    mod = ModuleType("fake_subcommand")
    setattr(mod, "main", lambda: return_value)
    return mod


def _subcommand_name(argv: t.StrSequence) -> str:
    cli_args = list(argv[1:])
    index = FlextInfraCliDeps._find_subcommand_index(cli_args)
    if index is None:
        msg = "missing deps subcommand in argv"
        raise ValueError(msg)
    return cli_args[index]


def _patch_subcommand(
    mp: pytest.MonkeyPatch,
    *,
    argv: t.StrSequence,
    module: ModuleType,
) -> None:
    subcommand = _subcommand_name(argv)
    export_name = FlextInfraCliDeps._SUBCOMMAND_MODULES[subcommand].rsplit(
        ".",
        maxsplit=1,
    )[-1]
    mp.setattr(sys, "argv", argv)
    mp.setattr(deps, export_name, module)


def _patch_dispatch(
    mp: pytest.MonkeyPatch,
    argv: t.StrSequence,
    ret: t.Infra.InfraValue = 0,
) -> None:
    _patch_subcommand(
        mp,
        argv=argv,
        module=_fake_module(ret),
    )


class TestMainSubcommandDispatch:
    @pytest.mark.parametrize(
        "name",
        list(FlextInfraCliDeps._SUBCOMMAND_MODULES.keys()),
    )
    def test_dispatch_each_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
        name: str,
    ) -> None:
        _patch_dispatch(monkeypatch, ["prog", name, "--workspace", "."])
        tm.that(FlextInfraCliDeps.run(), eq=0)


class TestMainModuleImport:
    @pytest.mark.parametrize(
        ("subcommand", "expected_module"),
        [
            ("detect", "flext_infra.deps.detector"),
            ("modernize", "flext_infra.deps.modernizer"),
            ("path-sync", "flext_infra.deps.path_sync"),
        ],
    )
    def test_imports_correct_module(
        self,
        monkeypatch: pytest.MonkeyPatch,
        subcommand: str,
        expected_module: str,
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", subcommand, "--workspace", "."])
        called: MutableSequence[str] = []
        export_name = expected_module.rsplit(".", maxsplit=1)[-1]
        fake = ModuleType(export_name)

        def _main() -> int:
            called.append(export_name)
            return 0

        setattr(fake, "main", _main)
        monkeypatch.setattr(deps, export_name, fake)
        FlextInfraCliDeps.run()
        tm.that(called[0], eq=export_name)


class TestMainSysArgvModification:
    def test_modifies_sys_argv_for_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_dispatch(monkeypatch, ["prog", "detect", "--arg1", "value1"])
        FlextInfraCliDeps.run()
        tm.that(sys.argv[0], has="detect")

    def test_passes_remaining_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_dispatch(monkeypatch, ["prog", "detect", "-q", "--no-fail"])
        FlextInfraCliDeps.run()
        tm.that(sys.argv, has="-q")
        tm.that(sys.argv, has="--no-fail")

    def test_preserves_shared_flags_before_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_dispatch(
            monkeypatch,
            ["prog", "--workspace", ".", "--projects", "flext-core", "detect"],
        )
        FlextInfraCliDeps.run()
        tm.that(sys.argv, has="--workspace")
        tm.that(sys.argv, has=".")
        tm.that(sys.argv, has="--projects")
        tm.that(sys.argv, has="flext-core")


class TestMainDelegation:
    def test_main_alias_runs_help_path(self) -> None:
        tm.that(FlextInfraCliDeps.run(["--help"]), eq=0)


class TestMainExceptionHandling:
    def test_subcommand_exception_propagates(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        error_mod = ModuleType("error_mod")

        def raise_error() -> int:
            msg = "Test error"
            raise RuntimeError(msg)

        setattr(error_mod, "main", raise_error)
        _patch_subcommand(
            monkeypatch,
            argv=["prog", "detect", "--workspace", "."],
            module=error_mod,
        )
        tm.that(FlextInfraCliDeps.run(), eq=1)


def test_string_zero_return_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test string '0' return value normalization (edge case)."""
    _patch_dispatch(monkeypatch, ["prog", "detect", "--workspace", "."], "0")
    tm.that(FlextInfraCliDeps.run(), eq=0)
