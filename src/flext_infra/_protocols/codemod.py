# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import c, t


class FlextInfraProtocolsCodemod:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class RopeSignatureAddition(Protocol):
        """Structural data contract projected from the owning model."""

        id: t.NonEmptyStr
        target: t.NonEmptyStr
        parameter: t.NonEmptyStr
        annotation: t.NonEmptyStr
        default: str | None = ...
        call_values: Mapping[str, str]

    @runtime_checkable
    class RopeSignatureRemoval(Protocol):
        """Structural data contract projected from the owning model."""

        id: t.NonEmptyStr
        target: t.NonEmptyStr
        parameter: t.NonEmptyStr
        replacement: t.NonEmptyStr

    @runtime_checkable
    class RopeMethodTransfer(Protocol):
        """Structural data contract projected from the owning model."""

        id: t.NonEmptyStr
        destination: Sequence[t.NonEmptyStr]
        methods: Sequence[Sequence[t.NonEmptyStr]]
        receiver_rewrites: Mapping[str, str] = ...

    @runtime_checkable
    class ContractAdmissionOptions(Protocol):
        """Structural data contract projected from the owning model."""

        annotation_only: bool = ...
        class_alias_only: bool = ...
        signature_additions: Sequence[
            FlextInfraProtocolsCodemod.RopeSignatureAddition
        ] = ...
        method_transfers: Sequence[FlextInfraProtocolsCodemod.RopeMethodTransfer] = ...
        signature_removals: Sequence[
            FlextInfraProtocolsCodemod.RopeSignatureRemoval
        ] = ...

    @runtime_checkable
    class AstGrepCapture(Protocol):
        """Structural data contract projected from the owning model."""

        text: str
        start_byte: int
        end_byte: int

    @runtime_checkable
    class CodemodBindingSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        states: tuple[p.Cli.AtomicFileState, ...]

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
        origin: c.Infra.ModFindingOrigin = ...

    @runtime_checkable
    class FamilyFlattenRule(Protocol):
        """Structural data contract projected from the owning model."""

        id: t.NonEmptyStr
        operation: c.Infra.FamilyFlattenOperation
        collision: c.Infra.FamilyCollisionPolicy

    @runtime_checkable
    class RopeContractOrigin(Protocol):
        """Structural data contract projected from the owning model."""

        owner_root: Path | None = ...

    @runtime_checkable
    class RopeContractScopeTarget(Protocol):
        """Structural data contract projected from the owning model."""

        distribution: t.NonEmptyStr
        module: t.NonEmptyStr

    @runtime_checkable
    class RopeContractScope(Protocol):
        """Structural data contract projected from the owning model."""

        targets: Sequence[FlextInfraProtocolsCodemod.RopeContractScopeTarget]

    @runtime_checkable
    class RopeContractRule(Protocol):
        """Structural data contract projected from the owning model."""

        owner_root: Path | None = ...
        id: t.NonEmptyStr
        operation: t.DocumentInput[c.Infra.RopeContractOperation] = ...
        source_revision: t.NonEmptyStr | None = ...
        scope: FlextInfraProtocolsCodemod.RopeContractScope | None = ...
        annotation_only: bool = ...
        annotation_member_source: t.NonEmptyStr | None = ...
        phase: t.DocumentInput[c.Infra.SemanticCutoverPhase] = ...
        pattern: t.NonEmptyStr
        goal: t.NonEmptyStr
        arguments: Mapping[str, str | Sequence[str]]
        imports: Mapping[str, str] = ...
        bindings: Mapping[str, str] = ...
        model_bases: t.DocumentInput[tuple[str, ...]] = ...
        unshadowed_builtins: t.DocumentInput[tuple[str, ...]] = ...
        repeats: t.NonEmptyStr | None = ...
        readonly_contract: t.NonEmptyStr | None = ...
        deferred_contract: t.NonEmptyStr | None = ...
        readonly_origins: t.DocumentInput[tuple[str, ...]] = ...
        drops: t.DocumentInput[tuple[str, ...]] = ...
        reorders_annotation: bool = ...
        families: t.DocumentInput[tuple[str, ...]] = ...
        scope_kinds: t.DocumentInput[
            tuple[t.DocumentInput[c.Infra.RopeScopeKind], ...]
        ] = ...
        implementation_owner: (
            t.DocumentInput[tuple[t.NonEmptyStr, t.NonEmptyStr]] | None
        ) = ...
        receiver_methods: t.DocumentInput[tuple[str, ...]] = ...
        call_target: t.NonEmptyStr | None = ...
        explicit_arguments: bool = ...
        required_field: bool = ...
        defaulted_field: bool = ...
        private_attribute: bool = ...
        value_default: t.NonEmptyStr | None = ...
        factory_default: t.NonEmptyStr | None = ...
        missing_keywords: t.DocumentInput[tuple[str, ...]] = ...
        ownership_transfer: (
            t.DocumentInput[tuple[t.NonEmptyStr, t.NonEmptyStr]] | None
        ) = ...

    @runtime_checkable
    class RopeContractRules(Protocol):
        """Structural data contract projected from the owning model."""

        rules: Sequence[FlextInfraProtocolsCodemod.RopeContractRule]
        signature_additions: Sequence[
            FlextInfraProtocolsCodemod.RopeSignatureAddition
        ] = ...
        method_transfers: Sequence[FlextInfraProtocolsCodemod.RopeMethodTransfer] = ...
        signature_removals: Sequence[
            FlextInfraProtocolsCodemod.RopeSignatureRemoval
        ] = ...

    @runtime_checkable
    class ModFixtureDirectories(Protocol):
        """Structural data contract projected from the owning model."""

        rule_dirs: tuple[Path, ...] = ...
        util_dirs: tuple[Path, ...] = ...
        test_dirs: tuple[Path, ...] = ...

    @runtime_checkable
    class ModRuleBatch(Protocol):
        """Structural data contract projected from the owning model."""

        inline_rules: t.NonEmptyStr
        rule_count: t.PositiveInt
        all_ids: frozenset[str]
        fixable_ids: frozenset[str]


__all__: list[str] = [
    "FlextInfraProtocolsCodemod",
]
