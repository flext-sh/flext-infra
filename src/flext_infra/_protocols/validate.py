# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/validate
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t
from flext_infra._protocols import FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_infra._constants import FlextInfraConstantsBase, FlextInfraConstantsMake


class FlextInfraProtocolsValidate:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ValidationReport(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def passed(self) -> bool:
            """Validation status."""
            ...

        @property
        def violations(self) -> Sequence[str]:
            """Collected validation violations."""
            ...

        @property
        def summary(self) -> str:
            """Human-readable validation summary."""
            ...

    @runtime_checkable
    class FreshImportProbe(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def subject(self) -> str:
            """Public contract verified by this process."""
            ...

        @property
        def code(self) -> str:
            """Python program rendered from typed contracts."""
            ...

    @runtime_checkable
    class FreshImportEntryPoints(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scripts(self) -> Mapping[str, str] | None:
            """Declared console entrypoints when present."""
            ...

        @property
        def gui_scripts(self) -> Mapping[str, str] | None:
            """Declared graphical entrypoints when present."""
            ...

        @property
        def entry_points(self) -> Mapping[str, Mapping[str, str]] | None:
            """Declared plugin entrypoint groups when present."""
            ...

    @runtime_checkable
    class FreshImportMetadata(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> FlextInfraProtocolsValidate.FreshImportEntryPoints:
            """Executable metadata from the published project table."""
            ...

    @runtime_checkable
    class SkillRuleEvaluationContext(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rules_list(self) -> t.JsonList:
            """Rules to evaluate."""
            ...

        @property
        def skill_dir(self) -> Path:
            """Skill directory path."""
            ...

        @property
        def root(self) -> Path:
            """Repository root path."""
            ...

        @property
        def mode(self) -> FlextInfraConstantsBase.OperationMode:
            """Skill validation mode."""
            ...

        @property
        def include_globs(self) -> Sequence[str]:
            """Include globs."""
            ...

        @property
        def exclude_globs(self) -> Sequence[str]:
            """Exclude globs."""
            ...

    @runtime_checkable
    class SkillReportContext(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rules(self) -> Mapping[str, t.JsonValue]:
            """Rules payload."""
            ...

        @property
        def root(self) -> Path:
            """Repository root path."""
            ...

        @property
        def skill_name(self) -> str:
            """Skill folder name."""
            ...

        @property
        def mode(self) -> FlextInfraConstantsBase.OperationMode:
            """Skill validation mode."""
            ...

        @property
        def counts(self) -> t.IntMapping:
            """Violation counts."""
            ...

        @property
        def violations(self) -> Sequence[str]:
            """Violations."""
            ...

    @runtime_checkable
    class StubAnalysisReport(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def mypy_hints(self) -> MutableSequence[str]:
            """Install-package hints extracted from mypy output."""
            ...

        @property
        def internal_missing(self) -> MutableSequence[str]:
            """Missing internal imports."""
            ...

        @property
        def unresolved_missing(self) -> MutableSequence[str]:
            """Missing external imports without an installed typed dependency."""
            ...

        @property
        def total_missing(self) -> t.NonNegativeInt:
            """Total missing imports."""
            ...

    @runtime_checkable
    class PytestMarkdownOrigin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_path(self) -> str:
            """Repository-relative source identity."""
            ...

        @property
        def start_line(self) -> int:
            """Plugin first-code-line offset."""
            ...

        @property
        def source_sha256(self) -> str:
            """Digest of the exact plugin-defined executable source."""
            ...

        @property
        def max_retries(self) -> int:
            """Plugin-declared retry policy."""
            ...

    @runtime_checkable
    class PytestMarkdownItem(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_id(self) -> t.NonEmptyStr:
            """Actual collected pytest node ID."""
            ...

        @property
        def origin(self) -> FlextInfraProtocolsValidate.PytestMarkdownOrigin:
            """Definition supplied by the installed Markdown collector."""
            ...

    @runtime_checkable
    class PytestMarkdownCollection(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def eligible(
            self,
        ) -> Sequence[FlextInfraProtocolsValidate.PytestMarkdownOrigin]:
            """Independently parsed origins."""
            ...

        @property
        def collected(self) -> Sequence[FlextInfraProtocolsValidate.PytestMarkdownItem]:
            """Observed pre-selection items."""
            ...

        deselected: MutableSequence[str]

    @runtime_checkable
    class PytestMarkdownAttempt(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_id(self) -> t.NonEmptyStr:
            """Actual executed Markdown node."""
            ...

        @property
        def attempts(self) -> int:
            """Observed native runner entries."""
            ...

        @property
        def first_exception_type(self) -> str | None:
            """First exception escaping the SDK runner."""
            ...

        @property
        def first_exception_traceback(self) -> str | None:
            """Original first exception traceback."""
            ...

    @runtime_checkable
    class PytestCollectionManifest(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_ids(self) -> t.StrTuple:
            """Unique node IDs in execution order."""
            ...

        @property
        def markdown_eligible(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownOrigin, ...]:
            """Independent plugin eligibility."""
            ...

        @property
        def markdown_collected(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownItem, ...]:
            """Collection before deselection."""
            ...

        @property
        def markdown_deselected(self) -> t.StrTuple:
            """Explicit Markdown deselection node IDs."""
            ...

    @runtime_checkable
    class PytestSelectionPlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def manifest_path(self) -> Path:
            """Canonical node-ID manifest."""
            ...

        @property
        def node_ids(self) -> t.StrTuple:
            """Selected node IDs in execution order."""
            ...

        @property
        def whole_target(self) -> bool:
            """Whether the selection covers the complete test target."""
            ...

        @property
        def inventory_collected(self) -> bool:
            """Whether this run executed the complete inventory phase."""
            ...

        @property
        def owns_no_tests(self) -> bool:
            """Structural member projected from the owning model.

            The project declares no test files under the config-owned collection
            roots: an empty suite by design, not a broken run.
            """
            ...

    @runtime_checkable
    class PytestInvocation(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def manifest_path(self) -> Path | None:
            """Collection manifest enforcing a nonempty selection."""
            ...

        @property
        def serialize(self) -> bool:
            """Run serially without xdist workers."""
            ...

        @property
        def whole_target(self) -> bool:
            """Selection covers the complete test target."""
            ...

        @property
        def execution_mode(self) -> FlextInfraConstantsMake.PytestExecutionMode:
            """Canonical execution mode for this invocation."""
            ...

    @runtime_checkable
    class PytestRunContext(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def execution_mode(self) -> FlextInfraConstantsMake.PytestExecutionMode:
            """Canonical test operation for this report directory."""
            ...

        @property
        def testmon_db(self) -> Path | None:
            """Structural member projected from the owning model.

            External pytest-testmon database for incremental operations; absent for
            full and coverage execution.
            """
            ...

        @property
        def testmon_lease_acquired(self) -> bool | None:
            """Structural member projected from the owning model.

            Whether an incremental phase acquired its Testmon lease; absent for full
            and coverage execution.
            """
            ...

        @property
        def deadline_monotonic(self) -> float:
            """Shared absolute deadline across all execution phases."""
            ...

        @property
        def report_directory(self) -> Path | None:
            """Explicit directory binding profiled parent and children."""
            ...

        @property
        def profile_sha256(self) -> str | None:
            """Digest binding a profile sidecar to its exact pstats artifact."""
            ...

    @runtime_checkable
    class PytestReportEvent(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def report_type(self) -> str:
            """Pytest event kind."""
            ...

        @property
        def category(self) -> str | None:
            """Warning category name."""
            ...

        @property
        def filename(self) -> str | None:
            """Warning source filename."""
            ...

        @property
        def lineno(self) -> int | None:
            """Warning source line."""
            ...

        @property
        def message(self) -> str | None:
            """Complete warning message."""
            ...

        @property
        def nodeid(self) -> str | None:
            """TestReport node ID."""
            ...

        @property
        def when(self) -> str | None:
            """Pytest lifecycle phase."""
            ...

        @property
        def outcome(self) -> Literal["passed", "failed", "skipped"] | None:
            """TestReport outcome."""
            ...

        @property
        def user_properties(self) -> tuple[tuple[str, t.JsonValue], ...]:
            """Public pytest item properties transported by report-log."""
            ...

    @runtime_checkable
    class PytestWarningEvent(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def category(self) -> str:
            """Runtime warning class name."""
            ...

        @property
        def category_module(self) -> str:
            """Declaring warning module."""
            ...

        @property
        def category_qualname(self) -> str:
            """Qualified runtime class name."""
            ...

        @property
        def filename(self) -> str:
            """Warning source filename."""
            ...

        @property
        def lineno(self) -> int:
            """Warning source line."""
            ...

        @property
        def message(self) -> str:
            """Complete warning message."""
            ...

    @runtime_checkable
    class PytestPhaseOutcome(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_id(self) -> t.NonEmptyStr:
            """Actual TestReport node ID."""
            ...

        @property
        def phase(self) -> Literal["setup", "call", "teardown", "???"]:
            """Observed public pytest runtest phase."""
            ...

        @property
        def outcome(self) -> Literal["passed", "failed", "skipped"]:
            """Unmodified TestReport outcome."""
            ...

    @runtime_checkable
    class PytestDiagnostics(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def failed_count(self) -> t.NonNegativeInt:
            """Failed test case count."""
            ...

        @property
        def error_count(self) -> t.NonNegativeInt:
            """Errored test case count."""
            ...

        @property
        def warning_count(self) -> t.NonNegativeInt:
            """Recorded warning event count."""
            ...

        @property
        def skipped_count(self) -> t.NonNegativeInt:
            """Skipped test case count."""
            ...

        connectivity_skip_cases: t.StrTuple
        collection_failed_count: t.NonNegativeInt
        collection_skipped_count: t.NonNegativeInt
        collection_failed_cases: t.StrTuple
        collection_skip_cases: t.StrTuple
        reported_node_ids: t.StrTuple

        @property
        def phase_outcomes(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestPhaseOutcome, ...]:
            """Complete observed runtest outcomes, including failures."""
            ...

        @property
        def markdown_attempts(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownAttempt, ...]:
            """Observed SDK execution attempts."""
            ...

        @property
        def markdown_items(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownItem, ...]:
            """Executed call-phase origins."""
            ...

        @property
        def failed_cases(self) -> Sequence[str]:
            """Failed test labels."""
            ...

        @property
        def error_traces(self) -> Sequence[str]:
            """Collected error traces."""
            ...

        @property
        def warning_lines(self) -> Sequence[str]:
            """Captured warning lines."""
            ...

        @property
        def skip_cases(self) -> Sequence[str]:
            """Skipped test labels."""
            ...

        @property
        def slow_entries(self) -> Sequence[str]:
            """Slow test entries."""
            ...

    @runtime_checkable
    class PytestMarkdownReconciliation(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def eligible(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownOrigin, ...]:
            """Independent parser eligibility."""
            ...

        @property
        def selected(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownItem, ...]:
            """Actual selected identities."""
            ...

        @property
        def deselected(
            self,
        ) -> tuple[FlextInfraProtocolsValidate.PytestMarkdownItem, ...]:
            """Origins not executed in this phase."""
            ...

        @property
        def diagnostics(self) -> FlextInfraProtocolsValidate.PytestDiagnostics:
            """Unmodified observed phases, attempts and first causes."""
            ...

        @property
        def cache_hit(self) -> bool:
            """Separate typed incremental cache receipt."""
            ...

        @property
        def violations(self) -> t.StrTuple:
            """Reconciliation failures."""
            ...

    @runtime_checkable
    class DiagResult(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        reported_phases: MutableMapping[str, t.MutableStrMapping]
        connectivity_skip_cases: MutableSequence[str]

        @property
        def markdown_attempts(
            self,
        ) -> Sequence[FlextInfraProtocolsValidate.PytestMarkdownAttempt]:
            """Call-phase attempt observations."""
            ...

        @property
        def markdown_items(
            self,
        ) -> Sequence[FlextInfraProtocolsValidate.PytestMarkdownItem]:
            """Call-phase origin observations."""
            ...

        collection_failed_cases: MutableSequence[str]
        collection_skip_cases: MutableSequence[str]

        @property
        def failed_cases(self) -> MutableSequence[str]:
            """Collected failed test-case labels."""
            ...

        @property
        def error_cases(self) -> MutableSequence[str]:
            """Collected error test-case labels."""
            ...

        @property
        def error_traces(self) -> MutableSequence[str]:
            """Collected error trace chunks."""
            ...

        @property
        def skip_cases(self) -> MutableSequence[str]:
            """Collected skipped test-case labels."""
            ...

        @property
        def warning_lines(self) -> MutableSequence[str]:
            """Collected warning lines."""
            ...

        @property
        def slow_entries(self) -> MutableSequence[str]:
            """Collected slow-test entries."""
            ...

    @runtime_checkable
    class InventoryReport(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def total_scripts(self) -> t.NonNegativeInt:
            """Total discovered scripts."""
            ...

        @property
        def reports_written(self) -> MutableSequence[str]:
            """Written report file paths."""
            ...

    @runtime_checkable
    class NamespaceValidateCommand(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository root whose namespace contract is validated."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsValidate",
]
