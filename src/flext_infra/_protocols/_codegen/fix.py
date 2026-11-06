# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/fix
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSet, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenScaffold


class FlextInfraProtocolsCodegenFix:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class AutoFixResult(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def violations_fixed(
            self,
        ) -> Sequence[FlextInfraProtocolsCodegenScaffold.CensusViolation]:
            """Fixed violations."""
            ...

        @property
        def violations_skipped(
            self,
        ) -> Sequence[FlextInfraProtocolsCodegenScaffold.CensusViolation]:
            """Skipped violations (not auto-fixable)."""
            ...

        files_modified: Sequence[str]

    @runtime_checkable
    class ConsolidatorFileResult(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> t.NonEmptyStr:
            """Workspace-relative file path."""
            ...

        @property
        def status(self) -> Literal["applied", "reverted"]:
            """File processing status."""
            ...

        @property
        def changes(self) -> Sequence[str]:
            """Applied replacements."""
            ...

    @runtime_checkable
    class ConsolidatorReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def total_found(self) -> t.NonNegativeInt:
            """Total replacements found."""
            ...

        @property
        def total_applied(self) -> t.NonNegativeInt:
            """Total replacements applied."""
            ...

        @property
        def total_failed(self) -> t.NonNegativeInt:
            """Total files reverted."""
            ...

        @property
        def files(
            self,
        ) -> Sequence[FlextInfraProtocolsCodegenFix.ConsolidatorFileResult]:
            """Per-file processing results."""
            ...

    @runtime_checkable
    class FacadeFamily(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def letter(self) -> t.NonEmptyStr:
            """Facade letter of the import-layer order."""
            ...

        @property
        def module(self) -> t.NonEmptyStr:
            """Stem of the facade module declaring the letter."""
            ...

        @property
        def suffix(self) -> t.NonEmptyStr:
            """Facade class suffix past the shared class stem."""
            ...

        @property
        def directory(self) -> str:
            """Private family package beside the facade module."""
            ...

        @property
        def directories(self) -> frozenset[str]:
            """Public and private family package directory names."""
            ...

        @property
        def file_names(self) -> frozenset[str]:
            """Public and private facade module file names."""
            ...

    @runtime_checkable
    class NamespaceModulePolicy(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        enforce_contract: bool
        export_symbols: bool
        include_in_lazy_init: bool
        project_prefix: str
        expected_alias: str | None
        expected_family: str | None
        inherited_namespaces: Sequence[str]
        is_internal_namespace: bool
        family_tokens: Sequence[str]
        accepted_suffixes: Sequence[str]
        allow_main_export: bool
        allow_type_alias: bool
        is_fixture_module: bool
        type_checking_imports: Sequence[str]

    @runtime_checkable
    class FixContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def violations_fixed(
            self,
        ) -> Sequence[FlextInfraProtocolsCodegenScaffold.CensusViolation]:
            """List of violations that were fixed."""
            ...

        @property
        def violations_skipped(
            self,
        ) -> Sequence[FlextInfraProtocolsCodegenScaffold.CensusViolation]:
            """List of violations that were skipped."""
            ...

        files_modified: MutableSet[str]

        @property
        def has_changes(self) -> bool:
            """Whether at least one file was modified."""
            ...

        def skip(self, *, module: str, rule: str, line: int, message: str) -> None:
            """Skip."""
            ...

        def fix(self, *, module: str, rule: str, line: int, message: str) -> None:
            """Fix."""
            ...

    @runtime_checkable
    class ViolationKey(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def module(self) -> str:
            """Module containing the violation."""
            ...

        @property
        def rule(self) -> str:
            """Rule that was violated."""
            ...

        @property
        def content_hash(self) -> str:
            """SHA256 of surrounding context lines."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenFix",
]
