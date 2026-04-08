"""Public Rope facade."""

from __future__ import annotations

from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraUtilitiesRope(
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeSource,
):
    """Public Rope facade exposed via ``u.Infra.*``."""


__all__ = ["FlextInfraUtilitiesRope"]
