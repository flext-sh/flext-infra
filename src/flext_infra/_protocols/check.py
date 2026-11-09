"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import c
from flext_infra._protocols.mixins import FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from collections.abc import Mapping

    from flext_cli import p

    from flext_infra import t
    from flext_infra._protocols import FlextInfraProtocolsValidate
    from flext_infra._protocols._git import FlextInfraProtocolsGitIdentity


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    @runtime_checkable
    class SarifLocation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def uri(self) -> str:
            """Artifact URI."""
            ...

        @property
        def start_line(self) -> int | None:
            """Start line (1-based)."""
            ...

        @property
        def start_column(self) -> int | None:
            """Native start column."""
            ...

        @property
        def end_line(self) -> int | None:
            """Native end line when supplied by the scanner."""
            ...

        @property
        def end_column(self) -> int | None:
            """Native end column when supplied by the scanner."""
            ...

        @property
        def uri_base_id(self) -> str:
            """URI base identifier."""
            ...

    @runtime_checkable
    class Issue(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> str:
            """Source file path."""
            ...

        @property
        def line(self) -> int:
            """Line number."""
            ...

        @property
        def column(self) -> int:
            """Column number."""
            ...

        @property
        def code(self) -> str:
            """Rule or error code."""
            ...

        @property
        def message(self) -> str:
            """Human-readable issue description."""
            ...

        @property
        def severity(self) -> str:
            """Issue severity level."""
            ...

        @property
        def locations(self) -> tuple[FlextInfraProtocolsCheck.SarifLocation, ...]:
            """Native primary source spans when supplied by the scanner."""
            ...

        @property
        def related_locations(
            self,
        ) -> tuple[FlextInfraProtocolsCheck.SarifLocation, ...]:
            """All native comparison locations, including other projects."""
            ...

        @property
        def formatted(self) -> str:
            """Format issue as ``file:line:col [code] message``."""
            ...

    @runtime_checkable
    class GitScopeFacts(Protocol):
        """Share one invocation's tracked Git scope inventory across consumers."""

        def tracked_scope_relative_paths(
            self,
            scope_root: Path,
        ) -> Sequence[str] | None: ...

    @runtime_checkable
    class NativeStorageSlot[ValueT](Protocol):
        """Read one interpreter-owned slot with its precise native result."""

        def __get__(
            self,
            instance: t.Infra.NativeOperand,
            owner: t.Infra.NativeType,
            /,
        ) -> ValueT: ...

    @runtime_checkable
    class NativeModuleSpec(Protocol):
        """Physical source fields supplied by the native import finder."""

        @property
        def origin(self) -> str | None: ...

        @property
        def loader(self) -> p.AttributeProbe | None: ...

        @property
        def submodule_search_locations(self) -> Sequence[str] | None: ...

    @runtime_checkable
    class PytestRunContextReceiver(Protocol):
        """Receive the runner's immutable Pydantic receipt through explicit DI."""

        def __call__(
            self, context: (FlextInfraProtocolsValidate.PytestRunContext)
        ) -> None: ...

    @runtime_checkable
    class WorkspaceLoopOutcome(Protocol):
        """Public structural view of the workspace gate loop outcome."""

        results: tuple[FlextInfraProtocolsCheck.ProjectResult, ...]
        failed: int
        total_elapsed: float

    @runtime_checkable
    class RunCommand(FlextInfraProtocolsMixins.WriteMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def fail_fast(self) -> bool:
            """Stop check gates after the first failure."""
            ...

        @property
        def gate_set(self) -> c.Infra.CheckGateSet:
            """Structural member projected from the owning model.

            Gate inventory resolved at runtime when --gates is empty: check (CI or
            local partition), fix, or fmt.
            """
            ...

        @property
        def phase(self) -> c.Infra.CheckPhase:
            """Primary source admission or complete checker phase."""
            ...

        @property
        def scope(self) -> c.Infra.CodegenConformScope:
            """Structural member projected from the owning model.

            Omitted-project selection: self checks the invoked repository; all adds
            every governed workspace member, and multi-root tools run once over
            their union.
            """
            ...

        @property
        def reports_dir(self) -> str:
            """Base directory for unique invocation check reports."""
            ...

        @property
        def check_only(self) -> bool:
            """Enable check-only mode for supported tools."""
            ...

        @property
        def ruff_args(self) -> str | None:
            """Extra arguments forwarded to Ruff."""
            ...

        @property
        def pyright_args(self) -> str | None:
            """Extra arguments forwarded to Pyright."""
            ...

        @property
        def file(self) -> str | None:
            """One literal repository-relative file; read-only gates."""
            ...

        @property
        def report_output(self) -> Path | None:
            """Absent invocation-owned typed summary destination."""
            ...

        @property
        def reports_dir_path(self) -> Path:
            """Resolve the requested base; the checker owns its unique run leaf."""
            ...

    @runtime_checkable
    class MypyResourceLimit(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def memory_limit_mb(self) -> int:
            """Positive Mypy memory limit in MiB (Linux AS; Darwin RSS)."""
            ...

        @property
        def timeout_seconds(self) -> int:
            """Structural member projected from the owning model.

            Positive Mypy wall-time limit in seconds, resolved from
            tools.mypy.timeout_seconds in tooling.yaml or the env override.
            """
            ...

        @property
        def memory_limit_bytes(self) -> int:
            """Validated memory limit converted to bytes for the platform owner."""
            ...

    @runtime_checkable
    class MypyInvocation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def targets(self) -> tuple[Path, ...]:
            """Files or directories to check."""
            ...

        @property
        def workspace(self) -> Path | None:
            """Workspace owning the checker environment."""
            ...

        @property
        def config_file(self) -> Path | None:
            """Owned Mypy configuration."""
            ...

        @property
        def report_json(self) -> bool:
            """Emit native JSON diagnostics."""
            ...

        @property
        def verbose(self) -> bool:
            """Emit Mypy progress."""
            ...

        @property
        def profile_output(self) -> Path | None:
            """Optional cProfile output destination."""
            ...

    @runtime_checkable
    class FixPyreflyConfigCommand(FlextInfraProtocolsMixins.WriteMixin, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class LineWrapLiteral(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def start(self) -> int:
            """Start column of the literal."""
            ...

        @property
        def end(self) -> int:
            """End column of the literal."""
            ...

        @property
        def prefix(self) -> str:
            """String prefix such as f or r."""
            ...

        @property
        def quote(self) -> str:
            """Single-character quote."""
            ...

        @property
        def bracketed(self) -> bool:
            """Whether the literal already sits inside brackets."""
            ...

    @runtime_checkable
    class GateOutputReceipt(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def raw_output(self) -> str:
            """Unmodified native output."""
            ...

        @property
        def path(self) -> Path:
            """Durably published native output receipt."""
            ...

    @runtime_checkable
    class GateExecutionParams(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_dir(self) -> Path:
            """Project whose gate was executed."""
            ...

        @property
        def verdict(self) -> bool:
            """Acceptance decided by the caller."""
            ...

        @property
        def outcome(self) -> c.Infra.ToolOutcome | None:
            """Declared native tool outcome; absent derives it from findings."""
            ...

        @property
        def issues(self) -> tuple[FlextInfraProtocolsCheck.Issue, ...]:
            """Complete native diagnostics."""
            ...

        @property
        def raw_output(self) -> str:
            """Unmodified native output."""
            ...

        @property
        def started(self) -> float:
            """Monotonic execution start time."""
            ...

    @runtime_checkable
    class SarifRule(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str:
            """Rule identifier."""
            ...

        @property
        def short_description(self) -> str:
            """Rule short description."""
            ...

        @property
        def help_uri(self) -> str:
            """Documentation URL of the tool behind the gate."""
            ...

    @runtime_checkable
    class SarifResult(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_id(self) -> str:
            """Rule identifier."""
            ...

        @property
        def level(self) -> str:
            """Result level (error/warning/note)."""
            ...

        @property
        def message(self) -> str:
            """Result message."""
            ...

        @property
        def locations(self) -> tuple[FlextInfraProtocolsCheck.SarifLocation, ...]:
            """Result locations."""
            ...

        @property
        def related_locations(
            self,
        ) -> tuple[FlextInfraProtocolsCheck.SarifLocation, ...]:
            """Native related source spans."""
            ...

    @runtime_checkable
    class SarifRun(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool_name(self) -> str:
            """Tool name."""
            ...

        @property
        def information_uri(self) -> str:
            """Tool documentation URL."""
            ...

        @property
        def rules(self) -> tuple[FlextInfraProtocolsCheck.SarifRule, ...]:
            """Rule descriptors."""
            ...

        @property
        def results(self) -> tuple[FlextInfraProtocolsCheck.SarifResult, ...]:
            """Run results."""
            ...

    @runtime_checkable
    class CheckReportSummary(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> c.Infra.CheckPhase:
            """Original checker phase; primary is never complete check proof."""
            ...

        @property
        def requested_gates(self) -> Sequence[str]:
            """Resolved gate inventory requested before execution."""
            ...

        @property
        def pending_gates(self) -> Sequence[str]:
            """Requested gates whose project applicability is still pending."""
            ...

        @property
        def targets(self) -> tuple[FlextInfraProtocolsCheck.CheckProjectTarget, ...]:
            """Canonical project roots selected for this invocation."""
            ...

        @property
        def results(self) -> tuple[FlextInfraProtocolsCheck.ProjectResult, ...]:
            """Only executions reached by this invocation."""
            ...

        @property
        def selected_files(self) -> tuple[Path, ...]:
            """File selection; empty means full-project execution."""
            ...

        @property
        def global_targets(
            self,
        ) -> tuple[FlextInfraProtocolsCheck.CheckProjectTarget, ...] | None:
            """Structural member projected from the owning model.

            Producer's unfiltered canonical global project and gate plan; absent for
            legacy, filtered or applicability-pending reports.
            """
            ...

        @property
        def complete(self) -> bool:
            """Every selected target executed its exact applicable inventory."""
            ...

    @runtime_checkable
    class BanditFinding(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def filename(self) -> t.NonEmptyStr:
            """Audited source path."""
            ...

        @property
        def line_number(self) -> t.NonNegativeInt:
            """Native finding line."""
            ...

        @property
        def test_id(self) -> t.NonEmptyStr:
            """Bandit test identifier."""
            ...

        @property
        def issue_text(self) -> t.NonEmptyStr:
            """Native security diagnostic."""
            ...

    @runtime_checkable
    class BanditScanError(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def filename(self) -> t.NonEmptyStr:
            """Unaudited source path."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Native scan failure."""
            ...

    @runtime_checkable
    class BanditReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def results(self) -> Sequence[FlextInfraProtocolsCheck.BanditFinding]:
            """Native security findings."""
            ...

        @property
        def errors(self) -> Sequence[FlextInfraProtocolsCheck.BanditScanError]:
            """Source files that were not audited."""
            ...

    @runtime_checkable
    class CheckProjectTarget(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Display/project name."""
            ...

        @property
        def path(self) -> Path:
            """Resolved project root path."""
            ...

        @property
        def applicable_gates(self) -> Sequence[str]:
            """Requested gates elected for this project's inputs."""
            ...

        @property
        def source_identity(
            self,
        ) -> FlextInfraProtocolsGitIdentity.GitIdentityReport | None:
            """Original exact repository identity before gates."""
            ...

    @runtime_checkable
    class GateResult(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        gate: str
        passed: bool
        errors: Sequence[str]
        duration: float

    @runtime_checkable
    class GateExecution(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def result(self) -> FlextInfraProtocolsCheck.GateResult:
            """Gate result model."""
            ...

        @property
        def issues(self) -> tuple[FlextInfraProtocolsCheck.Issue, ...]:
            """Complete native gate diagnostics, including informative findings."""
            ...

        raw_output: str
        raw_receipt: Path | None
        outcome: c.Infra.ToolOutcome

        @property
        def process(self) -> p.Cli.ProcessOutcome | None:
            """Original native process, when this gate invoked one."""
            ...

        @property
        def components(self) -> Mapping[str, FlextInfraProtocolsCheck.GateExecution]:
            """Executions owned by a composite gate."""
            ...

        requested_components: Sequence[str]

        @property
        def complete(self) -> bool:
            """Every elected component has its actual execution record."""
            ...

        @property
        def interrupted(self) -> bool:
            """Whether this execution or an owned component was interrupted."""
            ...

        @property
        def finding_count(self) -> int:
            """Structural member projected from the owning model.

            Number of native findings, independent of approval blocking policy.
            """
            ...

    @runtime_checkable
    class ProjectResult(FlextInfraProtocolsMixins.ProjectNameMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def gates(self) -> Mapping[str, FlextInfraProtocolsCheck.GateExecution]:
            """Gate name to execution mapping."""
            ...

        @property
        def passed(self) -> bool:
            """Whether every gate passed."""
            ...

        @property
        def total_findings(self) -> int:
            """Total native findings across every executed gate."""
            ...

    @runtime_checkable
    class LoopOutcome(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def results(self) -> tuple[FlextInfraProtocolsCheck.ProjectResult, ...]:
            """Individual project execution results."""
            ...

        failed: int
        total_elapsed: float

    @runtime_checkable
    class SarifReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        schema_uri: c.Infra.SarifSchema
        version: c.Infra.SarifVersion

        @property
        def runs(self) -> tuple[FlextInfraProtocolsCheck.SarifRun, ...]:
            """SARIF runs."""
            ...

        @property
        def properties(self) -> FlextInfraProtocolsCheck.CheckReportSummary | None:
            """Typed invocation targets and executions; absent is unknown."""
            ...


__all__: list[str] = ["FlextInfraProtocolsCheck"]
