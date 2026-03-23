"""Type aliases for flext-infra.

Re-exports and extends flext_core typings for infrastructure services.
Infra-specific type aliases live inside ``FlextInfraTypes`` so they are
accessed via ``t.Infra.Payload``, ``t.Infra.PayloadMap``, etc.

Non-recursive aliases use ``type X = ...`` (PEP 695 Python 3.13+ syntax).
See AGENTS.md §3 AXIOMATIC rule.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_core import FlextTypes
from pydantic import BaseModel

from flext_infra import c


class FlextInfraTypes(FlextTypes):
    """Type namespace for flext-infra; extends FlextTypes via MRO.

    Infra-specific types are nested under the ``Infra`` inner class to
    keep the namespace explicit (``t.Infra.Payload``, ``t.Infra.StrMap``).
    Parent types (``t.Scalar``, ``t.Container``, etc.) are inherited
    transparently from ``FlextTypes`` via MRO.
    """

    class Infra:
        """Infrastructure-domain type aliases.

        These aliases compose ``FlextTypes.Scalar`` and collection generics
        for infrastructure payload contracts and common patterns.
        """

        type StrMap = Mapping[str, str]
        "Mutable string-to-string mapping (symbol replacements, renames)."
        type InfraValue = (
            str
            | int
            | float
            | bool
            | None
            | Mapping[str, FlextInfraTypes.Infra.InfraValue]
            | Sequence[FlextInfraTypes.Infra.InfraValue]
        )
        "Recursive infrastructure value: primitive, nested dict/list, or null."
        type ContainerDict = Mapping[str, InfraValue]
        "Dict with string keys and infra values (project reports, etc.)."
        type TomlValue = (
            str
            | int
            | float
            | bool
            | None
            | Mapping[str, InfraValue]
            | Sequence[InfraValue]
        )
        "Recursive TOML value (scalar, table, or array)."
        type TomlConfig = Mapping[str, InfraValue]
        "Top-level TOML document mapping."
        type IssueMap = Mapping[str, InfraValue]
        "Dependency issue mapping: string-keyed mapping of infra values."
        type RuleConfig = Mapping[str, InfraValue]
        "A single rule configuration dict (parsed from TOML/YAML)."
        type FacadeFamily = c.FacadeFamily
        "Facade family identifier for MRO chain resolution."
        type ExpectedBase = type | str
        "Expected MRO base: a class or its qualified name."
        type PolicyContext = Mapping[str, ContainerDict]
        "Class-nesting policy matrix keyed by module family."
        type ClassFamilyMap = Mapping[str, str]
        "Mapping from symbol name to resolved module family."
        type MetricValue = FlextTypes.Scalar | Path | None
        "Output metric value: scalar (str/int/float/bool/datetime), path, or null."
        type MetricRecord = BaseModel | Mapping[str, MetricValue]
        "A single metric record: a Pydantic model or a string-keyed mapping of metric values."


t = FlextInfraTypes
__all__ = ["FlextInfraTypes", "t"]
