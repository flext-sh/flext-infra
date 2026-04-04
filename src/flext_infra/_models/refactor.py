"""Domain models for the refactor subpackage."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import m
from flext_infra import (
    FlextInfraNamespaceEnforcerModels,
    FlextInfraRefactorGrepModels,
    FlextInfraRefactorModelsCensus,
    FlextInfraRefactorModelsViolations,
    t,
)
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraRefactorModels(
    FlextInfraRefactorGrepModels,
    FlextInfraNamespaceEnforcerModels,
    FlextInfraRefactorModelsCensus,
    FlextInfraRefactorModelsViolations,
):
    """Models for the refactor engine and related tools.

    Canonical base policy:
    - ``ContractModel`` for configuration/policy contracts.
    - ``ArbitraryTypesModel`` for mutable engine/report/result payloads.
    """

    class Result(m.ArbitraryTypesModel):
        """Result of applying refactor rules to a single file."""

        file_path: Annotated[Path, Field(description="Target file path")]
        success: Annotated[bool, Field(description="Whether the operation succeeded")]
        modified: Annotated[
            bool,
            Field(description="Whether the file was actually modified"),
        ]
        error: Annotated[
            str | None,
            Field(default=None, description="Error message on failure"),
        ] = None
        changes: Annotated[
            t.StrSequence,
            Field(
                description="Human-readable change descriptions",
            ),
        ] = Field(default_factory=list)
        refactored_code: Annotated[
            str | None,
            Field(
                default=None,
                description="Resulting source code after transformation",
            ),
        ]

    class RefactorProjectInfo(m.ArbitraryTypesModel):
        name: Annotated[t.NonEmptyStr, Field(description="Project directory name")]
        path: Annotated[Path, Field(description="Absolute project path")]
        src_path: Annotated[Path, Field(description="Absolute src/ path")]
        package_roots: Annotated[
            t.Infra.StrSet,
            Field(
                description="Top-level Python package roots in src/",
            ),
        ] = Field(default_factory=set)

    class FileImportData(m.ArbitraryTypesModel):
        imported_modules: Annotated[
            t.Infra.StrSet,
            Field(description="Imported module roots"),
        ] = Field(default_factory=set)
        imported_symbols: Annotated[
            t.Infra.StrSet,
            Field(description="Imported symbol names"),
        ] = Field(default_factory=set)

    class MethodInfo(m.ArbitraryTypesModel):
        """Metadata about a method used for ordering inside classes."""

        name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        category: Annotated[str, Field(description="Method category classification")]
        node: Annotated[
            t.Infra.AstMethodNode,
            Field(
                description="Node representation from Rope or PyObject",
                exclude=True,
            ),
        ]
        decorators: Annotated[
            t.StrSequence,
            Field(description="Decorator names applied to this method"),
        ] = Field(default_factory=list)

    class Checkpoint(
        FlextInfraModelsMixins.StashRefMixin,
        m.ArbitraryTypesModel,
    ):
        """Serialisable checkpoint state for refactor safety recovery."""

        workspace_root: Annotated[
            t.NonEmptyStr,
            Field(description="Workspace root path"),
        ]
        status: Annotated[
            str,
            Field(default="running", description="Checkpoint status"),
        ] = "running"
        processed_targets: Annotated[
            t.StrSequence,
            Field(description="Already-processed file targets"),
        ] = Field(default_factory=list)
        updated_at: Annotated[
            str,
            Field(description="ISO 8601 timestamp of last update"),
        ] = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    class ClassOccurrence(m.ArbitraryTypesModel):
        """A single class definition occurrence within a source file."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        line: Annotated[
            t.NonNegativeInt, Field(description="Line number (0 = unknown)")
        ]
        is_top_level: Annotated[
            bool,
            Field(description="Whether class is at module top level"),
        ]

    class LooseClassViolation(m.ArbitraryTypesModel):
        """A detected loose-class naming violation with confidence."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source file path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Violating class name"),
        ]
        expected_prefix: Annotated[str, Field(description="Expected namespace prefix")]
        rule: Annotated[t.NonEmptyStr, Field(description="Violated rule id")]
        reason: Annotated[str, Field(description="Human-readable reason")]
        confidence: Annotated[str, Field(description="Confidence level")]
        score: Annotated[t.DecimalFraction, Field(description="Confidence score")]

    class FamilyMROResolution(m.ArbitraryTypesModel):
        """Resolution payload for one facade family MRO."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        family: Annotated[t.NonEmptyStr, Field(description="Facade family letter")]
        expected_bases: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Expected base class names in order"),
        ]
        resolved_mro: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Resolved MRO class names"),
        ]
        accessible_namespaces: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Namespaces accessible through the MRO"),
        ]

    class ProjectClassification(m.ArbitraryTypesModel):
        """Result of classifying a project by kind and family chains."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        project_kind: Annotated[
            t.NonEmptyStr,
            Field(
                description="Project kind (core, domain, platform, integration, app)"
            ),
        ]
        family_chains: Annotated[
            Mapping[str, t.StrSequence],
            Field(description="Family letter to MRO chain mapping"),
        ]

    # -- MRO Target Specification -----------------------------------------------

    class MROTargetSpec(m.ContractModel):
        """Specification for an MRO target family."""

        family_alias: Annotated[t.NonEmptyStr, Field(description="Family alias letter")]
        file_names: Annotated[frozenset[str], Field(description="File name patterns")]
        package_directory: Annotated[
            t.NonEmptyStr,
            Field(description="Package directory name"),
        ]
        class_suffix: Annotated[t.NonEmptyStr, Field(description="Class suffix")]

    # -- Pydantic Centralizer Models -------------------------------------------

    class ClassMove(m.ContractModel):
        """Tracks a class definition being moved during centralization."""

        name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        start: Annotated[t.NonNegativeInt, Field(description="Start line number")]
        end: Annotated[t.NonNegativeInt, Field(description="End line number")]
        source: Annotated[str, Field(description="Source code text")]
        kind: Annotated[t.NonEmptyStr, Field(description="Model kind classification")]

    class AliasMove(m.ContractModel):
        """Tracks a type alias being moved during centralization."""

        name: Annotated[t.NonEmptyStr, Field(description="Alias name")]
        start: Annotated[t.NonNegativeInt, Field(description="Start line number")]
        end: Annotated[t.NonNegativeInt, Field(description="End line number")]
        alias_expr: Annotated[str, Field(description="Alias expression text")]

    class CentralizerFailureStats(m.ArbitraryTypesModel):
        """Mutable statistics for centralizer parse failures."""

        parse_syntax_errors: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Syntax error count"),
        ] = 0
        parse_encoding_errors: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Encoding error count"),
        ] = 0
        parse_io_errors: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="I/O error count"),
        ] = 0

    class CentralizerFileResult(m.ArbitraryTypesModel):
        """Result of processing a single file for model centralization."""

        found_models: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Detected model violations"),
        ] = 0
        found_aliases: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Detected alias violations"),
        ] = 0
        skipped_non_necessary: Annotated[
            bool,
            Field(
                default=False,
                description="Whether the file was skipped as non-necessary",
            ),
        ] = False
        apply_class_moves: list[FlextInfraRefactorModels.ClassMove] = Field(
            default_factory=list, description="Class moves to apply"
        )
        apply_alias_moves: list[FlextInfraRefactorModels.AliasMove] = Field(
            default_factory=list, description="Alias moves to apply"
        )

    # -- Namespace Enforcer Models ---------------------------------------------

    class ParsedPythonModule(m.ArbitraryTypesModel):
        """Result of parsing a Python source file into AST."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        source: Annotated[str, Field(description="Raw source text")]
        tree: Annotated[
            t.Infra.AstModule,
            Field(description="Parsed PyObject module representation"),
        ]


__all__ = ["FlextInfraRefactorModels"]
