"""Census models for the refactor subpackage."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import m
from flext_infra import c, t


class FlextInfraRefactorModelsCensus:
    """Census and MRO models for the refactor engine."""

    # -- MRO Generic Models ----------------------------------------------------

    class MROFamilyTarget(m.ArbitraryTypesModel):
        """Parametrized target for an MRO family scan or operations."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        family: Annotated[
            t.NonEmptyStr,
            Field(description="Family alias letter (c/t/p/m/u)"),
        ]
        class_suffix: Annotated[
            str,
            Field(description="Class name suffix (e.g. 'Utilities')"),
        ]
        package_dir: Annotated[
            str,
            Field(
                description="Relative path to _xxx package dir (e.g. 'flext_core/_utilities')",
            ),
        ]
        facade_module: Annotated[
            str,
            Field(
                description="Relative path to facade (e.g. 'flext_core/utilities.py')",
            ),
        ]
        facade_class_prefix: Annotated[
            str,
            Field(
                default="Flext",
                description="Class name prefix for facade (e.g. 'Flext')",
            ),
        ] = "Flext"
        core_project: Annotated[
            str,
            Field(
                default=c.Infra.Packages.CORE,
                description="Core project directory name",
            ),
        ] = c.Infra.Packages.CORE

    # -- Census Models ---------------------------------------------------------

    class CensusMethodInfo(m.ArbitraryTypesModel):
        """A public method extracted from a _utilities class."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        method_type: Annotated[
            str,
            Field(description="Method kind: static, class, instance"),
        ]
        source_file: Annotated[str, Field(description="Source filename")]

    class CensusUsageRecord(m.ArbitraryTypesModel):
        """A single method usage found via CST analysis."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Utilities class name"),
        ]
        method_name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        access_mode: Annotated[
            str,
            Field(description="Access mode: alias_flat, alias_namespaced, direct"),
        ]
        file_path: Annotated[str, Field(description="Source file path")]
        project: Annotated[str, Field(description="Project name")]

    class CensusMethodSummary(m.ArbitraryTypesModel):
        """Aggregated usage counts for a single method."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        method_type: Annotated[str, Field(description="Method kind")]
        alias_flat: Annotated[t.NonNegativeInt, Field(description="u.method count")]
        alias_namespaced: Annotated[
            t.NonNegativeInt,
            Field(description="u.Class.method count"),
        ]
        direct: Annotated[
            t.NonNegativeInt,
            Field(description="Direct class.method count"),
        ]
        total: Annotated[t.NonNegativeInt, Field(description="Total usages")]

    class CensusClassSummary(m.ArbitraryTypesModel):
        """Aggregated census for one _utilities class."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Utilities class name"),
        ]
        source_file: Annotated[str, Field(description="Source filename")]
        methods: tuple[FlextInfraRefactorModelsCensus.CensusMethodSummary, ...] = Field(
            default_factory=tuple, description="Method summaries"
        )

    class CensusProjectMethodUsage(m.ArbitraryTypesModel):
        """Usage of a method within a specific project."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Utilities class name"),
        ]
        method_name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        access_mode: Annotated[str, Field(description="Access mode")]
        count: Annotated[t.NonNegativeInt, Field(description="Usage count")]

    class CensusProjectSummary(m.ArbitraryTypesModel):
        """Usage breakdown for one project."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        project_name: Annotated[
            t.NonEmptyStr,
            Field(description="Project directory name"),
        ]
        usages: Sequence[FlextInfraRefactorModelsCensus.CensusProjectMethodUsage] = (
            Field(default_factory=tuple, description="Per-method usages")
        )
        total: Annotated[t.NonNegativeInt, Field(description="Total usages in project")]

    class UtilitiesCensusReport(m.ArbitraryTypesModel):
        """Full census report for _utilities method usage."""

        classes: tuple[FlextInfraRefactorModelsCensus.CensusClassSummary, ...] = Field(
            default_factory=tuple, description="Per-class summaries"
        )
        projects: tuple[FlextInfraRefactorModelsCensus.CensusProjectSummary, ...] = (
            Field(default_factory=tuple, description="Per-project breakdowns")
        )
        total_classes: Annotated[
            t.NonNegativeInt,
            Field(description="Number of utility classes"),
        ]
        total_methods: Annotated[
            t.NonNegativeInt,
            Field(description="Number of public methods"),
        ]
        total_usages: Annotated[
            t.NonNegativeInt,
            Field(description="Total usage records"),
        ]
        total_unused: Annotated[
            t.NonNegativeInt,
            Field(description="Methods with zero usages"),
        ]
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]
        parse_errors: Annotated[
            t.NonNegativeInt,
            Field(description="Files that failed to parse"),
        ]


__all__ = ["FlextInfraRefactorModelsCensus"]
