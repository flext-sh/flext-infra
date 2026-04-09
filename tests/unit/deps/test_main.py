"""Tests for centralized deps subcommand dispatch.

Validates subcommand mapping, help/error paths, and return-value
normalization using real imports and pytest monkeypatch.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys

import pytest
from flext_tests import tm
from tests import t

from flext_infra import FlextInfraCliDeps, deps


def _fake_service(return_value: t.Infra.InfraValue = 0) -> type:
    """Create a fake service class exposing the canonical class-level main()."""

    class _FakeService:
        @staticmethod
        def main() -> t.Infra.InfraValue:
            return return_value

    return _FakeService


def _patch_dispatch(
    mp: pytest.MonkeyPatch,
    argv: t.StrSequence,
    ret: t.Infra.InfraValue = 0,
) -> None:
    """Patch sys.argv and lazy-exported deps modules for dispatch tests."""
    mp.setattr(sys, "argv", argv)
    service_name = FlextInfraCliDeps._SUBCOMMAND_SERVICES["detect"]
    mp.setattr(deps, service_name, _fake_service(ret))


class TestSubcommandMapping:
    """Test subcommand mapping completeness."""

    EXPECTED_SUBCOMMAND_SERVICES: t.StrMapping = {
        "detect": "FlextInfraRuntimeDevDependencyDetector",
        "extra-paths": "FlextInfraExtraPathsManager",
        "internal-sync": "FlextInfraInternalDependencySyncService",
        "modernize": "FlextInfraPyprojectModernizer",
        "path-sync": "FlextInfraUtilitiesDependencyPathSync",
    }

    def test_subcommands_count(self) -> None:
        """Test correct number of subcommands."""
        tm.that(len(FlextInfraCliDeps._SUBCOMMAND_SERVICES), eq=5)

    @pytest.mark.parametrize(
        ("name", "module"),
        list(EXPECTED_SUBCOMMAND_SERVICES.items()),
        ids=list(EXPECTED_SUBCOMMAND_SERVICES.keys()),
    )
    def test_subcommand_mapping(self, name: str, service_name: str) -> None:
        """Test each subcommand maps to the correct public service class."""
        tm.that(
            name in FlextInfraCliDeps._SUBCOMMAND_SERVICES,
            eq=True,
            msg=f"Missing subcommand: {name}",
        )
        tm.that(FlextInfraCliDeps._SUBCOMMAND_SERVICES[name], eq=service_name)

    @pytest.mark.parametrize("name", list(EXPECTED_SUBCOMMAND_SERVICES.keys()))
    def test_subcommand_service_importable(self, name: str) -> None:
        """Test each subcommand service is importable and exposes main()."""
        service_cls = getattr(deps, FlextInfraCliDeps._SUBCOMMAND_SERVICES[name])
        tm.that(
            hasattr(service_cls, "main"), eq=True, msg=f"{name} service has no main()"
        )


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
