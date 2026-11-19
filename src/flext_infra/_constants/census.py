"""Constants for the unified census pipeline — accessed via c.Infra.*.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping
from enum import StrEnum, unique
from types import MappingProxyType
from typing import ClassVar


class FlextInfraConstantsCensus:
    """Census pipeline constants for object detection and classification."""

    @unique
    class ProtocolOrigin(StrEnum):
        """Canonical source categories of structural contracts."""

        MODEL = "model"
        SERVICE = "service"
        EXTERNAL = "external"
        UNRESOLVED = "unresolved"

    DUPLICATE_BUILTIN_NAMES: ClassVar[frozenset[str]] = frozenset(dir(builtins))
    "Native builtin bindings available to pure duplicate definitions."
    DUPLICATE_PURE_CONSTRUCTORS: ClassVar[frozenset[str]] = frozenset({
        "bool",
        "bytes",
        "complex",
        "dict",
        "float",
        "frozenset",
        "int",
        "list",
        "range",
        "set",
        "str",
        "tuple",
    })
    "Builtin constructors admitted by the duplicate purity grammar."
    DUPLICATE_TRIVIAL_KINDS: ClassVar[frozenset[str]] = frozenset({
        "assignment",
        "class",
        "constant",
        "function",
    })
    "Census object kinds supporting identity-proven cure planning."
    DUPLICATE_DELETE_ACTION: ClassVar[str] = "delete-copy"
    "Removal action recorded by the public duplicate cure receipt."
    DUPLICATE_REBIND_ACTION: ClassVar[str] = "rebind-import"
    "Consumer import migration action."
    DUPLICATE_BIND_ACTION: ClassVar[str] = "bind-owner"
    "Binding of the elected duplicate owner."
    DUPLICATE_KEEP_ACTION: ClassVar[str] = "keep-owner"
    "Preservation of the elected duplicate owner."

    @unique
    class CensusRule(StrEnum):
        """Stable analysis identifiers shared by census and semantic planning."""

        DUPLICATE = "duplicate"
        UNUSED = "unused"
        WRONG_TIER = "wrong_tier"
        CONSTANT_CONSUMERS = "constant-consumers"
        COMPAT_ALIAS = "compat-alias"
        ALIAS_CHAIN = "alias-chain"
        DUPLICATE_DECLARATION = "duplicate-declaration"
        BLOAT_WRAPPER = "bloat-wrapper"
        PYDANTIC = "pydantic"

    @unique
    class PydanticLiteralKind(StrEnum):
        """Closed-domain classification of one ``Literal`` annotation."""

        FULL_DOMAIN = "full-domain"
        SUBSET = "subset"
        DISCRIMINATOR = "discriminator"

    CENSUS_PYDANTIC_SELECTORS: ClassVar[frozenset[str]] = frozenset({
        CensusRule.PYDANTIC,
    })
    "Extermination kinds selecting the Pydantic domain census."
    CENSUS_PYDANTIC_CODE: ClassVar[str] = "pydantic-census"
    "Finding code of the Pydantic domain census gate."
    PYDANTIC_MODEL_SUFFIX: ClassVar[str] = "Model"
    "Suffix that marks a concrete model declaration without a preset base."
    PYDANTIC_RAW_MODEL_NAME: ClassVar[str] = "BaseModel"
    "The raw Pydantic base a preset must replace."
    PYDANTIC_STR_ENUM_NAME: ClassVar[str] = "StrEnum"
    "The closed-domain enum base."
    PYDANTIC_LITERAL_NAME: ClassVar[str] = "Literal"
    "The inline closed-domain annotation that a full-domain literal abuses."
    PYDANTIC_ANNOTATED_NAME: ClassVar[str] = "Annotated"
    "The annotation wrapper that carries field metadata."
    PYDANTIC_UNION_NAME: ClassVar[str] = "Union"
    "The union wrapper that makes a literal a subset or discriminator."
    PYDANTIC_PROTOCOL_DIRECTORY: ClassVar[str] = "_protocols"
    "The generated projection directory compared against models."
    PYDANTIC_SUBSCRIPT_KIND: ClassVar[str] = "Subscript"
    "Native node kind of a ``Literal[...]`` annotation."
    PYDANTIC_CONSTANT_KIND: ClassVar[str] = "Constant"
    "Native node kind of one literal value element."

    CENSUS_ALIAS_SELECTORS: ClassVar[frozenset[str]] = frozenset({
        "alias",
        CensusRule.COMPAT_ALIAS,
        CensusRule.ALIAS_CHAIN,
    })
    "Extermination kinds selecting compatibility-alias rows."
    CENSUS_DUPLICATE_SELECTORS: ClassVar[frozenset[str]] = frozenset({
        "duplicate",
        CensusRule.DUPLICATE_DECLARATION,
    })
    "Extermination kinds selecting duplicate-declaration rows."
    CENSUS_SHORTEST_SELECTORS: ClassVar[frozenset[str]] = frozenset({
        "shortest",
        "ceremony",
        CensusRule.BLOAT_WRAPPER,
    })
    "Extermination kinds selecting shortest-form rows."
    CENSUS_ALIAS_CURE: ClassVar[str] = "ban-compat-alias"
    "Owned cure of a compatibility alias: the compat-alias semantic cutover."
    CENSUS_DUPLICATE_CURE: ClassVar[str] = "duplicate-apply"
    "Owned cure of an identity-proven duplicate: the mod duplicate phase."
    CENSUS_MANUAL_CURE: ClassVar[str] = "manual-review"
    "Rows without an owned automatic cure."
    CENSUS_CURE_COMMANDS: ClassVar[Mapping[str, str]] = MappingProxyType({
        "ban-compat-alias": "make mod RULES=ban-compat-alias",
        "duplicate-apply": "make mod",
    })
    "Individual validation command of each owned cure."
    CENSUS_MIN_REPEATED_EXPORTS: ClassVar[int] = 2
    "Occurrences that make one ``__all__`` entry a duplicate."
    CENSUS_FAMILY_NAMES: ClassVar[frozenset[str]] = frozenset({
        "c",
        "t",
        "p",
        "m",
        "u",
        "e",
        "s",
        "h",
        "d",
        "r",
        "x",
    })
    "Canonical facade family letters; rebinding one to an own class is lawful."
    CENSUS_ENTRYPOINT_NAMES: ClassVar[frozenset[str]] = frozenset({"main"})
    "Console entrypoint callables that may forward to the CLI owner."
    CENSUS_FAMILY_ALIAS_KIND: ClassVar[str] = "family-import-alias"
    "Import alias of another package's facade family (largest fleet deviation)."

    CENSUS_UNSUPPORTED_SIMPLE_REMOVAL_CODE: ClassVar[str] = (
        "CENSUS_UNSUPPORTED_SIMPLE_REMOVAL"
    )
    "Error code marking a candidate outside the simple-removal contract."


__all__: list[str] = ["FlextInfraConstantsCensus"]
