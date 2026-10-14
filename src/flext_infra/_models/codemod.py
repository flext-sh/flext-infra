"""Data-only contracts for the canonical AST-grep circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m
from typing_extensions import TypeForm

from flext_core import u
from flext_infra import c, t


class FlextInfraModelsCodemod:
    """Typed contracts for native codemod scans and mutation reports."""

    class AstGrepCapture(m.ContractModel):
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

    class CodemodBindingSnapshot(m.ArbitraryTypesModel):
        """Closed descriptor-authenticated sources used by occurrence admission."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

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

    class CodemodSourceEpoch(m.ArbitraryTypesModel):
        """One shared authenticated text view for an immutable capture operation."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)
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

        id: Annotated[t.NonEmptyStr, m.Field(description="Stable rule identity")]
        phase: c.Infra.SemanticCutoverPhase = m.Field(
            default=c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
            strict=False,
            description="Existing semantic phase owning this rule's execution",
        )
        pattern: Annotated[t.NonEmptyStr, m.Field(description="Native Rope pattern")]
        goal: Annotated[t.NonEmptyStr, m.Field(description="Native Rope replacement")]
        arguments: Annotated[
            t.MappingKV[str, str],
            m.Field(description="Native Rope wildcard identity constraints"),
        ]
        imports: t.MappingKV[str, str] = u.Field(
            default_factory=u.empty(TypeForm(t.MappingKV[str, str])),
            description="Destination bindings and their native import declarations",
        )
        bindings: t.MappingKV[str, str] = u.Field(
            default_factory=u.empty(TypeForm(t.MappingKV[str, str])),
            description="Destination expressions and their required Rope identities",
        )
        model_bases: t.StrSequence = m.Field(
            default=(),
            description="Required model ancestry for every matched declaration",
        )
        unshadowed_builtins: t.StrSequence = m.Field(
            default=(),
            description="Native lexical names required to be interpreter builtins",
        )
        families: t.StrSequence = m.Field(
            default=(),
            description="Declared facade families admitting the source module",
        )
        scope_kinds: t.SequenceOf[
            Annotated[c.Infra.RopeScopeKind, m.Field(strict=False)]
        ] = m.Field(
            default=(),
            description="Native Rope lexical scopes admitting a match",
        )

    class RopeContractRules(m.ContractModel):
        """The packaged semantic contract policy, validated once on input."""

        rules: Annotated[
            t.SequenceOf[FlextInfraModelsCodemod.RopeContractRule],
            m.Field(description="Ordered, identity-constrained Rope contract rules"),
        ]

    class ModFixtureDirectories(m.ArbitraryTypesModel):
        """Validated physical directories selected by one ast-grep owner."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        rule_dirs: t.VariadicTuple[Path] = m.Field(
            description="Validated rule directories declared by the ast-grep owner",
        )
        util_dirs: t.VariadicTuple[Path] = m.Field(
            description="Validated utility directories declared by the ast-grep owner",
        )
        test_dirs: t.VariadicTuple[Path] = m.Field(
            description="Validated fixture directories declared by the ast-grep owner",
        )

    class ModRuleBatch(m.ArbitraryTypesModel):
        """Validated executable ast-grep documents prepared for one circuit."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

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
