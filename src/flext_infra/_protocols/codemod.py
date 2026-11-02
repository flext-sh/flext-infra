# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/codemod
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsCodemod:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class RopeSignatureAddition(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def target(self) -> t.NonEmptyStr: ...
        @property
        def parameter(self) -> t.NonEmptyStr: ...
        @property
        def annotation(self) -> t.NonEmptyStr: ...
        @property
        def default(self) -> str | None: ...
        @property
        def call_values(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class RopeSignatureRemoval(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def target(self) -> t.NonEmptyStr: ...
        @property
        def parameter(self) -> t.NonEmptyStr: ...
        @property
        def replacement(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class RopeMethodTransfer(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def destination(self) -> Sequence[t.NonEmptyStr]: ...
        @property
        def methods(self) -> Sequence[Sequence[t.NonEmptyStr]]: ...
        @property
        def receiver_rewrites(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class ContractAdmissionOptions(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def annotation_only(self) -> bool: ...
        @property
        def class_alias_only(self) -> bool: ...
        @property
        def signature_additions(self) -> Sequence[p.Infra.RopeSignatureAddition]: ...
        @property
        def method_transfers(self) -> Sequence[p.Infra.RopeMethodTransfer]: ...
        @property
        def signature_removals(self) -> Sequence[p.Infra.RopeSignatureRemoval]: ...

    @runtime_checkable
    class AstGrepCapture(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def text(self) -> str: ...
        @property
        def start_byte(self) -> int: ...
        @property
        def end_byte(self) -> int: ...

    @runtime_checkable
    class CodemodBindingSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def states(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class AstGrepDiagnostic(Protocol):
        """Structural data contract projected from the owning model."""

        file: str
        rule_id: str
        severity: c.Infra.NativeRuleSeverity
        message: str
        text: str
        lines: str
        line: int
        column: int
        end_line: int
        end_column: int
        start_byte: int
        end_byte: int

    @runtime_checkable
    class AstGrepOwnedPathDiagnostic(Protocol):
        """Structural data contract projected from the owning model."""

        file: str
        rule_id: str
        severity: c.Infra.NativeRuleSeverity
        message: str
        text: str
        lines: str
        line: int
        column: int
        end_line: int
        end_column: int
        start_byte: int
        end_byte: int
        origin: c.Infra.ModFindingOrigin

    @runtime_checkable
    class AstGrepReport(Protocol):
        """Structural data contract projected from the owning model."""

        root: tuple[AstGrepDiagnostic, ...]

    @runtime_checkable
    class FamilyFlattenRule(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def operation(self) -> c.Infra.FamilyFlattenOperation: ...
        @property
        def collision(self) -> c.Infra.FamilyCollisionPolicy: ...

    @runtime_checkable
    class RopeContractOrigin(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner_root(self) -> Path | None: ...

    @runtime_checkable
    class RopeContractScopeTarget(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr: ...
        @property
        def module(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class RopeContractScope(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def targets(self) -> Sequence[p.Infra.RopeContractScopeTarget]: ...

    @runtime_checkable
    class RopeContractRule(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner_root(self) -> Path | None: ...
        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def operation(self) -> c.Infra.RopeContractOperation: ...
        @property
        def source_revision(self) -> t.NonEmptyStr | None: ...
        @property
        def scope(self) -> p.Infra.RopeContractScope | None: ...
        @property
        def annotation_only(self) -> bool: ...
        @property
        def annotation_member_source(self) -> t.NonEmptyStr | None: ...
        @property
        def phase(self) -> c.Infra.SemanticCutoverPhase: ...
        @property
        def pattern(self) -> t.NonEmptyStr: ...
        @property
        def goal(self) -> t.NonEmptyStr: ...
        @property
        def arguments(self) -> Mapping[str, str | Sequence[str]]: ...
        @property
        def imports(self) -> Mapping[str, str]: ...
        @property
        def bindings(self) -> Mapping[str, str]: ...
        @property
        def model_bases(self) -> tuple[str, ...]: ...
        @property
        def unshadowed_builtins(self) -> tuple[str, ...]: ...
        @property
        def repeats(self) -> t.NonEmptyStr | None: ...
        @property
        def readonly_contract(self) -> t.NonEmptyStr | None: ...
        @property
        def deferred_contract(self) -> t.NonEmptyStr | None: ...
        @property
        def readonly_origins(self) -> tuple[str, ...]: ...
        @property
        def drops(self) -> tuple[str, ...]: ...
        @property
        def reorders_annotation(self) -> bool: ...
        @property
        def families(self) -> tuple[str, ...]: ...
        @property
        def scope_kinds(self) -> tuple[c.Infra.RopeScopeKind, ...]: ...
        @property
        def implementation_owner(
            self,
        ) -> tuple[t.NonEmptyStr, t.NonEmptyStr] | None: ...
        @property
        def receiver_methods(self) -> tuple[str, ...]: ...
        @property
        def call_target(self) -> t.NonEmptyStr | None: ...
        @property
        def explicit_arguments(self) -> bool: ...
        @property
        def required_field(self) -> bool: ...
        @property
        def defaulted_field(self) -> bool: ...
        @property
        def private_attribute(self) -> bool: ...
        @property
        def value_default(self) -> t.NonEmptyStr | None: ...
        @property
        def factory_default(self) -> t.NonEmptyStr | None: ...
        @property
        def missing_keywords(self) -> tuple[str, ...]: ...
        @property
        def ownership_transfer(self) -> tuple[t.NonEmptyStr, t.NonEmptyStr] | None: ...

    @runtime_checkable
    class RopeContractRules(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rules(self) -> Sequence[p.Infra.RopeContractRule]: ...
        @property
        def signature_additions(self) -> Sequence[p.Infra.RopeSignatureAddition]: ...
        @property
        def method_transfers(self) -> Sequence[p.Infra.RopeMethodTransfer]: ...
        @property
        def signature_removals(self) -> Sequence[p.Infra.RopeSignatureRemoval]: ...

    @runtime_checkable
    class ModFixtureDirectories(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_dirs(self) -> tuple[Path, ...]: ...
        @property
        def util_dirs(self) -> tuple[Path, ...]: ...
        @property
        def test_dirs(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class ModRuleBatch(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def inline_rules(self) -> t.NonEmptyStr: ...
        @property
        def rule_count(self) -> t.PositiveInt: ...
        @property
        def all_ids(self) -> frozenset[str]: ...
        @property
        def fixable_ids(self) -> frozenset[str]: ...


__all__: list[str] = [
    "FlextInfraProtocolsCodemod",
]
