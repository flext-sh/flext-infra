"""Base typings for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import argparse as _argparse
import ast as _ast
import re as _re
from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from io import TextIOBase as _TextIOBase
from pathlib import Path as _Path

from flext_cli import m, t
from jinja2 import Environment as _JinjaEnvironment, Template as _JinjaTemplate
from tomlkit import TOMLDocument
from tomlkit.container import Container as _TOMLContainer
from tomlkit.items import Item as _TOMLItem, Table


class FlextInfraTypesBase:
    """Base typings for flext-infra project."""

    type CliArgumentParser = _argparse.ArgumentParser
    "argparse ArgumentParser for CLI command definitions."
    type CliNamespace = _argparse.Namespace
    "argparse Namespace for parsed CLI arguments."
    type RegexPattern = _re.Pattern[str]
    "Compiled regex pattern for string matching."
    type TextStream = _TextIOBase
    "Text I/O stream (file-like object with write/read)."
    type JinjaEnvironment = _JinjaEnvironment
    "Jinja2 template rendering environment."
    type JinjaTemplate = _JinjaTemplate
    "Jinja2 template object."
    type TomlDocument = TOMLDocument
    "Tomlkit TOML document."
    type TomlContainer = _TOMLContainer
    "Tomlkit container (mutable TOML section)."
    type TomlItem = _TOMLItem
    "Tomlkit item (value or table)."
    type TomlTable = Table
    "Tomlkit table."
    type RegexMatch = _re.Match[str]
    "Compiled regex match result."
    type AstClassDef = _ast.ClassDef
    "AST class definition node."
    type AstFunctionDef = _ast.FunctionDef
    "AST function definition node."
    type AstAsyncFunctionDef = _ast.AsyncFunctionDef
    "AST async function definition node."
    type AstExpr = _ast.expr
    "AST expression node."
    type AstStmt = _ast.stmt
    "AST statement node."
    type AstCall = _ast.Call
    "AST function call node."
    type AstAssign = _ast.Assign
    "AST assignment node."
    type AstAnnAssign = _ast.AnnAssign
    "AST annotated assignment node."
    type AstTypeAlias = _ast.TypeAlias
    "AST PEP 695 type alias node."
    type AstKeyword = _ast.keyword
    "AST keyword argument node."

    type Pair[LeftT, RightT] = tuple[LeftT, RightT]
    "Generic pair alias for two ordered values."
    type Triple[FirstT, SecondT, ThirdT] = tuple[FirstT, SecondT, ThirdT]
    "Generic triple alias for three ordered values."
    type Quad[FirstT, SecondT, ThirdT, FourthT] = tuple[
        FirstT,
        SecondT,
        ThirdT,
        FourthT,
    ]
    "Generic 4-item tuple alias."
    type Quint[FirstT, SecondT, ThirdT, FourthT, FifthT] = tuple[
        FirstT,
        SecondT,
        ThirdT,
        FourthT,
        FifthT,
    ]
    "Generic 5-item tuple alias."
    type VariadicTuple[ItemT] = tuple[ItemT, ...]
    "Generic variadic tuple alias for homogeneous tuples."

    type InfraValue = t.JsonValue
    "Canonical infrastructure payload contract from flext-cli JSON typing."
    type ContainerDict = t.JsonMapping
    "Validated JSON object for project reports, docs contracts, and rules."
    type FacadeFamily = str
    "Facade family identifier for MRO chain resolution."
    type ExpectedBase = type | str
    "Expected MRO base: a class or its qualified name."
    type PolicyContext = Mapping[str, ContainerDict]
    "Class-nesting policy matrix keyed by module family."
    type MetricValue = t.Scalar | _Path | None
    "Output metric value: scalar (str/int/float/bool/datetime), path, or null."
    type MetricRecord = m.BaseModel | Mapping[str, MetricValue]
    "A single metric record: a Pydantic model or a string-keyed mapping of metric values."
    type ChangeCallback = Callable[[str], None] | None
    "Optional callback invoked on transformer changes."
    type StrPair = tuple[str, str]
    "Ordered pair of strings."
    type StrIntPair = tuple[str, int]
    "Ordered pair of (str, int)."
    type IntPair = tuple[int, int]
    "Ordered pair of (int, int)."
    type StrPairSequence = Sequence[StrPair]
    "Read-only sequence of string pairs."
    type LazyImportMap = Mapping[str, StrPair]
    "Lazy import table: export -> (module, attr)."
    type MutableLazyImportMap = MutableMapping[str, StrPair]
    "Mutable lazy import table."
    type LazyInitProcessResult = tuple[int | None, LazyImportMap]
    "Result for per-directory lazy init processing."
    type LazyInitWriteResult = tuple[int, LazyImportMap]
    "Result for writing generated __init__.py."
    type VersionExportsResult = tuple[t.StrMapping, LazyImportMap]
    "Result for __version__.py export extraction (inline constants, eager import map)."
    type StrSet = set[str]
    "Mutable string set (supports .update/.intersection/etc)."
    type PathSet = set[_Path]
    "Mutable path set."
    type IntSet = set[int]
    "Mutable integer set."
    type StrPairSet = set[StrPair]
    "Mutable set of (str, str) tuples."
    type IntPairSet = set[StrIntPair]
    "Mutable set of (str, int) tuples."
    type CanonicalScalar = str | int
    "Canonical governance scalar: string or integer."
    type CanonicalValue = CanonicalScalar | t.StrSequence
    "Canonical governance value: scalar string, integer, or string list."
    type AstMethodNode = _ast.FunctionDef | _ast.AsyncFunctionDef
    "AST node for a method definition (sync or async)."
    type AstModule = _ast.Module
    "AST module node from ast.parse()."
    type TomlData = dict[str, InfraValue]
    "Unwrapped TOML table data — nested dicts of primitives from tomlkit unwrap()."

    type CensusRecord = t.HeaderMapping
    "Single census record: string keys with str|int values (name, type, usages)."
    type MutableCensusRecordList = MutableSequence[CensusRecord]
    "Mutable list of census records."

    type InfraMapping = ContainerDict
    "Read-only validated infra payload mapping."
    type MutableInfraMapping = MutableMapping[str, InfraValue]
    "Mutable validated infra payload mapping."
    type InfraSequence = t.JsonList
    "Read-only validated infra payload sequence."
    type MutableInfraSequence = MutableSequence[InfraValue]
    "Mutable validated infra payload sequence."
    type RuleDefinition = InfraMapping
    "Canonical declarative rule definition payload."
    type RuleDefinitions = Sequence[ContainerDict]
    "Read-only sequence of declarative rule definitions."
    type RuleSkipPredicate = Callable[[ContainerDict], bool]
    "Predicate deciding whether one rule definition should be skipped."
    type RuleSelection[KindT] = tuple[KindT, t.JsonMapping]
    "One matched rule kind paired with its validated declarative payload."
    type LoadedRuleSelections[RuleKindT, FileRuleKindT] = tuple[
        Sequence[tuple[RuleKindT, t.JsonMapping]],
        Sequence[tuple[FileRuleKindT, t.JsonMapping]],
    ]
    "Loaded text-rule + file-rule selections from one declarative rules directory."
    type DomainResult = m.BaseModel | InfraValue
    "Typed service result payload: model or validated JSON value."
    type DomainResultSequence = Sequence[DomainResult]
    "Read-only sequence of typed service result payloads."
    type DomainOutput = DomainResult | DomainResultSequence
    "Single or batched service result payload for infra services."

    # ── Transformer / edit result types ──────────────────────────────

    type TransformResult = tuple[str, t.StrSequence]
    "Canonical (new_source, change_descriptions) from any source transformer."
    type EditResult = tuple[bool, t.StrSequence]
    "Validated edit outcome: (success, report_lines)."
    type EditResultWithDescs = tuple[bool, t.StrSequence, t.StrSequence]
    "(success, descriptions, report_lines) — includes what was attempted."
    type LintSnapshot = Mapping[str, t.StrSequence]
    "Lint errors per tool: {tool_name: [error_lines]}."
