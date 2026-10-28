"""Composed rope analysis base joining the domain responsibility classes.

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

from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope._analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._rope._analysis.importstate import (
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._rope._analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)


class FlextInfraUtilitiesRopeAnalysisBase(
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
    FlextInfraUtilitiesRopeAnalysisSourceScan,
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
):
    """Rope-backed semantic analysis composed from its domain responsibilities."""


__all__: tuple[str, ...] = ("FlextInfraUtilitiesRopeAnalysisBase",)
