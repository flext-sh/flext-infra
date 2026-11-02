# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import c, p, t


class FlextInfraProtocolsRefactorAstGrep:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class CodemodRule(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...

        @property
        def digest(self) -> t.NonEmptyStr: ...

        @property
        def provider(self) -> t.NonEmptyStr: ...

        @property
        def resource(self) -> Path: ...

        @property
        def fixable(self) -> bool: ...

        @property
        def owned_path_suffix(self) -> Literal[".pyi"] | None: ...

        @property
        def message(self) -> str: ...

        @property
        def module_absence(self) -> bool: ...

        @property
        def expected(self) -> int | None: ...

        @property
        def owner(self) -> t.NonEmptyStr | None: ...

        @property
        def consumers_of(self) -> t.NonEmptyStr | None: ...

        @property
        def enforce(self) -> t.Infra.EnforcementIds: ...

        @property
        def disabled(self) -> bool: ...

        @property
        def partitioned(self) -> bool: ...

        @property
        def partition_of(self) -> t.NonEmptyStr | None: ...

        @property
        def relocation(self) -> c.Infra.CodemodRelocation | None: ...

    @runtime_checkable
    class CodemodRuleset(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def provider(self) -> t.NonEmptyStr: ...

        @property
        def config(self) -> Path: ...

        @property
        def rule_ids(self) -> Sequence[str]: ...

        @property
        def fixable_rule_ids(self) -> Sequence[str]: ...

    @runtime_checkable
    class CodemodRulePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def provider_order(self) -> Sequence[str]: ...

        @property
        def rules(self) -> tuple[p.Infra.CodemodRule, ...]: ...

        @property
        def rulesets(self) -> tuple[p.Infra.CodemodRuleset, ...]: ...

        @property
        def project_rule_ids(self) -> Mapping[Path, Sequence[str]]: ...

    @runtime_checkable
    class CodemodPackageExportsFacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def exports(self) -> Mapping[str, t.StrTuple]: ...

        @property
        def directories(self) -> Mapping[str, str]: ...

        @property
        def modules(self) -> Mapping[str, t.StrTuple]: ...

    @runtime_checkable
    class CodemodNativeGenerated(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def utilities(self) -> Mapping[str, t.JsonMapping]: ...

        @property
        def rules(self) -> Mapping[str, t.JsonMapping]: ...

        @property
        def scopes(self) -> Mapping[str, t.StrTuple]: ...

    @runtime_checkable
    class CodemodPrimitiveOwner(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def arg(self) -> tuple[str, str]: ...

    @runtime_checkable
    class CodemodScopePartition(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_id(self) -> t.NonEmptyStr: ...

        @property
        def variable(self) -> t.NonEmptyStr: ...

        @property
        def holds(self) -> bool: ...

        @property
        def selectors(self) -> t.NonEmptyStr: ...

        @property
        def pattern(self) -> t.NonEmptyStr: ...

        @property
        def keys(self) -> Mapping[str, str]: ...

        @property
        def matching(self) -> bool: ...

    @runtime_checkable
    class CodemodScopeFacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scopes(self) -> Mapping[str, t.StrTuple]: ...

    @runtime_checkable
    class AccessorMigrationRule(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_name(self) -> t.NonEmptyStr: ...

        @property
        def replacement_name(self) -> t.NonEmptyStr: ...

        @property
        def reason(self) -> t.NonEmptyStr: ...

        @property
        def origin(self) -> str: ...

        @property
        def operation(self) -> Literal["rename", "normalize-field"]: ...

        @property
        def declaring_class(self) -> t.NonEmptyStr | None: ...

        @property
        def field(self) -> t.NonEmptyStr | None: ...

    @runtime_checkable
    class AccessorMigrationChange(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> t.NonEmptyStr: ...

        @property
        def line(self) -> t.NonNegativeInt: ...

        @property
        def original_name(self) -> t.NonEmptyStr: ...

        @property
        def replacement_name(self) -> str: ...

        @property
        def automated(self) -> bool: ...

        @property
        def reason(self) -> str: ...


__all__: list[str] = [
    "FlextInfraProtocolsRefactorAstGrep",
]
