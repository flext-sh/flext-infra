"""Base typings for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from pathlib import Path as _Path
from typing import Annotated, Literal

from jinja2.environment import (
    Environment as _JinjaEnvironment,
    Template as _JinjaTemplate,
)

from flext_cli import m, t


class FlextInfraTypesBase:
    """Base typings for flext-infra project."""

    type RegexPattern = t.RegexPattern
    "Compiled regex pattern for string matching."
    type RegexMatch = t.RegexMatch
    "Regex match object for string patterns."
    type JinjaEnvironment = _JinjaEnvironment
    "Jinja2 template rendering environment."
    type JinjaTemplate = _JinjaTemplate
    "Jinja2 template object."

    type InfraValue = t.JsonValue
    "Canonical infrastructure payload contract from flext-cli JSON typing."
    type FacadeFamily = str
    "Facade family identifier for MRO chain resolution."
    type ExpectedBase = type | str
    "Expected MRO base: a class or its qualified name."
    type PolicyContext = t.MappingKV[str, t.JsonMapping]
    "Class-nesting policy matrix keyed by module family."
    type MetricValue = t.Scalar | _Path | None
    "Output metric value: scalar (str/int/float/bool/datetime), path, or null."
    type ChangeCallback = Callable[[str], None] | None
    "Optional callback invoked on transformer changes."
    type LazyInitProcessResult = tuple[int | None, t.LazyAliasMap]
    "Result for per-directory lazy init processing."
    type LazyInitWriteResult = tuple[int, t.LazyAliasMap]
    "Result for writing generated __init__.py."
    type StrSet = set[str]
    "Mutable string set (supports .update/.intersection/etc)."
    type CanonicalValue = t.Scalar | t.StrSequence
    "Canonical governance value: scalar payload or string sequence."

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
    type LoadedRuleSelections[RuleKindT, FileRuleKindT] = tuple[
        t.SequenceOf[tuple[RuleKindT, t.JsonMapping]],
        t.SequenceOf[tuple[FileRuleKindT, t.JsonMapping]],
    ]
    "Loaded text-rule + file-rule selections from one declarative rules directory."
    type DomainResult = m.BaseModel | InfraValue
    "Typed service result payload: model or validated JSON value."
    type DomainResultSequence = t.SequenceOf[DomainResult]
    "Read-only sequence of typed service result payloads."

    # ── Transformer / edit result types ──────────────────────────────

    type TransformResult = t.StrSequencePair
    "Canonical (new_source, change_descriptions) from any source transformer."
    type EditResult = tuple[bool, t.StrSequence]
    "Validated edit outcome: (success, report_lines)."
    type EditResultWithDescs = tuple[bool, t.StrSequence, t.StrSequence]
    "(success, descriptions, report_lines) — includes what was attempted."
    type LintSnapshot = t.MappingKV[str, t.StrSequence]
    "Lint errors per tool: {tool_name: [error_lines]}."

    type DocsPhase = Literal["audit", "build", "fix", "generate", "validate"]
    "Closed string set selecting which docs orchestrator phase to execute."
    type ReleaseArtifactKind = Literal["sdist", "wheel"]
    "Closed artifact kind emitted by a release build."
    type ReleaseAbsolutePath = Annotated[
        str, t.StringConstraints(min_length=1, pattern=r"^(?:/|[A-Za-z]:[\\/])")
    ]
    "Absolute POSIX or Windows path serialized in a release report."
    type ReleaseArtifactSha256 = Annotated[
        str, t.StringConstraints(pattern=r"^[0-9a-f]{64}$")
    ]
    "Lowercase SHA-256 digest serialized in a release report."
    type ReleaseCommitOid = Annotated[
        str, t.StringConstraints(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    ]
    "Lowercase Git SHA-1 or SHA-256 commit object identifier."
