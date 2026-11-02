# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import c, t


class FlextInfraProtocolsRefactorAstGrep:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class CodemodRule(Protocol):
        """Structural data contract projected from the owning model."""

        id: t.NonEmptyStr
        digest: t.NonEmptyStr
        provider: t.NonEmptyStr
        resource: Path
        fixable: bool
        owned_path_suffix: Literal[".pyi"] | None = ...
        message: str = ...
        module_absence: bool = ...
        expected: int | None = ...
        owner: t.NonEmptyStr | None = ...
        consumers_of: t.NonEmptyStr | None = ...
        enforce: t.Infra.EnforcementIds = ...
        disabled: bool = ...
        partitioned: bool = ...
        partition_of: t.NonEmptyStr | None = ...
        relocation: c.Infra.CodemodRelocation | None = ...

    @runtime_checkable
    class CodemodRuleset(Protocol):
        """Structural data contract projected from the owning model."""

        provider: t.NonEmptyStr
        config: Path
        rule_ids: Sequence[str]
        fixable_rule_ids: Sequence[str]

    @runtime_checkable
    class CodemodRulePlan(Protocol):
        """Structural data contract projected from the owning model."""

        provider_order: Sequence[str]
        rules: tuple[FlextInfraModelsRefactorGrep.CodemodRule, ...]
        rulesets: tuple[FlextInfraModelsRefactorGrep.CodemodRuleset, ...]
        project_rule_ids: Mapping[Path, Sequence[str]]

    @runtime_checkable
    class CodemodPackageExportsFacts(Protocol):
        """Structural data contract projected from the owning model."""

        exports: Mapping[str, t.StrTuple]
        directories: Mapping[str, str]
        modules: Mapping[str, t.StrTuple]

    @runtime_checkable
    class CodemodNativeGenerated(Protocol):
        """Structural data contract projected from the owning model."""

        utilities: Mapping[str, t.JsonMapping]
        rules: Mapping[str, t.JsonMapping]
        scopes: Mapping[str, t.StrTuple]

    @runtime_checkable
    class CodemodPrimitiveOwner(Protocol):
        """Structural data contract projected from the owning model."""

        arg: tuple[str, str]

    @runtime_checkable
    class CodemodScopePartition(Protocol):
        """Structural data contract projected from the owning model."""

        rule_id: t.NonEmptyStr
        variable: t.NonEmptyStr
        holds: bool
        selectors: t.NonEmptyStr
        pattern: t.NonEmptyStr = ...
        keys: Mapping[str, str] = ...
        matching: bool = ...

    @runtime_checkable
    class CodemodScopeFacts(Protocol):
        """Structural data contract projected from the owning model."""

        scopes: Mapping[str, t.StrTuple]

    @runtime_checkable
    class AccessorMigrationRule(Protocol):
        """Structural data contract projected from the owning model."""

        source_name: t.NonEmptyStr
        replacement_name: t.NonEmptyStr
        reason: t.NonEmptyStr
        origin: str = ...
        operation: Literal["rename", "normalize-field"] = ...
        declaring_class: t.NonEmptyStr | None = ...
        field: t.NonEmptyStr | None = ...

    @runtime_checkable
    class AccessorMigrationChange(Protocol):
        """Structural data contract projected from the owning model."""

        file: t.NonEmptyStr
        line: t.NonNegativeInt
        original_name: t.NonEmptyStr
        replacement_name: str = ...
        automated: bool
        reason: str


__all__: list[str] = [
    "FlextInfraProtocolsRefactorAstGrep",
]
