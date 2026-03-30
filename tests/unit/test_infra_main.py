"""Tests for the centralized flext_infra CLI entrypoint.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.cli import FlextInfraCli, main


def test_main_returns_error_when_no_args() -> None:
    assert main([]) == 1


def test_main_help_flag_returns_zero() -> None:
    assert main(["--help"]) == 0


def test_main_unknown_group_returns_error() -> None:
    assert main(["unknown"]) == 1


def test_main_all_groups_defined() -> None:
    expected_groups = {
        "basemk",
        "check",
        "codegen",
        "validate",
        "deps",
        "docs",
        "github",
        "maintenance",
        "refactor",
        "release",
        "workspace",
    }
    assert set(FlextInfraCli.GROUPS.keys()) == expected_groups


def test_main_group_descriptions_are_present() -> None:
    for group, description in FlextInfraCli.GROUPS.items():
        assert isinstance(description, str)
        assert description
        assert group
