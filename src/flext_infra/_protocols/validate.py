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

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsValidate:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ValidationReport(Protocol):
        """Structural data contract projected from the owning model."""

        passed: bool
        violations: Sequence[str]
        summary: str

    @runtime_checkable
    class FreshImportProbe(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def subject(self) -> str: ...
        @property
        def code(self) -> str: ...

    @runtime_checkable
    class FreshImportEntryPoints(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scripts(self) -> Mapping[str, str] | None: ...
        @property
        def gui_scripts(self) -> Mapping[str, str] | None: ...
        @property
        def entry_points(self) -> Mapping[str, Mapping[str, str]] | None: ...

    @runtime_checkable
    class FreshImportMetadata(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> p.Infra.FreshImportEntryPoints: ...

    @runtime_checkable
    class SkillRuleEvaluationContext(Protocol):
        """Structural data contract projected from the owning model."""

        rules_list: t.JsonList
        skill_dir: Path
        root: Path
        mode: c.Infra.OperationMode
        include_globs: Sequence[str]
        exclude_globs: Sequence[str]

    @runtime_checkable
    class SkillReportContext(Protocol):
        """Structural data contract projected from the owning model."""

        rules: Mapping[str, t.JsonValue]
        root: Path
        skill_name: str
        mode: c.Infra.OperationMode
        counts: t.IntMapping
        violations: Sequence[str]

    @runtime_checkable
    class StubAnalysisReport(Protocol):
        """Structural data contract projected from the owning model."""

        project: t.NonEmptyStr
        mypy_hints: MutableSequence[str]
        internal_missing: MutableSequence[str]
        unresolved_missing: MutableSequence[str]
        total_missing: t.NonNegativeInt

    @runtime_checkable
    class PytestMarkdownOrigin(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_path(self) -> str: ...
        @property
        def start_line(self) -> int: ...
        @property
        def source_sha256(self) -> str: ...
        @property
        def max_retries(self) -> int: ...

    @runtime_checkable
    class PytestMarkdownItem(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_id(self) -> t.NonEmptyStr: ...
        @property
        def origin(self) -> p.Infra.PytestMarkdownOrigin: ...

    @runtime_checkable
    class PytestMarkdownCollection(Protocol):
        """Structural data contract projected from the owning model."""

        eligible: MutableSequence[p.Infra.PytestMarkdownOrigin]
        collected: MutableSequence[p.Infra.PytestMarkdownItem]
        deselected: MutableSequence[str]

    @runtime_checkable
    class PytestMarkdownAttempt(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_id(self) -> t.NonEmptyStr: ...
        @property
        def attempts(self) -> int: ...
        @property
        def first_exception_type(self) -> str | None: ...
        @property
        def first_exception_traceback(self) -> str | None: ...

    @runtime_checkable
    class PytestCollectionManifest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_ids(self) -> t.StrTuple: ...
        @property
        def markdown_eligible(self) -> tuple[p.Infra.PytestMarkdownOrigin, ...]: ...
        @property
        def markdown_collected(self) -> tuple[p.Infra.PytestMarkdownItem, ...]: ...
        @property
        def markdown_deselected(self) -> t.StrTuple: ...

    @runtime_checkable
    class PytestSelectionPlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def manifest_path(self) -> Path: ...
        @property
        def node_ids(self) -> t.StrTuple: ...
        @property
        def whole_target(self) -> bool: ...
        @property
        def inventory_collected(self) -> bool: ...
        @property
        def owns_no_tests(self) -> bool: ...

    @runtime_checkable
    class PytestInvocation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def manifest_path(self) -> Path | None: ...
        @property
        def serialize(self) -> bool: ...
        @property
        def whole_target(self) -> bool: ...
        @property
        def execution_mode(self) -> c.Infra.PytestExecutionMode: ...

    @runtime_checkable
    class PytestRunContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def execution_mode(self) -> c.Infra.PytestExecutionMode: ...
        @property
        def testmon_db(self) -> Path | None: ...
        @property
        def testmon_lease_acquired(self) -> bool | None: ...
        @property
        def deadline_monotonic(self) -> float: ...
        @property
        def report_directory(self) -> Path | None: ...
        @property
        def profile_sha256(self) -> str | None: ...

    @runtime_checkable
    class PytestReportEvent(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def report_type(self) -> str: ...
        @property
        def category(self) -> str | None: ...
        @property
        def filename(self) -> str | None: ...
        @property
        def lineno(self) -> int | None: ...
        @property
        def message(self) -> str | None: ...
        @property
        def nodeid(self) -> str | None: ...
        @property
        def when(self) -> str | None: ...
        @property
        def outcome(self) -> Literal["passed", "failed", "skipped"] | None: ...
        @property
        def user_properties(self) -> tuple[tuple[str, t.JsonValue], ...]: ...

    @runtime_checkable
    class PytestWarningEvent(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def category(self) -> str: ...
        @property
        def category_module(self) -> str: ...
        @property
        def category_qualname(self) -> str: ...
        @property
        def filename(self) -> str: ...
        @property
        def lineno(self) -> int: ...
        @property
        def message(self) -> str: ...

    @runtime_checkable
    class PytestPhaseOutcome(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def node_id(self) -> t.NonEmptyStr: ...
        @property
        def phase(self) -> Literal["setup", "call", "teardown", "???"]: ...
        @property
        def outcome(self) -> Literal["passed", "failed", "skipped"]: ...

    @runtime_checkable
    class PytestDiagnostics(Protocol):
        """Structural data contract projected from the owning model."""

        failed_count: t.NonNegativeInt
        error_count: t.NonNegativeInt
        warning_count: t.NonNegativeInt
        skipped_count: t.NonNegativeInt
        connectivity_skip_cases: t.StrTuple
        collection_failed_count: t.NonNegativeInt
        collection_skipped_count: t.NonNegativeInt
        collection_failed_cases: t.StrTuple
        collection_skip_cases: t.StrTuple
        reported_node_ids: t.StrTuple
        phase_outcomes: tuple[p.Infra.PytestPhaseOutcome, ...]
        markdown_attempts: tuple[p.Infra.PytestMarkdownAttempt, ...]
        markdown_items: tuple[p.Infra.PytestMarkdownItem, ...]
        failed_cases: Sequence[str]
        error_traces: Sequence[str]
        warning_lines: Sequence[str]
        skip_cases: Sequence[str]
        slow_entries: Sequence[str]

    @runtime_checkable
    class PytestMarkdownReconciliation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def eligible(self) -> tuple[p.Infra.PytestMarkdownOrigin, ...]: ...
        @property
        def selected(self) -> tuple[p.Infra.PytestMarkdownItem, ...]: ...
        @property
        def deselected(self) -> tuple[p.Infra.PytestMarkdownItem, ...]: ...
        @property
        def diagnostics(self) -> p.Infra.PytestDiagnostics: ...
        @property
        def cache_hit(self) -> bool: ...
        @property
        def violations(self) -> t.StrTuple: ...

    @runtime_checkable
    class DiagResult(Protocol):
        """Structural data contract projected from the owning model."""

        reported_phases: MutableMapping[str, t.MutableStrMapping]
        connectivity_skip_cases: MutableSequence[str]
        markdown_attempts: MutableSequence[p.Infra.PytestMarkdownAttempt]
        markdown_items: MutableSequence[p.Infra.PytestMarkdownItem]
        collection_failed_cases: MutableSequence[str]
        collection_skip_cases: MutableSequence[str]
        failed_cases: MutableSequence[str]
        error_cases: MutableSequence[str]
        error_traces: MutableSequence[str]
        skip_cases: MutableSequence[str]
        warning_lines: MutableSequence[str]
        slow_entries: MutableSequence[str]

    @runtime_checkable
    class InventoryReport(Protocol):
        """Structural data contract projected from the owning model."""

        total_scripts: t.NonNegativeInt
        reports_written: MutableSequence[str]

    @runtime_checkable
    class NamespaceValidateCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...


__all__: list[str] = [
    "FlextInfraProtocolsValidate",
]
