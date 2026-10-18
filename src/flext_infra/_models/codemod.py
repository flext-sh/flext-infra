"""Data-only contracts for the canonical AST-grep circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u
from typing_extensions import TypeForm

from flext_infra import c, p, t
from flext_infra._models import FlextInfraModelsBase


class FlextInfraModelsCodemod:
    """Typed contracts for native codemod scans and mutation reports."""

    class AstGrepCapture(FlextInfraModelsBase.FrozenArbitrary):
        """Authenticate an occurrence against native UTF-8 capture coordinates."""

        text: Annotated[str, m.Field(description="Exact captured source text")]
        start_byte: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "byteOffset", "start"),
                description="Inclusive UTF-8 byte offset",
            ),
        ]
        end_byte: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "byteOffset", "end"),
                description="Exclusive UTF-8 byte offset",
            ),
        ]

    class CodemodBindingSnapshot(FlextInfraModelsBase.FrozenArbitrary):
        """Closed descriptor-authenticated sources used by occurrence admission."""

        states: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(description="Consumer and resolved Python import-owner inputs"),
        ]

        @m.field_validator("states")
        @classmethod
        def unique_inputs(
            cls, states: tuple[m.Cli.AtomicFileState, ...]
        ) -> tuple[m.Cli.AtomicFileState, ...]:
            """Store each authenticated input once; conflicting identities fail.

            Returns:
                The resulting ``tuple[m.Cli.AtomicFileState, ...]``.

            Raises:
                ValueError: If binding source snapshots disagree.

            """
            indexed: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
            for state in states:
                previous = indexed.setdefault(state.path, state)
                if previous is not state and previous != state:
                    msg = f"binding source snapshots disagree: {state.path}"
                    raise ValueError(msg)
            return tuple(indexed.values())

    class CodemodSourceEpoch(FlextInfraModelsBase.FrozenArbitrary):
        """One shared authenticated text view for an immutable capture operation."""

        snapshot: FlextInfraModelsCodemod.CodemodBindingSnapshot = m.Field(
            description="Authenticated binding snapshot defining this source epoch"
        )
        sources: MappingProxyType[Path, str] = m.Field(
            description="Immutable decoded text for every present captured input"
        )
        contents: MappingProxyType[Path, bytes] = m.Field(
            description="Immutable original bytes for every present captured input"
        )

        @m.model_validator(mode="after")
        def _validate_sources(self) -> Self:
            expected = {
                state.path
                for state in self.snapshot.states
                if state.content is not None
            }
            if set(self.sources) != expected or set(self.contents) != expected:
                msg = "source epoch must contain every present captured input"
                raise ValueError(msg)
            for state in self.snapshot.states:
                if state.content is not None and (
                    self.contents[state.path] != state.content
                    or self.sources[state.path].encode("utf-8") != state.content
                ):
                    msg = f"source epoch differs from authenticated bytes: {state.path}"
                    raise ValueError(msg)
            return self

    class CodemodBindingProject(m.ArbitraryTypesModel):
        """One selected project's lexical roots within a shared input capture."""

        root: Annotated[Path, m.Field(description="Native project resolution root")]
        source_paths: Annotated[
            tuple[Path, ...],
            m.Field(description="Authenticated consumer paths requiring admission"),
        ]
        modules: Annotated[
            t.StrSequence,
            m.Field(description="Symbol owners elected by this project's findings"),
        ]

    class AstGrepDiagnostic(m.FlexibleModel):
        """Required native RuleMatch fields, with zero-based source coordinates.

        ast-grep may include additional replacement and metavariable metadata;
        the complete payload remains in the gate's raw scanner output.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(strict=True)

        file: Annotated[str, m.Field(min_length=1, description="Reported source path")]
        rule_id: Annotated[
            str,
            m.Field(alias="ruleId", min_length=1, description="Native rule ID"),
        ]
        severity: Annotated[
            Literal["error", "warning", "info", "hint"],
            m.Field(description="Native rule severity"),
        ]
        message: Annotated[str, m.Field(description="Native rule diagnostic")]
        text: Annotated[str, m.Field(description="Exact matched source text")]
        lines: Annotated[str, m.Field(description="Source lines containing the match")]
        line: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "start", "line"),
                description="Zero-based starting source line",
            ),
        ]
        column: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "start", "column"),
                description="Zero-based starting source column",
            ),
        ]
        end_line: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "end", "line"),
                description="Zero-based ending source line",
            ),
        ]
        end_column: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "end", "column"),
                description="Zero-based ending source column",
            ),
        ]
        start_byte: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "byteOffset", "start"),
                description="Inclusive UTF-8 byte offset",
            ),
        ]
        end_byte: Annotated[
            int,
            m.Field(
                ge=0,
                validation_alias=m.AliasPath("range", "byteOffset", "end"),
                description="Exclusive UTF-8 byte offset",
            ),
        ]
        captures: Annotated[
            t.JsonMapping,
            m.Field(
                validation_alias=m.AliasPath("metaVariables", "single"),
                default_factory=lambda: MappingProxyType[str, t.JsonValue]({}),
                description=(
                    "Captured single metavariables; ast-grep omits the payload "
                    "for a match that captures none"
                ),
            ),
        ]
        transformed: Annotated[
            t.JsonMapping,
            m.Field(
                validation_alias=m.AliasPath("metaVariables", "transformed"),
                default_factory=lambda: MappingProxyType[str, t.JsonValue]({}),
                description="Metavariables the rule derived through transform",
            ),
        ]

    class AstGrepReport(m.RootModel[tuple[AstGrepDiagnostic, ...]]):
        """Complete ``ast-grep scan --json=compact`` array; malformed input raises."""

    class FamilyFlattenRule(m.ContractModel):
        """One installed, closed family-shape operation (ADR-017)."""

        id: Annotated[t.NonEmptyStr, m.Field(description="Exact rule receipt identity")]
        operation: Annotated[
            Literal["flatten-single-wrapper"],
            m.Field(description="Supported semantic family transformation"),
        ]
        collision: Annotated[
            Literal["prefix-wrapper"],
            m.Field(description="Member-name collision resolution policy"),
        ]

    class RopeContractRule(m.ContractModel):
        """Identity-constrained native Rope restructuring of a Python contract."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            arbitrary_types_allowed=True
        )
        source_states: t.VariadicTuple[t.Port[p.Infra.SemanticSourceState]] = m.Field(
            default=(), exclude=True, description="Original recipe input receipts"
        )

        id: Annotated[t.NonEmptyStr, m.Field(description="Stable rule identity")]
        phase: c.Infra.SemanticCutoverPhase = m.Field(
            default=c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
            strict=False,
            description="Existing semantic phase owning this rule's execution",
        )
        pattern: Annotated[t.NonEmptyStr, m.Field(description="Native Rope pattern")]
        goal: Annotated[t.NonEmptyStr, m.Field(description="Native Rope replacement")]
        arguments: Annotated[
            t.MappingKV[str, str | t.StrSequence],
            m.Field(
                description="Native Rope identity constraints or admitted alternatives"
            ),
        ]
        imports: t.MappingKV[str, str] = u.Field(
            default_factory=u.empty(TypeForm(t.MappingKV[str, str])),
            description="Destination bindings and their native import declarations",
        )
        bindings: t.MappingKV[str, str] = u.Field(
            default_factory=u.empty(TypeForm(t.MappingKV[str, str])),
            description="Destination expressions and their required Rope identities",
        )
        model_bases: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Required model ancestry for every matched declaration",
        )
        unshadowed_builtins: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Native lexical names required to be interpreter builtins",
        )
        repeats: t.NonEmptyStr | None = m.Field(
            default=None,
            description=(
                "Pattern capture the replacement evaluates again; it must hold "
                "no authored call"
            ),
        )
        drops: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Discarded captures that must be inert native constants",
        )
        reorders_annotation: bool = m.Field(
            default=False,
            description="Whether the replacement changes annotation evaluation order",
        )
        families: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Declared facade families admitting the source module",
        )
        scope_kinds: t.VariadicTuple[
            Annotated[c.Infra.RopeScopeKind, m.Field(strict=False)]
        ] = m.Field(
            default=(),
            description="Native Rope lexical scopes admitting a match",
        )
        implementation_owner: t.Pair[t.NonEmptyStr, t.NonEmptyStr] | None = m.Field(
            default=None,
            description="Native module and public primitive whose backend remains native",
        )
        receiver_methods: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Proven discarded-call interface required of a factory product",
        )
        call_target: t.NonEmptyStr | None = m.Field(
            default=None,
            description="Capture admitted only as the original callee, preserving every argument",
        )
        missing_keywords: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Required injected keywords whose explicit presence preserves an existing composition",
        )
        ownership_transfer: t.Pair[t.NonEmptyStr, t.NonEmptyStr] | None = m.Field(
            default=None,
            description="Project-owned native module/member retired after complete receiver transfer",
        )

        @m.model_validator(mode="after")
        def _validate_call_target(self) -> Self:
            if self.missing_keywords and self.call_target is None:
                msg = "missing-keyword proof requires a call target"
                raise ValueError(msg)
            if (
                self.call_target is not None
                and f"${{{self.call_target}}}" not in self.pattern
            ):
                msg = "call target must name a capture in the native pattern"
                raise ValueError(msg)
            return self

    class RopeContractRules(m.ContractModel):
        """The packaged semantic contract policy, validated once on input."""

        rules: Annotated[
            t.SequenceOf[FlextInfraModelsCodemod.RopeContractRule],
            m.Field(description="Ordered, identity-constrained Rope contract rules"),
        ]

    class ModFixtureDirectories(FlextInfraModelsBase.FrozenArbitrary):
        """Validated physical directories selected by one ast-grep owner."""

        rule_dirs: t.VariadicTuple[Path] = m.Field(
            description="Validated rule directories declared by the ast-grep owner",
        )
        util_dirs: t.VariadicTuple[Path] = m.Field(
            description="Validated utility directories declared by the ast-grep owner",
        )
        test_dirs: t.VariadicTuple[Path] = m.Field(
            description="Validated fixture directories declared by the ast-grep owner",
        )

    class ModRuleBatch(FlextInfraModelsBase.FrozenArbitrary):
        """Validated executable ast-grep documents prepared for one circuit."""

        inline_rules: Annotated[
            t.NonEmptyStr,
            m.Field(description="Executable YAML document stream"),
        ]
        rule_count: Annotated[
            t.PositiveInt,
            m.Field(description="Discovered rule file count"),
        ]
        all_ids: Annotated[
            frozenset[str],
            m.Field(description="Every validated rule ID"),
        ]
        fixable_ids: Annotated[
            frozenset[str],
            m.Field(description="Rule IDs owning an automatic rewrite"),
        ]


__all__: list[str] = ["FlextInfraModelsCodemod"]
