"""Domain models for the core subpackage."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from flext_cli import m
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsCore:
    """Models for core infrastructure services (subprocess, validation).

    Canonical base policy:
    - ``ArbitraryTypesModel`` for mutable report/result payloads.
    - ``ContractModel`` reserved for immutable settings/settings contracts.
    """

    class ValidationReport(m.ArbitraryTypesModel):
        """Validation report model with violations and summary."""

        passed: Annotated[bool, m.Field(description="Validation status")]
        violations: Annotated[
            t.StrSequence, m.Field(description="Collected validation violations")
        ] = m.Field(default_factory=tuple)
        summary: Annotated[
            str, m.Field(description="Human-readable validation summary")
        ] = ""

    class SkillRuleEvaluationContext(m.ArbitraryTypesModel):
        """Resolved inputs for one skill rule evaluation pass."""

        rules_list: Annotated[t.JsonList, m.Field(description="Rules to evaluate")]
        skill_dir: Annotated[Path, m.Field(description="Skill directory path")]
        root: Annotated[Path, m.Field(description="Workspace root path")]
        mode: Annotated[
            c.Infra.OperationMode, m.Field(description="Skill validation mode")
        ]
        include_globs: Annotated[t.StrSequence, m.Field(description="Include globs")]
        exclude_globs: Annotated[t.StrSequence, m.Field(description="Exclude globs")]

    class SkillReportContext(m.ArbitraryTypesModel):
        """Resolved inputs for one skill validation report."""

        rules: Annotated[
            t.MappingKV[str, t.Infra.InfraValue], m.Field(description="Rules payload")
        ]
        root: Annotated[Path, m.Field(description="Workspace root path")]
        skill_name: Annotated[str, m.Field(description="Skill folder name")]
        mode: Annotated[
            c.Infra.OperationMode, m.Field(description="Skill validation mode")
        ]
        counts: Annotated[t.IntMapping, m.Field(description="Violation counts")]
        violations: Annotated[t.StrSequence, m.Field(description="Violations")]

    class StubAnalysisReport(mm.ProjectNameMixin, m.ArbitraryTypesModel):
        """Structured typed-dependency analysis result for a project."""

        mypy_hints: Annotated[
            t.MutableSequenceOf[str],
            m.Field(description="Install-package hints extracted from mypy output"),
        ] = m.Field(default_factory=list)
        internal_missing: Annotated[
            t.MutableSequenceOf[str], m.Field(description="Missing internal imports")
        ] = m.Field(default_factory=list)
        unresolved_missing: Annotated[
            t.MutableSequenceOf[str],
            m.Field(
                description="Missing external imports without an installed typed dependency"
            ),
        ] = m.Field(default_factory=list)
        total_missing: Annotated[
            t.NonNegativeInt, m.Field(description="Total missing imports")
        ]

    class PytestDiagnostics(m.ArbitraryTypesModel):
        """Extracted diagnostics summary from junit XML and pytest logs."""

        failed_count: Annotated[
            t.NonNegativeInt, m.Field(description="Failed test case count")
        ]
        error_count: Annotated[
            t.NonNegativeInt, m.Field(description="Errored test case count")
        ]
        warning_count: Annotated[
            t.NonNegativeInt, m.Field(description="Warning line count")
        ]
        skipped_count: Annotated[
            t.NonNegativeInt, m.Field(description="Skipped test case count")
        ]
        failed_cases: Annotated[
            t.StrSequence, m.Field(description="Failed test labels")
        ] = m.Field(default_factory=tuple)
        error_traces: Annotated[
            t.StrSequence, m.Field(description="Collected error traces")
        ] = m.Field(default_factory=tuple)
        warning_lines: Annotated[
            t.StrSequence, m.Field(description="Captured warning lines")
        ] = m.Field(default_factory=tuple)
        skip_cases: Annotated[
            t.StrSequence, m.Field(description="Skipped test labels")
        ] = m.Field(default_factory=tuple)
        slow_entries: Annotated[
            t.StrSequence, m.Field(description="Slow test entries")
        ] = m.Field(default_factory=tuple)

    class PytestShardManifest(m.ContractModel):
        """One external pytest shard's collection and completion evidence."""

        schema_version: Annotated[
            Literal[1], m.Field(description="Shard manifest schema version")
        ] = 1
        assignment: Annotated[
            Literal["sha256-mod-v1"],
            m.Field(description="Stable nodeid assignment algorithm"),
        ]
        shard_index: Annotated[
            t.NonNegativeInt, m.Field(description="Zero-based external shard index")
        ]
        shard_count: Annotated[
            int, m.Field(ge=2, le=64, description="Total external shard count")
        ]
        max_workers: Annotated[
            int, m.Field(ge=1, le=16, description="Configured xdist worker ceiling")
        ]
        worker_count: Annotated[
            int, m.Field(ge=1, le=16, description="Observed xdist worker collections")
        ]
        full_collection: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Complete unfiltered pytest nodeid collection"),
        ]
        selected_nodeids: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Nodeids assigned to this external shard"),
        ]
        completed_nodeids: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Nodeids whose runtest protocol completed"),
        ]
        outcomes: Annotated[
            t.MappingKV[
                t.NonEmptyStr,
                Literal["passed", "failed", "skipped", "xfailed", "xpassed", "error"],
            ],
            m.Field(
                description="Final pytest outcome recorded for each selected nodeid"
            ),
        ]
        validation_errors: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Fail-closed plugin validation errors"),
        ] = ()

    class PytestShardUnionSummary(m.ContractModel):
        """Verified exact union of every external pytest shard."""

        schema_version: Annotated[
            Literal[1], m.Field(description="Shard union summary schema version")
        ] = 1
        assignment: Annotated[
            Literal["sha256-mod-v1"],
            m.Field(description="Verified stable nodeid assignment algorithm"),
        ]
        shard_count: Annotated[
            int, m.Field(ge=2, le=64, description="Verified shard count")
        ]
        collected_count: Annotated[
            t.NonNegativeInt, m.Field(description="Complete collection size")
        ]
        completed_count: Annotated[
            t.NonNegativeInt, m.Field(description="Exact completed union size")
        ]
        coverage_files: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Coverage data files combined across shards"),
        ] = ()

    class DiagResult(m.ArbitraryTypesModel):
        """Internal container for extracted diagnostics.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        failed_cases: Annotated[
            t.StrSequence, m.Field(description="Collected failed test-case labels")
        ] = m.Field(default_factory=tuple)
        error_traces: Annotated[
            t.StrSequence, m.Field(description="Collected error trace chunks")
        ] = m.Field(default_factory=tuple)
        skip_cases: Annotated[
            t.StrSequence, m.Field(description="Collected skipped test-case labels")
        ] = m.Field(default_factory=tuple)
        warning_lines: Annotated[
            t.StrSequence, m.Field(description="Collected warning lines")
        ] = m.Field(default_factory=tuple)
        slow_entries: Annotated[
            t.StrSequence, m.Field(description="Collected slow-test entries")
        ] = m.Field(default_factory=tuple)

    class InventoryReport(m.ArbitraryTypesModel):
        """Summary of written inventory report artifacts."""

        total_scripts: Annotated[
            t.NonNegativeInt, m.Field(description="Total discovered scripts")
        ]
        reports_written: Annotated[
            t.MutableSequenceOf[str], m.Field(description="Written report file paths")
        ] = m.Field(default_factory=list)

    class NamespaceValidateCommand(mm.ReadMixin, m.ContractModel):
        """CLI payload for ``flext-infra validate namespace``.

        Read-only namespace rule scan (NS-000..003) across selected projects.
        """

        scan_tests: Annotated[
            bool,
            m.Field(
                alias="scan-tests",
                description="Include test packages in the namespace scan",
            ),
        ] = False


__all__: list[str] = ["FlextInfraModelsCore"]
