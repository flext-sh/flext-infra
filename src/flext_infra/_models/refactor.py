"""Domain models for the refactor subpackage."""

from __future__ import annotations

from collections.abc import (
    Mapping,
    MutableSet,
)
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m
from flext_infra import (
    FlextInfraModelsMixins as mm,
    FlextInfraModelsNamespaceEnforcer,
    FlextInfraModelsRefactorCensus,
    FlextInfraModelsRefactorGrep,
    FlextInfraModelsRefactorViolations,
    t,
)


class FlextInfraModelsRefactor(
    FlextInfraModelsRefactorGrep,
    FlextInfraModelsNamespaceEnforcer,
    FlextInfraModelsRefactorCensus,
    FlextInfraModelsRefactorViolations,
):
    """Models for the refactor engine and related tools.

    Canonical base policy:
    - ``ContractModel`` for configuration/policy contracts.
    - ``ArbitraryTypesModel`` for mutable engine/report/result payloads.
    """

    class RefactorMigrateMroInput(
        mm.WriteMixin,
        m.ContractModel,
    ):
        """CLI/service request for MRO migration."""

        target: Annotated[
            str,
            m.Field(
                description="Migration target scope (constants/typings/protocols/models/utilities/all)",
            ),
        ] = "all"

    class RefactorNamespaceEnforceInput(
        mm.WriteMixin,
        m.ContractModel,
    ):
        """CLI/service request for namespace enforcement."""

    class AccessorMigrationInput(
        mm.WriteMixin,
        m.ContractModel,
    ):
        """CLI/service request for accessor migration dry-runs and applies."""

        preview_limit: Annotated[
            t.PositiveInt,
            m.Field(
                alias="preview-limit",
                description="Maximum number of file previews to include in the report",
            ),
        ] = 10

    class Result(m.ArbitraryTypesModel):
        """Result of applying refactor rules to a single file."""

        file_path: Annotated[Path, m.Field(description="Target file path")]
        success: Annotated[bool, m.Field(description="Whether the operation succeeded")]
        modified: Annotated[
            bool,
            m.Field(description="Whether the file was actually modified"),
        ]
        error: Annotated[
            str | None, m.Field(description="Error message on failure")
        ] = None
        changes: Annotated[
            t.StrSequence,
            m.Field(
                description="Human-readable change descriptions",
            ),
        ] = m.Field(default_factory=tuple)
        refactored_code: Annotated[
            str | None,
            m.Field(
                description="Resulting source code after transformation",
            ),
        ] = None

    class RefactorProjectInfo(m.ArbitraryTypesModel):
        """Project metadata with mutable package-root set.

        Enforcement exemption: ``package_roots`` is a ``set[str]``
        accumulator populated during scanning.
        """

        name: Annotated[t.NonEmptyStr, m.Field(description="Project directory name")]
        path: Annotated[Path, m.Field(description="Absolute project path")]
        src_path: Annotated[Path, m.Field(description="Absolute src/ path")]
        package_roots: Annotated[
            MutableSet[str],
            m.Field(
                description="Top-level Python package roots in src/",
            ),
        ] = m.Field(default_factory=set)

    class FileImportData(m.ArbitraryTypesModel):
        """File-level import data with mutable set accumulators.

        Enforcement exemption: ``imported_modules``/``imported_symbols``
        accumulate during a scan; keep ``set[str]`` as the declared type.
        """

        imported_modules: Annotated[
            MutableSet[str],
            m.Field(description="Imported module roots"),
        ] = m.Field(default_factory=set)
        imported_symbols: Annotated[
            MutableSet[str],
            m.Field(description="Imported symbol names"),
        ] = m.Field(default_factory=set)

    class MethodInfo(m.ArbitraryTypesModel):
        """Metadata about a method used for ordering inside classes."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Method name")]
        category: Annotated[str, m.Field(description="Method category classification")]
        node: Annotated[
            t.Infra.AstMethodNode,
            m.Field(
                description="Node representation from Rope or PyObject",
                exclude=True,
            ),
        ]
        decorators: Annotated[
            t.StrSequence,
            m.Field(description="Decorator names applied to this method"),
        ] = m.Field(default_factory=tuple)

    class Checkpoint(
        mm.StashRefMixin,
        m.ArbitraryTypesModel,
    ):
        """Serialisable checkpoint state for refactor safety recovery."""

        workspace_root: Annotated[
            t.NonEmptyStr,
            m.Field(description="Workspace root path"),
        ]
        status: Annotated[str, m.Field(description="Checkpoint status")] = "running"
        processed_targets: Annotated[
            t.StrSequence,
            m.Field(description="Already-processed file targets"),
        ] = m.Field(default_factory=tuple)
        updated_at: Annotated[
            str,
            m.Field(description="ISO 8601 timestamp of last update"),
        ] = m.Field(default_factory=lambda: datetime.now(UTC).isoformat())

    class ClassOccurrence(m.ArbitraryTypesModel):
        """A single class definition occurrence within a source file."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, m.Field(description="Class name")]
        line: Annotated[
            t.NonNegativeInt, m.Field(description="Line number (0 = unknown)")
        ]
        is_top_level: Annotated[
            bool,
            m.Field(description="Whether class is at module top level"),
        ]

    class LooseClassViolation(m.ArbitraryTypesModel):
        """A detected loose-class naming violation with confidence."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, m.Field(description="Source file path")]
        line: Annotated[t.PositiveInt, m.Field(description="Line number")]
        class_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Violating class name"),
        ]
        expected_prefix: Annotated[
            str, m.Field(description="Expected namespace prefix")
        ]
        rule: Annotated[t.NonEmptyStr, m.Field(description="Violated rule id")]
        reason: Annotated[str, m.Field(description="Human-readable reason")]
        confidence: Annotated[str, m.Field(description="Confidence level")]
        score: Annotated[t.DecimalFraction, m.Field(description="Confidence score")]

    class FamilyMROResolution(m.ArbitraryTypesModel):
        """Resolution payload for one facade family MRO."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        family: Annotated[t.NonEmptyStr, m.Field(description="Facade family letter")]
        expected_bases: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Expected base class names in order"),
        ]
        resolved_mro: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Resolved MRO class names"),
        ]
        accessible_namespaces: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Namespaces accessible through the MRO"),
        ]

    class ProjectClassification(m.ArbitraryTypesModel):
        """Result of classifying a project by kind and family chains."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        project_kind: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Project kind (core, domain, platform, integration, app)"
            ),
        ]
        family_chains: Annotated[
            Mapping[str, t.StrSequence],
            m.Field(description="Family letter to MRO chain mapping"),
        ]

    # -- MRO Target Specification -----------------------------------------------

    class MROTargetSpec(m.ContractModel):
        """Specification for an MRO target family."""

        family_alias: Annotated[
            t.NonEmptyStr, m.Field(description="Family alias letter")
        ]
        file_names: Annotated[frozenset[str], m.Field(description="File name patterns")]
        package_directory: Annotated[
            t.NonEmptyStr,
            m.Field(description="Package directory name"),
        ]
        class_suffix: Annotated[t.NonEmptyStr, m.Field(description="Class suffix")]

    # -- Namespace Enforcer Models ---------------------------------------------

    class ParsedPythonModule(m.ArbitraryTypesModel):
        """Result of parsing a Python source file into AST."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        source: Annotated[str, m.Field(description="Raw source text")]
        tree: Annotated[
            t.Infra.AstModule,
            m.Field(description="Parsed PyObject module representation"),
        ]


__all__: list[str] = ["FlextInfraModelsRefactor"]
