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

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t


class FlextInfraProtocolsCodemod:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class RopeSignatureAddition(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Stable addition identity."""
            ...

        @property
        def target(self) -> t.NonEmptyStr:
            """Native qualified function declaration."""
            ...

        @property
        def parameter(self) -> t.NonEmptyStr:
            """Required keyword parameter name."""
            ...

        @property
        def annotation(self) -> t.NonEmptyStr:
            """Origin-owned annotation expression."""
            ...

        @property
        def default(self) -> str | None:
            """Native default expression; absent requires every caller value."""
            ...

        @property
        def call_values(self) -> Mapping[str, str]:
            """Caller declaration identity to argument expression."""
            ...

    @runtime_checkable
    class RopeSignatureRemoval(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Stable operation identity."""
            ...

        @property
        def target(self) -> t.NonEmptyStr:
            """Native qualified function declaration."""
            ...

        @property
        def parameter(self) -> t.NonEmptyStr:
            """Existing parameter to retire."""
            ...

        @property
        def replacement(self) -> t.NonEmptyStr:
            """Explicit native body expression."""
            ...

    @runtime_checkable
    class RopeMethodTransfer(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Stable transfer identity."""
            ...

        @property
        def destination(self) -> Sequence[t.NonEmptyStr]:
            """Destination module and existing qualified class."""
            ...

        @property
        def methods(self) -> Sequence[Sequence[t.NonEmptyStr]]:
            """Source module and qualified method pairs."""
            ...

        @property
        def receiver_rewrites(self) -> Mapping[str, str]:
            """Structural member projected from the owning model.

            Explicit self.member to injected receiver path for one instance method.
            """
            ...

    @runtime_checkable
    class ContractAdmissionOptions(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def annotation_only(self) -> bool:
            """Limit admission to annotation-only contracts."""
            ...

        @property
        def class_alias_only(self) -> bool:
            """Limit admission to class-alias contracts."""
            ...

        @property
        def signature_additions(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeSignatureAddition]:
            """Native additions in this same source pass."""
            ...

        @property
        def method_transfers(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeMethodTransfer]:
            """Native transfers in this same source pass."""
            ...

        @property
        def signature_removals(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeSignatureRemoval]:
            """Native body and parameter retirements."""
            ...

    @runtime_checkable
    class AstGrepCapture(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def text(self) -> str:
            """Exact captured source text."""
            ...

        @property
        def start_byte(self) -> int:
            """Inclusive UTF-8 byte offset."""
            ...

        @property
        def end_byte(self) -> int:
            """Exclusive UTF-8 byte offset."""
            ...

    @runtime_checkable
    class CodemodBindingSnapshot(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def states(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Consumer and resolved Python import-owner inputs."""
            ...

    @runtime_checkable
    class AstGrepDiagnostic(FlextCliProtocols.BaseModel, Protocol):
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
    class AstGrepOwnedPathDiagnostic(AstGrepDiagnostic, Protocol):
        """Structural data contract projected from the owning model."""

        origin: c.Infra.ModFindingOrigin

    @runtime_checkable
    class AstGrepReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> tuple[FlextInfraProtocolsCodemod.AstGrepDiagnostic, ...]:
            """Structural member projected from the owning model."""
            ...

    @runtime_checkable
    class FamilyFlattenRule(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Exact rule receipt identity."""
            ...

        @property
        def operation(self) -> c.Infra.FamilyFlattenOperation:
            """Supported semantic family transformation."""
            ...

        @property
        def collision(self) -> c.Infra.FamilyCollisionPolicy:
            """Member-name collision resolution policy."""
            ...

    @runtime_checkable
    class RopeContractOrigin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner_root(self) -> Path | None:
            """Elected repository root, or None for packaged policy."""
            ...

    @runtime_checkable
    class RopeContractScopeTarget(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr:
            """Canonical PEP 503 distribution identity."""
            ...

        @property
        def module(self) -> t.NonEmptyStr:
            """Exact dotted Python module identity."""
            ...

    @runtime_checkable
    class RopeContractScope(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def targets(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeContractScopeTarget]:
            """Exact distribution/module target pairs."""
            ...

    @runtime_checkable
    class RopeContractRuleTarget(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner_root(self) -> Path | None:
            """Structural member projected from the owning model.

            Project root whose catalogue declares this rule; None for the packaged
            universal policy.
            """
            ...

        @property
        def id(self) -> t.NonEmptyStr:
            """Stable rule identity."""
            ...

        @property
        def operation(self) -> c.Infra.RopeContractOperation:
            """Native contract operation executed in the shared source epoch."""
            ...

        @property
        def scope(self) -> FlextInfraProtocolsCodemod.RopeContractScope | None:
            """Structural member projected from the owning model.

            Closed distribution/module admission set; absent keeps the rule
            universal.
            """
            ...

        @property
        def annotation_only(self) -> bool:
            """Admit matches only inside declared type annotations."""
            ...

        @property
        def annotation_member_source(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Exact source namespace admitted for a proven annotation member move.
            """
            ...

        @property
        def phase(self) -> c.Infra.SemanticCutoverPhase:
            """Existing semantic phase owning this rule's execution."""
            ...

        @property
        def pattern(self) -> t.NonEmptyStr:
            """Native Rope pattern."""
            ...

        @property
        def goal(self) -> str:
            """Native Rope replacement."""
            ...

        @property
        def arguments(self) -> Mapping[str, str | Sequence[str]]:
            """Native Rope identity constraints or admitted alternatives."""
            ...

        @property
        def imports(self) -> Mapping[str, str]:
            """Destination bindings and their native import declarations."""
            ...

        @property
        def bindings(self) -> Mapping[str, str]:
            """Destination expressions and their required Rope identities."""
            ...

    @runtime_checkable
    class RopeContractRuleShape(RopeContractRuleTarget, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def model_bases(self) -> tuple[str, ...]:
            """Required model ancestry for every matched declaration."""
            ...

        @property
        def unshadowed_builtins(self) -> tuple[str, ...]:
            """Native lexical names required to be interpreter builtins."""
            ...

        @property
        def repeats(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Pattern capture the replacement evaluates again; it must hold no
            authored call.
            """
            ...

        @property
        def readonly_contract(self) -> t.NonEmptyStr | None:
            """Capture requiring a proven read-only collection origin."""
            ...

        @property
        def deferred_contract(self) -> t.NonEmptyStr | None:
            """Capture resolved by a canonical typed factory after declaration."""
            ...

        @property
        def readonly_origins(self) -> tuple[str, ...]:
            """Native read-only collection identities admitting the capture."""
            ...

        @property
        def drops(self) -> tuple[str, ...]:
            """Discarded captures that must be inert native constants."""
            ...

        @property
        def reorders_annotation(self) -> bool:
            """Whether the replacement changes annotation evaluation order."""
            ...

        @property
        def families(self) -> tuple[str, ...]:
            """Declared facade families admitting the source module."""
            ...

        @property
        def scope_kinds(self) -> tuple[c.Infra.RopeScopeKind, ...]:
            """Native Rope lexical scopes admitting a match."""
            ...

        @property
        def implementation_owner(self) -> tuple[t.NonEmptyStr, t.NonEmptyStr] | None:
            """Native module and primitive whose backend stays native."""
            ...

    @runtime_checkable
    class RopeContractRule(RopeContractRuleShape, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def receiver_methods(self) -> tuple[str, ...]:
            """Discarded-call interface required of a factory product."""
            ...

        @property
        def call_target(self) -> t.NonEmptyStr | None:
            """Capture admitted as a native callee or required field call."""
            ...

        @property
        def explicit_arguments(self) -> bool:
            """Structural member projected from the owning model.

            Require proven call arguments without positional or keyword expansion.
            """
            ...

        @property
        def required_field(self) -> bool:
            """Require metadata without a field default or factory."""
            ...

        @property
        def defaulted_field(self) -> bool:
            """Extract one concrete field default outside metadata."""
            ...

        @property
        def private_attribute(self) -> bool:
            """Require an unset native private model attribute."""
            ...

        @property
        def value_default(self) -> t.NonEmptyStr | None:
            """Default capture that must not denote a required field."""
            ...

        @property
        def factory_default(self) -> t.NonEmptyStr | None:
            """Factory capture that must not denote an absent factory."""
            ...

        @property
        def missing_keywords(self) -> tuple[str, ...]:
            """Injected keywords whose presence preserves a composition."""
            ...

        @property
        def ownership_transfer(self) -> tuple[t.NonEmptyStr, t.NonEmptyStr] | None:
            """Native module/member retired after receiver transfer."""
            ...

    @runtime_checkable
    class RopeContractRules(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rules(self) -> Sequence[FlextInfraProtocolsCodemod.RopeContractRule]:
            """Ordered, identity-constrained Rope contract rules."""
            ...

        @property
        def signature_additions(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeSignatureAddition]:
            """Ordered native required keyword additions."""
            ...

        @property
        def method_transfers(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeMethodTransfer]:
            """Ordered native method ownership transfers."""
            ...

        @property
        def signature_removals(
            self,
        ) -> Sequence[FlextInfraProtocolsCodemod.RopeSignatureRemoval]:
            """Ordered native parameter retirements."""
            ...

    @runtime_checkable
    class ModFixtureDirectories(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_dirs(self) -> tuple[Path, ...]:
            """Validated rule directories declared by the ast-grep owner."""
            ...

        @property
        def util_dirs(self) -> tuple[Path, ...]:
            """Validated utility directories declared by the ast-grep owner."""
            ...

        @property
        def test_dirs(self) -> tuple[Path, ...]:
            """Validated fixture directories declared by the ast-grep owner."""
            ...

    @runtime_checkable
    class ModRuleBatch(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def inline_rules(self) -> t.NonEmptyStr:
            """Executable YAML document stream."""
            ...

        @property
        def rule_count(self) -> t.PositiveInt:
            """Discovered rule file count."""
            ...

        @property
        def all_ids(self) -> frozenset[str]:
            """Every validated rule ID."""
            ...

        @property
        def fixable_ids(self) -> frozenset[str]:
            """Rule IDs owning an automatic rewrite."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodemod",
]
