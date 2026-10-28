"""Extracted facade class for codemod.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra._utilities._codemod import (
    FlextInfraUtilitiesCodemodImportLawRules,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesCodemodProjectFacts,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesCodemodScopes,
    FlextInfraUtilitiesCodemodTypeSetRules,
)


class FlextInfraUtilitiesCodemod(
    FlextInfraUtilitiesCodemodImportLawRules,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesCodemodProjectFacts,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesCodemodScopes,
    FlextInfraUtilitiesCodemodTypeSetRules,
):
    """Facade for codemod."""


__all__: list[str] = ["FlextInfraUtilitiesCodemod"]
