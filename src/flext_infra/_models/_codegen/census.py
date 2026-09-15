"""Census violation models for the codegen reporting domain."""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from .. import FlextInfraModelsMixins as mm
from ... import t


class FlextInfraModelsCodegenCensus:
    """Private codegen census model domain partial."""

    class CensusViolation(mm.RequiredNonNegativeLineMixin, m.ArbitraryTypesModel):
        """A single namespace violation detected by the census service."""

        module: t.NonEmptyStr = m.Field(description="Module file path")
        rule: t.NonEmptyStr = m.Field(
            description="Violated rule identifier (e.g. NS-001)"
        )
        message: t.NonEmptyStr = m.Field(description="Human-readable violation message")
        fixable: bool = m.Field(description="Whether this violation can be auto-fixed")

    class CensusReport(mm.ProjectNameMixin, m.ArbitraryTypesModel):
        """Aggregated census report for a single project."""

        @staticmethod
        def _violations_default() -> list[
            FlextInfraModelsCodegenCensus.CensusViolation
        ]:
            """Violations default."""
            return []

        violations: Annotated[
            list[FlextInfraModelsCodegenCensus.CensusViolation],
            m.Field(
                default_factory=_violations_default, description="Detected violations"
            ),
        ]
        total: Annotated[t.NonNegativeInt, m.Field(description="Total violation count")]
        fixable: Annotated[
            t.NonNegativeInt, m.Field(description="Count of auto-fixable violations")
        ]
