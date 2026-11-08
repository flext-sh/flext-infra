# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/scaffold
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsCodegenScaffold:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CensusViolation(
        FlextInfraProtocolsMixins.RequiredNonNegativeLineMixin, Protocol
    ):
        """Structural data contract projected from the owning model."""

        module: t.NonEmptyStr
        rule: t.NonEmptyStr
        message: t.NonEmptyStr
        fixable: bool

    @runtime_checkable
    class CensusReport(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        violations: Sequence[FlextInfraProtocolsCodegenScaffold.CensusViolation]
        total: t.NonNegativeInt
        fixable: t.NonNegativeInt

    @runtime_checkable
    class ScaffoldResult(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        files_created: Sequence[str]
        files_skipped: Sequence[str]

    @runtime_checkable
    class ScaffoldDirRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        target_dir: Path
        prefix: str
        modules: tuple[tuple[str, str, str, str], ...]
        test_prefix: str
        base_module: t.NonEmptyStr
        project_module: t.NonEmptyStr
        test_module: bool
        dry_run: bool
        files_created: MutableSequence[str]
        files_skipped: MutableSequence[str]


__all__: list[str] = [
    "FlextInfraProtocolsCodegenScaffold",
]
