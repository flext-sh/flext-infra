"""Domain models for the core subpackage."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import m

from .. import c, t, u
from . import FlextInfraModelsMixins as mm
from ._defaults import FlextInfraModelsDefaults


def _default_fresh_import_entry_points() -> FlextInfraModelsCore.FreshImportEntryPoints:
    """Default factory for the fresh-import entry-points payload.

    Module-level on purpose: neither a qualified nor a bare reference to the
    nested model resolves inside the class body at definition time (class
    scopes do not nest, and the outer class is still being defined), so the
    deferred lookup must live outside it.
    """
    return FlextInfraModelsCore.FreshImportEntryPoints()


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

    class FreshImportProbe(m.Value):
        """One complete child-process verification program and its subject."""

        subject: str = m.Field(description="Public contract verified by this process")
        code: str = m.Field(description="Python program rendered from typed contracts")

    class FreshImportEntryPoints(m.Value):
        """The standardized executable metadata consumed by importlib."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore")

        scripts: t.StrMapping = m.Field(
            default_factory=FlextInfraModelsDefaults.ImmutableEmptyMapping,
            description="Declared console entrypoints",
        )
        gui_scripts: t.StrMapping = m.Field(
            default_factory=FlextInfraModelsDefaults.ImmutableEmptyMapping,
            alias="gui-scripts",
            description="Declared graphical entrypoints",
        )
        entry_points: t.MappingKV[str, t.StrMapping] = m.Field(
            default_factory=FlextInfraModelsDefaults.ImmutableEmptyMapping,
            alias="entry-points",
            description="Declared plugin entrypoint groups",
        )

    class FreshImportMetadata(m.Value):
        """Typed entrypoint view of the published pyproject document."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore")

        project: FlextInfraModelsCore.FreshImportEntryPoints = m.Field(
            default_factory=_default_fresh_import_entry_points,
            description="Executable metadata from the published project table",
        )

    class SkillRuleEvaluationContext(m.ArbitraryTypesModel):
        """Resolved inputs for one skill rule evaluation pass."""

        rules_list: Annotated[t.JsonList, m.Field(description="Rules to evaluate")]
        skill_dir: Annotated[Path, m.Field(description="Skill directory path")]
        root: Annotated[Path, m.Field(description="Repository root path")]
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
        root: Annotated[Path, m.Field(description="Repository root path")]
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

    class PytestReportEvent(m.Value):
        """Common report-log envelope and the complete warning payload."""

        # Report-log event kinds carry different plugin-owned payload fields.
        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="ignore", strict=True)

        report_type: Annotated[
            str, m.Field(alias="$report_type", description="Pytest event kind")
        ]
        category: Annotated[
            str | None, m.Field(description="Warning category name")
        ] = None
        filename: Annotated[
            str | None, m.Field(description="Warning source filename")
        ] = None
        lineno: Annotated[
            int | None, m.Field(ge=0, description="Warning source line")
        ] = None
        message: Annotated[
            str | None, m.Field(description="Complete warning message")
        ] = None

        @u.model_validator(mode="after")
        def require_warning_payload(self) -> Self:
            """Reject incomplete warnings instead of reporting zero findings."""
            if self.report_type == "WarningMessage" and any(
                value is None
                for value in (self.category, self.filename, self.lineno, self.message)
            ):
                msg = "WarningMessage requires category, filename, lineno and message"
                raise ValueError(msg)
            return self

    class PytestDiagnostics(m.ArbitraryTypesModel):
        """Extracted diagnostics summary from JUnit XML and pytest report-log."""

        failed_count: Annotated[
            t.NonNegativeInt, m.Field(description="Failed test case count")
        ]
        error_count: Annotated[
            t.NonNegativeInt, m.Field(description="Errored test case count")
        ]
        warning_count: Annotated[
            t.NonNegativeInt, m.Field(description="Recorded warning event count")
        ]
        blocking_warning_count: Annotated[
            t.NonNegativeInt, m.Field(description="Warnings outside suspended policy")
        ]
        suspended_warning_count: Annotated[
            t.NonNegativeInt, m.Field(description="Warnings retained under suspension")
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
        suspended_warning_lines: Annotated[
            t.StrSequence, m.Field(description="Visible suspended warning occurrences")
        ] = m.Field(default_factory=tuple)
        skip_cases: Annotated[
            t.StrSequence, m.Field(description="Skipped test labels")
        ] = m.Field(default_factory=tuple)
        slow_entries: Annotated[
            t.StrSequence, m.Field(description="Slow test entries")
        ] = m.Field(default_factory=tuple)

    class DiagResult(m.ArbitraryTypesModel):
        """Internal container for extracted diagnostics.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        failed_cases: Annotated[
            t.MutableSequenceOf[str],
            m.Field(description="Collected failed test-case labels"),
        ] = m.Field(default_factory=list)
        error_cases: Annotated[
            t.MutableSequenceOf[str],
            m.Field(description="Collected error test-case labels"),
        ] = m.Field(default_factory=list)
        error_traces: Annotated[
            t.MutableSequenceOf[str],
            m.Field(description="Collected error trace chunks"),
        ] = m.Field(default_factory=list)
        skip_cases: Annotated[
            t.MutableSequenceOf[str],
            m.Field(description="Collected skipped test-case labels"),
        ] = m.Field(default_factory=list)
        warning_lines: Annotated[
            t.MutableSequenceOf[str], m.Field(description="Collected warning lines")
        ] = m.Field(default_factory=list)
        suspended_warning_lines: Annotated[
            t.MutableSequenceOf[str],
            m.Field(description="Collected suspended warning occurrences"),
        ] = m.Field(default_factory=list)
        slow_entries: Annotated[
            t.MutableSequenceOf[str], m.Field(description="Collected slow-test entries")
        ] = m.Field(default_factory=list)

    class InventoryReport(m.ArbitraryTypesModel):
        """Summary of written inventory report artifacts."""

        total_scripts: Annotated[
            t.NonNegativeInt, m.Field(description="Total discovered scripts")
        ]
        reports_written: Annotated[
            t.MutableSequenceOf[str], m.Field(description="Written report file paths")
        ] = m.Field(default_factory=list)

    class GateContractViolation(m.Value):
        """One gate-script contract violation."""

        # Why: leaf validate contract owned by m.Infra (collision-safe vs census Violation).
        script: Annotated[str, m.Field(description="Script path")]
        check: Annotated[str, m.Field(description="Failed check")]
        message: Annotated[str, m.Field(description="Violation message")]
        severity: Annotated[str, m.Field(description="Severity")] = (
            c.Infra.GateSeverity.ERROR.value
        )

    class GateContractScriptInfo(m.Value):
        """Validation result for one gate script."""

        path: Annotated[str, m.Field(description="Script path")]
        extension: Annotated[str, m.Field(description="File extension")]
        role: Annotated[str, m.Field(description="Script role")]
        violations: Annotated[
            t.VariadicTuple[FlextInfraModelsCore.GateContractViolation],
            m.Field(description="Violations"),
        ] = ()

    class GateContractSummary(m.Value):
        """Aggregate gate-contract counts."""

        errors: Annotated[int, m.Field(description="Error count")] = 0
        gate_scripts: Annotated[int, m.Field(description="Gate script count")] = 0
        ok: Annotated[int, m.Field(description="Passing gate script count")] = 0
        warnings: Annotated[int, m.Field(description="Warning count")] = 0

    class GateContractRunResult(m.Value):
        """CLI outcome for one gate-contract validation run."""

        exit_code: Annotated[int, m.Field(description="Process exit code")]
        violation_count: Annotated[int, m.Field(description="Error count")]

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
