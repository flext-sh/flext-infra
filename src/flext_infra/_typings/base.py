"""Base typings for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence


class FlextInfraTypesBase:
    """Base typings for flext-infra project."""

    type InfraValue = (
        str
        | int
        | float
        | bool
        | Mapping[str, FlextInfraTypes.Infra.InfraValue]  # noqa: F821
        | Sequence[FlextInfraTypes.Infra.InfraValue]  # noqa: F821
        | None
    )
    "Recursive infrastructure value: primitive, nested dict/list, or null."
    type ContainerDict = Mapping[str, InfraValue]
    "Dict with string keys and infra values (project reports, etc.)."
    type FacadeFamily = str
    "Facade family identifier for MRO chain resolution."
    type ExpectedBase = type | str
    "Expected MRO base: a class or its qualified name."
    type PolicyContext = Mapping[str, ContainerDict]
    "Class-nesting policy matrix keyed by module family."
    type MetricValue = FlextTypes.Scalar | Path | None  # noqa: F821
    "Output metric value: scalar (str/int/float/bool/datetime), path, or null."
    type MetricRecord = BaseModel | Mapping[str, MetricValue]  # noqa: F821
    "A single metric record: a Pydantic model or a string-keyed mapping of metric values."
    type ChangeCallback = Callable[[str], None] | None
    "Optional callback invoked on transformer changes."
    type StrIndex = Mapping[str, int]
    "String-keyed integer index (counters, metrics)."
    type MutableStrIndex = MutableMapping[str, int]
    "Mutable string-keyed integer index."
