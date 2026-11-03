# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/scaffold
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t
from flext_infra._protocols import FlextInfraProtocolsMixins


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

        @property
        def violations(
            self,
        ) -> Sequence[FlextInfraProtocolsCodegenScaffold.CensusViolation]:
            """Detected violations."""
            ...

        @property
        def total(self) -> t.NonNegativeInt:
            """Total violation count."""
            ...

        @property
        def fixable(self) -> t.NonNegativeInt:
            """Count of auto-fixable violations."""
            ...

    @runtime_checkable
    class ScaffoldResult(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        files_created: Sequence[str]
        files_skipped: Sequence[str]

    @runtime_checkable
    class ScaffoldDirRequest(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target_dir(self) -> Path:
            """Directory to scaffold."""
            ...

        @property
        def prefix(self) -> str:
            """Generated class name prefix."""
            ...

        @property
        def modules(self) -> tuple[tuple[str, str, str, str], ...]:
            """Module skeleton definitions."""
            ...

        @property
        def test_prefix(self) -> str:
            """Generated test class prefix."""
            ...

        @property
        def base_module(self) -> t.NonEmptyStr:
            """Explicit module owning every generated base class."""
            ...

        @property
        def project_module(self) -> t.NonEmptyStr:
            """Owning package imported by generated test modules."""
            ...

        @property
        def test_module(self) -> bool:
            """Whether this directory renders test module skeletons."""
            ...

        @property
        def dry_run(self) -> bool:
            """Whether to report creations without writing."""
            ...

        @property
        def files_created(self) -> MutableSequence[str]:
            """Created file accumulator."""
            ...

        @property
        def files_skipped(self) -> MutableSequence[str]:
            """Skipped file accumulator."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenScaffold",
]
