"""Data-only contracts for the canonical AST-grep circuit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import m, u
from packaging.utils import canonicalize_name
from typing_extensions import TypeForm

from flext_infra import c, p, t
from flext_infra._models import FlextInfraModelsBase


class FlextInfraModelsCodemod:
    """Typed contracts for native codemod scans and mutation reports."""

    class RopeSignatureAddition(m.ContractModel):
        """Required keyword propagation elected by native caller identities."""

        id: Annotated[t.NonEmptyStr, m.Field(description="Stable addition identity")]
        target: Annotated[
            t.NonEmptyStr, m.Field(description="Native qualified function declaration")
        ]
        parameter: Annotated[
            t.NonEmptyStr, m.Field(description="Required keyword parameter name")
        ]
        annotation: Annotated[
            t.NonEmptyStr, m.Field(description="Origin-owned annotation expression")
        ]
        default: str | None = m.Field(
            default=None,
            description="Native default expression; absent requires every caller value",
        )
        call_values: Annotated[
            Mapping[str, str],
            m.Field(description="Caller declaration identity to argument expression"),
        ]

    class RopeSignatureRemoval(m.ContractModel):
        """Replace exact parameter references before native signature retirement."""

        id: Annotated[t.NonEmptyStr, m.Field(description="Stable operation identity")]
        target: Annotated[
            t.NonEmptyStr, m.Field(description="Native qualified function declaration")
        ]
        parameter: Annotated[
            t.NonEmptyStr, m.Field(description="Existing parameter to retire")
        ]
        replacement: Annotated[
            t.NonEmptyStr, m.Field(description="Explicit native body expression")
        ]

    class RopeMethodTransfer(m.ContractModel):
        """An existing class receiving a natively proven method declaration."""

        id: Annotated[t.NonEmptyStr, m.Field(description="Stable transfer identity")]
        destination: Annotated[
            Sequence[t.NonEmptyStr],
            m.Field(
                min_length=2,
                max_length=2,
                description="Destination module and existing qualified class",
            ),
        ]
        methods: Annotated[
            Sequence[
                Annotated[Sequence[t.NonEmptyStr], m.Field(min_length=2, max_length=2)]
            ],
            m.Field(
                min_length=1,
                description="Source module and qualified method pairs",
            ),
        ]
        receiver_rewrites: Mapping[str, str] = m.Field(
            default_factory=dict,
            description=(
                "Explicit self.member to injected receiver path for one instance method"
            ),
        )

    class ContractAdmissionOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Independent native admission selectors for one contract planning pass."""

        annotation_only: bool = m.Field(
            default=False, description="Limit admission to annotation-only contracts"
        )
        class_alias_only: bool = m.Field(
            default=False, description="Limit admission to class-alias contracts"
        )
        signature_additions: Sequence[FlextInfraModelsCodemod.RopeSignatureAddition] = (
            m.Field(default=(), description="Native additions in this same source pass")
        )
        method_transfers: Sequence[FlextInfraModelsCodemod.RopeMethodTransfer] = (
            m.Field(default=(), description="Native transfers in this same source pass")
        )
        signature_removals: Sequence[FlextInfraModelsCodemod.RopeSignatureRemoval] = (
            m.Field(default=(), description="Native body and parameter retirements")
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
            tuple[t.Port[p.Cli.AtomicFileState], ...],
            m.Field(description="Consumer and resolved Python import-owner inputs"),
        ]

        @m.field_validator("states")
        @classmethod
        def unique_inputs(
            cls, states: tuple[t.Port[p.Cli.AtomicFileState], ...]
        ) -> tuple[t.Port[p.Cli.AtomicFileState], ...]:
            """Store each authenticated input once; conflicting identities fail.

            Returns:
                The resulting ``tuple[p.Cli.AtomicFileState, ...]``.

            Raises:
                ValueError: If binding source snapshots disagree.

            """
            indexed: MutableMapping[Path, p.Cli.AtomicFileState] = {}
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
        Python-mode dumps carry field names and re-validate by name.
        """

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(
            strict=True, validate_by_name=True
        )

        file: Annotated[str, m.Field(min_length=1, description="Reported source path")]
        rule_id: str = m.Field(
            alias="ruleId", min_length=1, description="Native rule ID"
        )
        severity: Annotated[
            c.Infra.NativeRuleSeverity,
            m.Field(description="Native rule severity"),
        ]
        message: Annotated[str, m.Field(description="Native rule diagnostic")]
        text: Annotated[str, m.Field(description="Exact matched source text")]
        lines: Annotated[str, m.Field(description="Source lines containing the match")]
        line: int = m.Field(
            ge=0,
            validation_alias=m.AliasPath("range", "start", "line"),
            description="Zero-based starting source line",
        )
        column: int = m.Field(
            ge=0,
            validation_alias=m.AliasPath("range", "start", "column"),
            description="Zero-based starting source column",
        )
        end_line: int = m.Field(
            ge=0,
            validation_alias=m.AliasPath("range", "end", "line"),
            description="Zero-based ending source line",
        )
        end_column: int = m.Field(
            ge=0,
            validation_alias=m.AliasPath("range", "end", "column"),
            description="Zero-based ending source column",
        )
        start_byte: int = m.Field(
            ge=0,
            validation_alias=m.AliasPath("range", "byteOffset", "start"),
            description="Inclusive UTF-8 byte offset",
        )
        end_byte: int = m.Field(
            ge=0,
            validation_alias=m.AliasPath("range", "byteOffset", "end"),
            description="Exclusive UTF-8 byte offset",
        )

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
            c.Infra.FamilyFlattenOperation,
            m.Field(
                description="Supported semantic family transformation", strict=False
            ),
        ]
        collision: Annotated[
            c.Infra.FamilyCollisionPolicy,
            m.Field(
                description="Member-name collision resolution policy", strict=False
            ),
        ]

    class RopeContractOrigin(m.ContractModel):
        """Operational ownership elected independently of catalog document data."""

        owner_root: Path | None = m.Field(
            description="Elected repository root, or None for packaged policy"
        )

    class RopeContractScopeTarget(m.ContractModel):
        """One exact distribution and module admitted by a contract rule."""

        distribution: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical PEP 503 distribution identity"),
        ]
        module: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact dotted Python module identity"),
        ]

        @m.model_validator(mode="after")
        def _validate_identity(self) -> Self:
            if canonicalize_name(self.distribution) != self.distribution:
                msg = (
                    "contract scope distribution must use its canonical PEP 503 "
                    "identity"
                )
                raise ValueError(msg)
            if any(not part.isidentifier() for part in self.module.split(".")):
                msg = "contract scope module must be a dotted Python identifier"
                raise ValueError(msg)
            return self

    class RopeContractScope(m.ContractModel):
        """Closed rule target set; unlisted source modules are never candidates."""

        targets: Annotated[
            Sequence[FlextInfraModelsCodemod.RopeContractScopeTarget],
            m.Field(min_length=1, description="Exact distribution/module target pairs"),
        ]

        @m.model_validator(mode="after")
        def _unique_targets(self) -> Self:
            identities = tuple(
                (item.distribution, item.module) for item in self.targets
            )
            if len(identities) != len(set(identities)):
                msg = "contract scope targets must be unique"
                raise ValueError(msg)
            return self

    class RopeContractRuleTarget(m.ContractModel):
        """Identity, admission scope and native pattern of one Rope contract rule."""

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
            value: t.ValidationInput[p.BaseModel],
            info: p.ValidationInfo,
        ) -> t.ValidationInput[p.BaseModel]:
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
        scope: FlextInfraModelsCodemod.RopeContractScope | None = m.Field(
            default=None,
            description=(
                "Closed distribution/module admission set; absent keeps the rule "
                "universal"
            ),
        )
        annotation_only: bool = m.Field(
            default=False,
            description="Admit matches only inside declared type annotations",
        )
        annotation_member_source: t.NonEmptyStr | None = m.Field(
            default=None,
            description=(
                "Exact source namespace admitted for a proven annotation member move"
            ),
        )
        phase: t.DocumentInput[c.Infra.SemanticCutoverPhase] = m.Field(
            default=c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
            description="Existing semantic phase owning this rule's execution",
        )
        pattern: Annotated[t.NonEmptyStr, m.Field(description="Native Rope pattern")]
        goal: Annotated[str, m.Field(description="Native Rope replacement")]
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

    class RopeContractRuleShape(RopeContractRuleTarget):
        """Ancestry, capture and lexical-scope constraints of a Rope rule."""

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

    class RopeContractRule(RopeContractRuleShape):
        """Identity-constrained native Rope restructuring of a Python contract."""

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

        def _validate_annotation_member_template(self) -> None:
            """Require a precise source template and authenticated target owner.

            Raises:
                ValueError: The annotation rule cannot prove its target member owner.

            """
            if self.annotation_member_source is None:
                return
            member = ".${member}"
            target = self.goal.removesuffix(member)
            if target.partition(".")[0] == c.Infra.FacadeFamily.M:
                msg = (
                    "annotation member rules cannot produce model typing; "
                    "declare a canonical runtime-checkable protocol destination"
                )
                raise ValueError(msg)
            owner = self.bindings.get(target)
            source_owner = self.bindings.get(self.annotation_member_source)
            valid = (
                self.annotation_only
                and self.operation == c.Infra.RopeContractOperation.RESTRUCTURE
                and self.pattern == "${receiver}.${member}"
                and self.goal.endswith(member)
                and self.goal.count(member) == 1
                and "${" not in target
                and self.scope is not None
                and all(
                    part.isidentifier()
                    for value in (
                        self.annotation_member_source,
                        target,
                        owner or "",
                        source_owner or "",
                    )
                    for part in value.split(".")
                )
                and owner is not None
                and source_owner is not None
            )
            if not valid:
                msg = "annotation member rules require a native source and bound target"
                raise ValueError(msg)

        @m.model_validator(mode="after")
        def _validate_call_target(self) -> Self:
            self._validate_annotation_member_template()
            if (
                self.annotation_only
                and self.operation != c.Infra.RopeContractOperation.RESTRUCTURE
            ):
                msg = "annotation-only rules require native restructure"
                raise ValueError(msg)
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
        signature_additions: Sequence[FlextInfraModelsCodemod.RopeSignatureAddition] = (
            m.Field(default=(), description="Ordered native required keyword additions")
        )
        method_transfers: Sequence[FlextInfraModelsCodemod.RopeMethodTransfer] = (
            m.Field(default=(), description="Ordered native method ownership transfers")
        )
        signature_removals: Sequence[FlextInfraModelsCodemod.RopeSignatureRemoval] = (
            m.Field(default=(), description="Ordered native parameter retirements")
        )

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
