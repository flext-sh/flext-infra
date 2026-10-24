"""Base typings for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast as _ast
import pathlib
from collections.abc import Callable, MutableMapping, MutableSet
from datetime import date, datetime
from dis import Instruction
from types import (
    BuiltinFunctionType,
    ClassMethodDescriptorType,
    CodeType,
    FunctionType,
    GetSetDescriptorType,
    MemberDescriptorType,
    MethodDescriptorType,
    MethodWrapperType,
    UnionType,
    WrapperDescriptorType,
)
from typing import Annotated, Literal

import griffe
from flext_cli import m, p, t
from jinja2.environment import (
    Environment as _JinjaEnvironment,
    Template as _JinjaTemplate,
)


class FlextInfraTypesBase:
    """Base typings for flext-infra project."""

    type DocumentationLanguage = t.DocumentationLanguage
    "Supported project-local documentation presentation languages."
    type PythonModule = griffe.Module
    "One statically parsed Python module of the shared static model."

    type Path = pathlib.Path
    "Unconstrained native filesystem path, independent of existence and kind."

    type MutableSetOf[ItemT] = MutableSet[ItemT]
    "An explicitly mutable set contract for operation-owned native state."

    type SettingsContainerInput = (
        t.JsonValue | tuple[t.JsonValue | tuple[t.JsonValue, ...], ...]
    )
    "Native option ingress before only its declaration containers are frozen."

    @staticmethod
    def _freeze_settings_container(
        value: FlextInfraTypesBase.SettingsContainerInput,
    ) -> FlextInfraTypesBase.SettingsContainerInput:
        """Freeze one YAML declaration container without rewriting its payload.

        Returns:
            The same container as a tuple when YAML supplied a list.

        """
        return tuple(value) if isinstance(value, list) else value

    type SettingsPairs = Annotated[
        tuple[
            Annotated[
                tuple[
                    Annotated[
                        str,
                        t.StringConstraints(
                            min_length=1,
                            strip_whitespace=False,
                            pattern=r"^\S+$",
                        ),
                    ],
                    t.JsonValue,
                ],
                m.BeforeValidator(_freeze_settings_container),
            ],
            ...,
        ],
        m.BeforeValidator(_freeze_settings_container),
    ]
    "Ordered JSON-compatible option pairs with last-declaration precedence."

    @staticmethod
    def _reject_blanket_mask(rule: str) -> str:
        """Return the bare Ruff rule name, rejecting ``ALL``, padding and codes.

        Normalizing here keeps the rendered TOML free of accidental padding: a
        padded name would otherwise reach a generated pyproject verbatim and no
        longer match the rule Ruff knows. Ruff identifies a rule by its
        kebab-case name (``line-too-long``), so a code (``E501``) is refused.

        Returns:
            The bare rule name.

        Raises:
            ValueError: If the value is blank padding, ``ALL``, or not a
                kebab-case Ruff rule name.

        """
        normalized = rule.strip()
        if not normalized:
            message = "a Ruff exemption must name a rule, not blank padding."
            raise ValueError(message)
        if normalized.upper() == "ALL":
            message = (
                "ALL is not a Ruff exemption: it masks every rule, present and "
                "future. Name each suppressed rule instead."
            )
            raise ValueError(message)
        if not (normalized.islower() and normalized.replace("-", "").isalnum()):
            message = (
                f"{normalized!r} is not a Ruff rule name: name the rule in "
                "kebab-case (line-too-long), never by its code (E501)."
            )
            raise ValueError(message)
        return normalized

    type PlanSourceTimestamp = str | date | datetime | None
    "Native YAML timestamp ingress; dates retain their original precision."
    type DocsRenderedArtifactTuple = t.Triple[Path, Path, str | None]
    "Rendered document destination, source, and optional project owner."

    type RegexPattern = t.RegexPattern
    "Compiled regex pattern for string matching."
    type RegexMatch = t.RegexMatch
    "Regex match object for string patterns."
    type JinjaEnvironment = _JinjaEnvironment
    "Jinja2 template rendering environment."
    type JinjaTemplate = _JinjaTemplate
    "Jinja2 template object."
    type NativeCode = CodeType
    "Exact interpreter code identity accepted by disassembly and native encoding."
    type NativeFunction = FunctionType
    "Exact interpreter function identity retaining its actual executable storage."
    type NativeBuiltinCallable = BuiltinFunctionType | MethodWrapperType
    "The two interpreter callable types with native receiver metadata."
    type NativeDescriptor = (
        GetSetDescriptorType
        | MemberDescriptorType
        | ClassMethodDescriptorType
        | MethodDescriptorType
        | WrapperDescriptorType
    )
    "Exact interpreter descriptor identities accepted by native observation."
    type NativeOperand = p.AttributeProbe | type[p.AttributeProbe] | UnionType | None
    "A passively observed value, including native class identities and nulls."
    type NativeType = type[p.AttributeProbe | UnionType]
    "Exact native type owners, including the interpreter's union type."
    type NativeClassDeclarations = t.MappingKV[
        str, t.VariadicTuple[t.Pair[int, frozenset[str]]]
    ]
    "Immutable compiler facts: class qualified names, source lines and stores."
    type NativeCompilationFacts = t.DictKV[
        t.Triple[bytes, str, int], NativeClassDeclarations
    ]
    "Invocation-local class facts keyed by exact source bytes and compiler inputs."
    type NativeInstructionFacts = t.DictKV[
        int, t.Pair[NativeCode, t.VariadicTuple[Instruction]]
    ]
    "Immutable instructions indexed by strong native code identity."
    type NativeInvocationFacts = t.Pair[NativeCompilationFacts, NativeInstructionFacts]
    "The two immutable fact caches scoped to one native observation invocation."

    type InfraValue = t.JsonValue
    "Canonical infrastructure payload contract from flext-cli JSON typing."
    type FacadeFamily = str
    "Facade family identifier for FLEXT chain resolution."
    type ExpectedBase = type | str
    "Expected FLEXT base: a class or its qualified name."
    type MetricValue = t.Scalar | Path | None
    "Output metric value: scalar (str/int/float/bool/datetime), path, or null."
    type ChangeCallback = Callable[[str], None] | None
    "Optional callback invoked on transformer changes."
    type PipelineHandler = Callable[
        [p.Cli.PipelineStageContext],
        p.Result[m.Cli.PipelineStageResult],
    ]
    "Stage handler contract for the flext-infra check/codegen DAG pipelines."
    type PipelineHandlerMap = t.MappingKV[str, PipelineHandler]
    "Stage-id to handler mapping used to build DAG pipeline stage specs."
    type StrSet = set[str]
    "Mutable string set (supports .update/.intersection/etc)."
    type CanonicalValue = t.Scalar | t.StrSequence
    "Canonical governance value: scalar payload or string sequence."
    "Scalar types admitted by declarative tooling settings."

    type CensusRecord = t.HeaderMapping
    "Single census record: string keys with str|int values (name, type, usages)."

    type InfraMapping = t.JsonMapping
    "Read-only validated infra payload mapping."
    type MutableInfraMapping = MutableMapping[str, InfraValue]
    "Mutable validated infra payload mapping."
    type InfraSequence = t.JsonList
    "Read-only validated infra payload sequence."
    type RuleSelection[KindT] = tuple[KindT, t.JsonMapping]
    "One matched rule kind paired with its validated declarative payload."
    type DomainResult = m.BaseModel | InfraValue
    "Typed service result payload: model or validated JSON value."
    type DomainResultSequence = t.SequenceOf[DomainResult]
    "Read-only sequence of typed service result payloads."
    # ── Transformer / edit result types ──────────────────────────────

    type TransformResult = t.StrSequencePair
    "Canonical (new_source, change_descriptions) from any source transformer."
    type PrivateImportSpec = t.Quint[str, str, str, str, str]
    "(private module, symbol, qualified name, owner package, target reference)."
    type PrivateImportReferences = tuple[
        t.MappingKV[Path, t.SequenceOf[PrivateImportSpec]],
        t.MappingKV[Path, t.MappingKV[str, t.StrPair]],
        t.MappingKV[str, t.VariadicTuple[t.Quad[_ast.Module, str, str, str]]],
    ]
    "Resolved private-import specs, declared re-export targets, and facade owners."
    type ConstantFacadeIndex = tuple[
        t.MappingKV[str, t.VariadicTuple[t.Quad[_ast.Module, str, str, str]]],
        t.MappingKV[str, set[str]],
        t.MappingKV[str, t.VariadicTuple[str]],
    ]
    "Live constants facades, export identities, and declared class ancestry."
    type ConstantConsumerContext = t.Quad[
        _ast.Module,
        str,
        ConstantFacadeIndex,
        t.MutableMappingKV[t.Pair[str, str], str | None],
    ]
    "One module's constants facade selection and shared identity cache."
    type EditResult = tuple[bool, t.StrSequence]
    "Validated edit outcome: (success, report_lines)."
    type EditResultWithDescs = tuple[bool, t.StrSequence, t.StrSequence]
    "(success, descriptions, report_lines) — includes what was attempted."
    type LintSnapshot[Receipt] = t.MappingKV[str, Receipt]
    "Native gate receipts or diagnostic deltas, keyed by canonical tool name."

    # ── Lint policy types ────────────────────────────────────────────

    type RuffRule = Annotated[
        str,
        t.StringConstraints(min_length=1),
        m.AfterValidator(_reject_blanket_mask),
    ]
    """One native Ruff rule name used by repair and checking ownership.

    ``ALL``, family selectors, and rule codes are not individual rule identities.
    They cannot identify a repair or checking owner and are rejected before
    projection. Rule ownership never permits a blanket mask.
    """

    type LifecycleContext = Literal["local", "ci"]

    type DocsPhase = Literal["audit", "build", "fix", "generate", "validate"]
    "Closed string set selecting which docs orchestrator phase to execute."
    type LayoutRule = Literal["move", "archive", "gitignore", "review"]
    "Closed layout decision kinds produced by the layout engine."
    type LayoutStatus = Literal["planned", "applied", "skipped", "noop"]
    "Closed layout finding execution statuses."
    type ReleaseArtifactKind = Literal["sdist", "wheel"]
    "Closed artifact kind emitted by a release build."
    type ReleaseAbsolutePath = Annotated[
        str,
        t.StringConstraints(min_length=1, pattern=r"^(?:/|[A-Za-z]:[\\/])"),
    ]
    "Absolute POSIX or Windows path serialized in a release report."
    type ReleaseArtifactSha256 = Annotated[
        str,
        t.StringConstraints(pattern=r"^[0-9a-f]{64}$"),
    ]
    "Lowercase SHA-256 digest serialized in a release report."
    type ReleaseCommitOid = Annotated[
        str,
        t.StringConstraints(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"),
    ]
    "Lowercase Git SHA-1 or SHA-256 commit object identifier."
    # ── Git type aliases ────────────────────────────────────────────

    type GitOid = str
    "Canonical hex Git object identifier."
    type GitRef = str
    "Fully-qualified or short Git ref name."
    type GitPathSpec = str
    "Git pathspec string (e.g. ``:(exclude)dir``)."


__all__: list[str] = ["FlextInfraTypesBase"]
