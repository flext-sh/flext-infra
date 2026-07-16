"""Protocol for workspace check outcomes.

Defines the structural contracts for workspace gate loop outcome objects
(issues, gate results, gate executions, per-project aggregates, and the
overall loop outcome) consumed across the check reporting surface.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    # mro-qc84 (fix-forward): reverse edges consumed only by postponed protocol
    # annotations; runtime loading closes the p -> m/t facade cycle.
    from flext_infra import p, t


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

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
