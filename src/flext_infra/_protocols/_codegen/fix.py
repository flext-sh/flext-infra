# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/fix
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, MutableSet, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsCodegenFix:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class AutoFixResult(Protocol):
        """Structural data contract projected from the owning model."""

        project: t.NonEmptyStr
        violations_fixed: MutableSequence[p.Infra.CensusViolation]
        violations_skipped: MutableSequence[p.Infra.CensusViolation]
        files_modified: Sequence[str]

    @runtime_checkable
    class ConsolidatorFileResult(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> t.NonEmptyStr: ...
        @property
        def status(self) -> Literal["applied", "reverted"]: ...
        @property
        def changes(self) -> Sequence[str]: ...

    @runtime_checkable
    class ConsolidatorReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def total_found(self) -> t.NonNegativeInt: ...
        @property
        def total_applied(self) -> t.NonNegativeInt: ...
        @property
        def total_failed(self) -> t.NonNegativeInt: ...
        @property
        def files(self) -> Sequence[p.Infra.ConsolidatorFileResult]: ...

    @runtime_checkable
    class FacadeFamily(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def letter(self) -> t.NonEmptyStr: ...
        @property
        def module(self) -> t.NonEmptyStr: ...
        @property
        def suffix(self) -> t.NonEmptyStr: ...
        @property
        def directory(self) -> str: ...
        @property
        def directories(self) -> frozenset[str]: ...
        @property
        def file_names(self) -> frozenset[str]: ...

    @runtime_checkable
    class NamespaceModulePolicy(Protocol):
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
    class FixContext(Protocol):
        """Structural data contract projected from the owning model."""

        violations_fixed: MutableSequence[p.Infra.CensusViolation]
        violations_skipped: MutableSequence[p.Infra.CensusViolation]
        files_modified: MutableSet[str]

    @runtime_checkable
    class ViolationKey(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def module(self) -> str: ...
        @property
        def rule(self) -> str: ...
        @property
        def content_hash(self) -> str: ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenFix",
]
