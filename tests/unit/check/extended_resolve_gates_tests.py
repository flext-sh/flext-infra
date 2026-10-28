"""Tests for workspace checker gate resolution and CSV parsing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from tests import c, tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraWorkspaceCheckerResolveGates:
    """Test FlextInfraWorkspaceChecker.resolve_gates."""

    @staticmethod
    def test_resolve_gates_type_is_rejected(tmp_path: Path) -> None:
        """Test resolve gates type is rejected."""
        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).resolve_gates([
            "type"
        ])
        tm.fail(result, has="unknown gate")

    @staticmethod
    def test_resolve_gates_rejects_empty_strings(tmp_path: Path) -> None:
        """Test resolve gates rejects empty strings."""
        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).resolve_gates([
            "lint",
            "",
            "format",
        ])
        tm.fail(result, has="invalid gate name")

    @staticmethod
    def test_resolve_gates_rejects_duplicate_entries(tmp_path: Path) -> None:
        """Test resolve gates rejects duplicate entries."""
        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).resolve_gates([
            "lint",
            "lint",
            "format",
            "lint",
        ])
        tm.fail(result, has="duplicate gate")

    @staticmethod
    def test_resolve_gates_invalid_gate_fails(tmp_path: Path) -> None:
        """Test resolve gates invalid gate fails."""
        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).resolve_gates([
            "invalid"
        ])
        tm.fail(result, has="unknown gate")

    @staticmethod
    def test_resolve_gates_accepts_every_declared_gate(tmp_path: Path) -> None:
        """Test resolve gates accepts every declared gate."""
        gates = sorted(c.Infra.ALLOWED_GATES)
        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).resolve_gates(
            gates
        )
        tm.ok(result)
        tm.that(sorted(result.value), eq=gates)
