from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import p

from flext_infra import c, p

"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""


if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    @runtime_checkable
    class SarifLocation(Protocol):
        """Read a native source span without depending on its payload model."""

        @property
        def uri(self) -> str: ...

        @property
        def start_line(self) -> int | None: ...

        @property
        def start_column(self) -> int | None: ...

        @property
        def end_line(self) -> int | None: ...

        @property
        def end_column(self) -> int | None: ...

        @property
        def uri_base_id(self) -> str: ...

    @runtime_checkable
    class Issue(Protocol):
        """Shared diagnostic contract for native parsers and gate aggregation."""

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

        @property
        def locations(
            self,
        ) -> Sequence[p.Infra.SarifLocation]: ...

        @property
        def related_locations(
            self,
        ) -> Sequence[p.Infra.SarifLocation]: ...

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
    class GlobalCheckTargetPlanner(Protocol):
        """Plan native global coverage on demand at the admission boundary."""

        def __call__(
            self,
            gates: Sequence[str],
        ) -> p.Result[tuple[p.Infra.CheckProjectTarget, ...]]: ...

    @runtime_checkable
    class PytestRunContextReceiver(Protocol):
        """Receive the runner's immutable Pydantic receipt through explicit DI."""

        def __call__(self, context: p.Infra.PytestRunContext) -> None: ...

    @runtime_checkable
    class WorkspaceLoopOutcome(Protocol):
        """Public structural view of the workspace gate loop outcome."""

        results: tuple[p.Infra.ProjectResult, ...]
        failed: int
        total_elapsed: float

    @runtime_checkable
    class RunCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def fail_fast(self) -> bool: ...

        @property
        def gate_set(self) -> c.Infra.CheckGateSet: ...

        @property
        def phase(self) -> c.Infra.CheckPhase: ...

        @property
        def scope(self) -> c.Infra.CodegenConformScope: ...

        @property
        def reports_dir(self) -> str: ...

        @property
        def check_only(self) -> bool: ...

        @property
        def ruff_args(self) -> str | None: ...

        @property
        def pyright_args(self) -> str | None: ...

        @property
        def file(self) -> str | None: ...

        @property
        def report_output(self) -> Path | None: ...

    @runtime_checkable
    class MypyResourceLimit(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def memory_limit_mb(self) -> int: ...

        @property
        def timeout_seconds(self) -> int: ...

    @runtime_checkable
    class MypyInvocation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def targets(self) -> tuple[Path, ...]: ...

        @property
        def workspace(self) -> Path | None: ...

        @property
        def config_file(self) -> Path | None: ...

        @property
        def report_json(self) -> bool: ...

        @property
        def verbose(self) -> bool: ...

        @property
        def profile_output(self) -> Path | None: ...

    @runtime_checkable
    class FixPyreflyConfigCommand(Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class LineWrapLiteral(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def start(self) -> int: ...

        @property
        def end(self) -> int: ...

        @property
        def prefix(self) -> str: ...

        @property
        def quote(self) -> str: ...

        @property
        def bracketed(self) -> bool: ...

    @runtime_checkable
    class GateOutputReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def raw_output(self) -> str: ...

        @property
        def path(self) -> Path: ...

    @runtime_checkable
    class GateExecutionParams(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_dir(self) -> Path: ...

        @property
        def verdict(self) -> bool: ...

        @property
        def outcome(self) -> c.Infra.ToolOutcome | None: ...

        @property
        def issues(self) -> tuple[p.Infra.Issue, ...]: ...

        @property
        def raw_output(self) -> str: ...

        @property
        def started(self) -> float: ...

    @runtime_checkable
    class SarifRule(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str: ...

        @property
        def short_description(self) -> str: ...

        @property
        def help_uri(self) -> str: ...

    @runtime_checkable
    class SarifResult(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_id(self) -> str: ...

        @property
        def level(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def locations(self) -> tuple[p.Infra.SarifLocation, ...]: ...

        @property
        def related_locations(self) -> tuple[p.Infra.SarifLocation, ...]: ...

    @runtime_checkable
    class SarifRun(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool_name(self) -> str: ...

        @property
        def information_uri(self) -> str: ...

        @property
        def rules(self) -> tuple[p.Infra.SarifRule, ...]: ...

        @property
        def results(self) -> tuple[p.Infra.SarifResult, ...]: ...

    @runtime_checkable
    class CheckReportSummary(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> c.Infra.CheckPhase: ...

        @property
        def requested_gates(self) -> Sequence[str]: ...

        @property
        def pending_gates(self) -> Sequence[str]: ...

        @property
        def targets(self) -> tuple[p.Infra.CheckProjectTarget, ...]: ...

        @property
        def results(self) -> tuple[p.Infra.ProjectResult, ...]: ...

        @property
        def selected_files(self) -> tuple[Path, ...]: ...

        @property
        def global_targets(self) -> tuple[p.Infra.CheckProjectTarget, ...] | None: ...


__all__: list[str] = ["FlextInfraProtocolsCheck"]
