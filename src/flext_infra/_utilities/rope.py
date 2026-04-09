"""Public Rope facade."""

from __future__ import annotations

from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraUtilitiesRope(
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeAnalysisIntrospection,
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeSource,
):
    """Public Rope facade exposed via ``u.Infra.*``."""
