"""Data-only contracts for the canonical AST-grep circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal, Self

from flext_cli import m, u
from typing_extensions import TypeForm

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsBase

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraModelsCodemod:
    """Typed contracts for native codemod scans and mutation reports."""

    class ContractAdmissionOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Independent native admission selectors for one contract planning pass."""

        annotation_only: bool = m.Field(
            default=False, description="Limit admission to annotation-only contracts"
        )
        class_alias_only: bool = m.Field(
            default=False, description="Limit admission to class-alias contracts"
        )

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
            indexed: MutableMapping[Path, m.Cli.AtomicFileState] = {}
            for state in states:
                previous = indexed.setdefault(state.path, state)
                if previous is not state and previous != state:
                    msg = f"binding source snapshots disagree: {state.path}"
                    raise ValueError(msg)
            return tuple(indexed.values())

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
            c.Infra.NativeRuleSeverity,
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

    class AstGrepOwnedPathDiagnostic(AstGrepDiagnostic):
        """A validated owned-path finding in the native scanner wire format."""

        origin: c.Infra.ModFindingOrigin = m.Field(
            default=c.Infra.ModFindingOrigin.OWNED_PATH,
            description="Native owned-path rule provenance",
        )

        @m.model_serializer
        def _serialize(self) -> t.JsonMapping:
            """Preserve the complete native record consumed by both scan routes.

            Returns:
                The native diagnostic with its original nested source range.

            """
            return {
                "file": self.file,
                "ruleId": self.rule_id,
                "severity": self.severity,
                "message": self.message,
                "origin": self.origin,
                "text": self.text,
                "lines": self.lines,
                "range": {
                    "start": {"line": self.line, "column": self.column},
                    "end": {"line": self.end_line, "column": self.end_column},
                    "byteOffset": {"start": self.start_byte, "end": self.end_byte},
                },
            }

    class AstGrepReport(m.RootModel[tuple[AstGrepDiagnostic, ...]]):
        """Complete ``ast-grep scan --json=compact`` array; malformed input raises."""

    class FamilyFlattenRule(m.ContractModel):
        """One installed, closed family-shape operation (ADR-017)."""

        id: Annotated[t.NonEmptyStr, m.Field(description="Exact rule receipt identity")]
        operation: Annotated[
            Literal[c.Infra.FamilyFlattenOperation.FLATTEN_SINGLE_WRAPPER],
            m.Field(description="Supported semantic family transformation"),
        ]
        collision: Annotated[
            Literal[c.Infra.FamilyCollisionPolicy.PREFIX_WRAPPER],
            m.Field(description="Member-name collision resolution policy"),
        ]

    class RopeContractOrigin(m.ContractModel):
        """Operational ownership elected independently of catalog document data."""

        owner_root: Path | None = m.Field(
            description="Elected repository root, or None for packaged policy"
        )

    class RopeContractRule(m.ContractModel):
        """Identity-constrained native Rope restructuring of a Python contract."""

        owner_root: Path | None = m.Field(
            default=None,
            exclude=True,
            description=(
                "Project root whose catalogue declares this rule; None for the "
                "packaged universal policy"
            ),
        )

        @m.field_validator("owner_root", mode="before")
        @classmethod
        def _document_origin(
            cls,
            value: t.ValidationInput[p.Model],
            info: p.ValidationInfo,
        ) -> t.ValidationInput[p.Model]:
            """Bind operational ownership without modifying the document mapping.

            Returns:
                The original Python value, or the elected document origin.

            Raises:
                TypeError: A Rope document has no validated operational origin.
                ValueError: A document attempts to declare its own origin.

            """
            context = info.context
            if not isinstance(context, Mapping) or (
                context.get("kind") is not c.ValidationInputKind.DOCUMENT
            ):
                return value
            origin = context.get("metadata")
            if not isinstance(origin, FlextInfraModelsCodemod.RopeContractOrigin):
                message = "Rope document input requires a validated catalog origin"
                raise TypeError(message)
            if value is not None:
                message = "A Rope document cannot declare its operational owner root"
                raise ValueError(message)
            return origin.owner_root

        id: Annotated[t.NonEmptyStr, m.Field(description="Stable rule identity")]
        operation: t.DocumentInput[c.Infra.RopeContractOperation] = m.Field(
            default=c.Infra.RopeContractOperation.RESTRUCTURE,
            description="Native contract operation executed in the shared source epoch",
        )
        source_revision: t.NonEmptyStr | None = m.Field(
            default=None,
            description="Explicit Git revision authenticating retired provider "
            "declarations",
        )
        phase: t.DocumentInput[c.Infra.SemanticCutoverPhase] = m.Field(
            default=c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
            description="Existing semantic phase owning this rule's execution",
        )
        pattern: Annotated[t.NonEmptyStr, m.Field(description="Native Rope pattern")]
        goal: Annotated[t.NonEmptyStr, m.Field(description="Native Rope replacement")]
        arguments: Annotated[
            Mapping[str, str | Sequence[str]],
            m.Field(
                description="Native Rope identity constraints or admitted alternatives"
            ),
        ]
        imports: Mapping[str, str] = m.Field(
            default_factory=u.empty(TypeForm(Mapping[str, str])),
            description="Destination bindings and their native import declarations",
        )
        bindings: Mapping[str, str] = m.Field(
            default_factory=u.empty(TypeForm(Mapping[str, str])),
            description="Destination expressions and their required Rope identities",
        )
        model_bases: t.DocumentInput[tuple[str, ...]] = m.Field(
            default=(),
            description="Required model ancestry for every matched declaration",
        )
        unshadowed_builtins: t.DocumentInput[tuple[str, ...]] = m.Field(
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
        readonly_contract: t.NonEmptyStr | None = m.Field(
            default=None,
            description="Capture requiring a proven read-only collection origin",
        )
        deferred_contract: t.NonEmptyStr | None = m.Field(
            default=None,
            description=(
                "Capture resolved by a canonical typed factory after declaration"
            ),
        )
        readonly_origins: t.DocumentInput[tuple[str, ...]] = m.Field(
            default=(),
            description="Native read-only collection identities admitting the capture",
        )
        drops: t.DocumentInput[tuple[str, ...]] = m.Field(
            default=(),
            description="Discarded captures that must be inert native constants",
        )
        reorders_annotation: bool = m.Field(
            default=False,
            description="Whether the replacement changes annotation evaluation order",
        )
        families: t.DocumentInput[tuple[str, ...]] = m.Field(
            default=(),
            description="Declared facade families admitting the source module",
        )
        scope_kinds: t.DocumentInput[
            tuple[t.DocumentInput[c.Infra.RopeScopeKind], ...]
        ] = m.Field(
            default=(),
            description="Native Rope lexical scopes admitting a match",
        )
        implementation_owner: (
            t.DocumentInput[tuple[t.NonEmptyStr, t.NonEmptyStr]] | None
        ) = m.Field(
            default=None,
            description="Native module and primitive whose backend stays native",
        )
        receiver_methods: t.DocumentInput[tuple[str, ...]] = m.Field(
            default=(),
            description="Discarded-call interface required of a factory product",
        )
        call_target: t.NonEmptyStr | None = m.Field(
            default=None,
            description="Capture admitted as a native callee or required field call",
        )
        explicit_arguments: bool = m.Field(
            default=False,
            description=(
                "Require proven call arguments without positional or keyword expansion"
            ),
        )
        required_field: bool = m.Field(
            default=False,
            description="Require metadata without a field default or factory",
        )
        defaulted_field: Annotated[
            bool,
            m.Field(description="Extract one concrete field default outside metadata"),
        ] = False
        private_attribute: bool = m.Field(
            default=False,
            description="Require an unset native private model attribute",
        )
        value_default: t.NonEmptyStr | None = m.Field(
            default=None,
            description="Default capture that must not denote a required field",
        )
        factory_default: t.NonEmptyStr | None = m.Field(
            default=None,
            description="Factory capture that must not denote an absent factory",
        )
        missing_keywords: t.DocumentInput[tuple[str, ...]] = m.Field(
            default=(),
            description="Injected keywords whose presence preserves a composition",
        )
        ownership_transfer: (
            t.DocumentInput[tuple[t.NonEmptyStr, t.NonEmptyStr]] | None
        ) = m.Field(
            default=None,
            description="Native module/member retired after receiver transfer",
        )

        @m.model_validator(mode="after")
        def _validate_call_target(self) -> Self:
            for capture in (self.value_default, self.factory_default):
                if capture is not None and f"${{{capture}}}" not in self.pattern:
                    msg = "native default proof must name a pattern capture"
                    raise ValueError(msg)
            field_modes = (
                self.required_field,
                self.defaulted_field,
                self.private_attribute,
            )
            field_metadata = any(field_modes)
            invalid_field_mode = sum(field_modes) > 1
            if field_metadata and (
                self.call_target is None
                or not self.model_bases
                or self.scope_kinds != (c.Infra.RopeScopeKind.CLASS,)
                or invalid_field_mode
            ):
                msg = (
                    "native field metadata requires one mode, a callee "
                    "and model class scope"
                )
                raise ValueError(msg)
            if self.defaulted_field and (
                self.value_default is None
                or f"${{{self.call_target}}}(${{{self.value_default}}})"
                not in self.pattern
                or f"${{{self.call_target}}}()" not in self.goal
            ):
                msg = (
                    "native default extraction requires its call and default templates"
                )
                raise ValueError(msg)
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
            Sequence[FlextInfraModelsCodemod.RopeContractRule],
            m.Field(description="Ordered, identity-constrained Rope contract rules"),
        ]

    class ModFixtureDirectories(FlextInfraModelsBase.FrozenArbitrary):
        """Validated physical directories selected by one ast-grep owner."""

        rule_dirs: tuple[Path, ...] = m.Field(
            description="Validated rule directories declared by the ast-grep owner",
        )
        util_dirs: tuple[Path, ...] = m.Field(
            description="Validated utility directories declared by the ast-grep owner",
        )
        test_dirs: tuple[Path, ...] = m.Field(
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
