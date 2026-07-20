"""Protocol for workspace check outcomes.

Defines the structural contracts for workspace gate loop outcome objects
(issues, gate results, gate executions, per-project aggregates, and the
overall loop outcome) consumed across the check reporting surface.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import p as cli_p

if TYPE_CHECKING:
    # mro-qc84 (fix-forward): reverse edges consumed only by postponed protocol
    # annotations; runtime loading closes the p -> m/t facade cycle.
    from flext_infra import p, t


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    # mro-dxrp.3.9 (Sisyphus-Junior): mirror the common config rule contract so
    # Rope consumers accept every discriminated StaticRuleSpec model variant.
    @runtime_checkable
    class StaticRuleSpec(cli_p.BaseModel, Protocol):
        """Shared metadata exposed by every configured static-analysis rule."""

        @property
        def kind(self) -> str: ...

        @property
        def detail(self) -> str: ...

    @runtime_checkable
    class RunCommand(Protocol):
        """Canonical CLI payload for ``flext-infra check run``."""

        @property
        def workspace(self) -> str: ...

        @property
        def projects(self) -> t.StrSequence | None: ...

        @property
        def module(self) -> str | None: ...

        @property
        def namespace(self) -> str | None: ...

        @property
        def fail_fast(self) -> bool: ...

        @property
        def verbose(self) -> bool: ...

        @property
        def apply(self) -> bool: ...

        @property
        def gates(self) -> t.StrSequence: ...

        @property
        def reports_dir(self) -> str: ...

        @property
        def files(self) -> t.StrSequence | None: ...

        @property
        def fix(self) -> bool: ...

        @property
        def check_only(self) -> bool: ...

        @property
        def ruff_args(self) -> str | None: ...

        @property
        def pyright_args(self) -> str | None: ...

    @runtime_checkable
    class MypyResourceLimit(Protocol):
        """Validated memory and wall-time limits for every Mypy process."""

        @property
        def memory_limit_mb(self) -> int: ...

        @property
        def timeout_seconds(self) -> int: ...

    @runtime_checkable
    class FixPyreflyConfigCommand(Protocol):
        """Canonical payload for fixing Pyrefly settings."""

        @property
        def workspace(self) -> str: ...

        @property
        def projects(self) -> t.StrSequence | None: ...

        @property
        def module(self) -> str | None: ...

        @property
        def namespace(self) -> str | None: ...

        @property
        def fail_fast(self) -> bool: ...

        @property
        def verbose(self) -> bool: ...

        @property
        def apply(self) -> bool: ...

        @property
        def gates(self) -> t.StrSequence: ...

    @runtime_checkable
    class FixEnforcementCommand(Protocol):
        """Canonical payload for fixing enforcement violations."""

        @property
        def workspace(self) -> str: ...

        @property
        def projects(self) -> t.StrSequence | None: ...

        @property
        def module(self) -> str | None: ...

        @property
        def namespace(self) -> str | None: ...

        @property
        def fail_fast(self) -> bool: ...

        @property
        def verbose(self) -> bool: ...

        @property
        def apply(self) -> bool: ...

        @property
        def gates(self) -> t.StrSequence: ...

        @property
        def rules(self) -> t.StrSequence: ...

        @property
        def safe_only(self) -> bool: ...

        @property
        def check_after(self) -> bool: ...

    @runtime_checkable
    class SarifRule(Protocol):
        """Compact SARIF rule descriptor."""

        @property
        def id(self) -> str: ...

        @property
        def short_description(self) -> str: ...

    @runtime_checkable
    class SarifResult(Protocol):
        """SARIF result entry."""

        @property
        def rule_id(self) -> str: ...

        @property
        def level(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def locations(self) -> t.SequenceOf[p.BaseModel]: ...

    @runtime_checkable
    class SarifReport(Protocol):
        """Complete SARIF 2.1.0 report."""

        @property
        def schema_uri(self) -> str: ...

        @property
        def version(self) -> str: ...

        @property
        def runs(self) -> t.SequenceOf[p.BaseModel]: ...

    # mro-qc84 (fix-forward): protocol-of-model for a single tool-reported issue
    # (m.Infra.Issue). Consumed through gate execution issue tuples.
    @runtime_checkable
    class Issue(Protocol):
        """Single issue reported by a quality gate tool."""

        @property
        def file(self) -> str: ...

        @property
        def line(self) -> int: ...

        @property
        def column(self) -> int: ...

        @property
        def code(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def formatted(self) -> str: ...

    # mro-qc84 (fix-forward): protocol-of-model for a single gate result summary
    # (m.Infra.GateResult).
    @runtime_checkable
    class GateResult(Protocol):
        """Result summary for a single quality gate execution."""

        @property
        def project(self) -> str: ...

        @property
        def gate(self) -> str: ...

        @property
        def passed(self) -> bool: ...

        @property
        def errors(self) -> t.StrSequence: ...

        @property
        def duration(self) -> float: ...

    # mro-qc84 (fix-forward): protocol-of-model for the execution of one gate
    # (m.Infra.GateExecution). Consumed at runtime by check reporting.
    @runtime_checkable
    class GateExecution(Protocol):
        """Execution result for a single quality gate."""

        @property
        def result(self) -> p.Infra.GateResult: ...

        @property
        def issues(self) -> t.SequenceOf[p.Infra.Issue]: ...

        @property
        def raw_output(self) -> str: ...

        @property
        def error_count(self) -> int: ...

    # mro-qc84 (fix-forward): protocol-of-model for aggregated per-project gate
    # results (m.Infra.ProjectResult). Consumed at runtime by the workspace
    # check loop outcome pydantic field and by report generators.
    @runtime_checkable
    class ProjectResult(Protocol):
        """Aggregated gate results for a single project."""

        @property
        def project(self) -> str: ...

        @property
        def gates(self) -> t.MappingKV[str, p.Infra.GateExecution]: ...

        @property
        def passed(self) -> bool: ...

        @property
        def total_errors(self) -> int: ...

    @runtime_checkable
    class WorkspaceLoopOutcome(Protocol):
        """Public structural view of the workspace gate loop outcome."""

        results: tuple[p.Infra.ProjectResult, ...]
        failed: int
        skipped: int
        total_elapsed: float


__all__: list[str] = ["FlextInfraProtocolsCheck"]
