"""Base gate class and protocol for quality gate library.

Defines the structural contract (Protocol) and shared implementation
base (ABC) for quality gates. Each gate encapsulates a single tool
(ruff, mypy, pyrefly, etc.) with check and optional fix operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Protocol, runtime_checkable

from flext_core import FlextModels
from pydantic import ConfigDict, Field

from flext_infra import c, m, u


class FlextInfraGateContext(FlextModels.FrozenStrictModel):
    """Typed execution context passed to each gate invocation.

    Centralizes run-specific parameters instead of ``**kwargs``.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    workspace_root: Annotated[Path, Field(description="Workspace root directory")]
    reports_dir: Annotated[Path, Field(description="Reports output directory")]
    fail_fast: Annotated[
        bool,
        Field(default=False, description="Stop on first gate failure"),
    ] = False


@runtime_checkable
class FlextInfraGateProtocol(Protocol):
    """Structural contract for quality gates."""

    @property
    def gate_id(self) -> str:
        """Unique gate identifier (e.g. 'lint', 'mypy')."""
        ...

    @property
    def can_fix(self) -> bool:
        """Whether this gate supports auto-fix."""
        ...

    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.Check.GateExecution:
        """Run the gate check and return execution result."""
        ...


class FlextInfraGate(ABC):
    """Base class for quality gates with shared infrastructure.

    Each concrete gate implements ``check()`` for a specific tool.
    Gates with auto-fix capability override ``fix()`` as well.
    """

    gate_id: str = ""
    gate_name: str = ""
    can_fix: bool = False
    tool_name: str = ""
    tool_url: str = ""

    def __init__(self, workspace_root: Path) -> None:
        """Initialize gate with workspace root."""
        self._workspace_root = workspace_root

    @abstractmethod
    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.Check.GateExecution:
        """Run the quality check and return execution result."""

    def fix(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.Check.GateExecution:
        """Auto-fix issues (override in gates with ``can_fix=True``)."""
        _ = ctx
        return self._build_gate_result(
            project=project_dir.name,
            passed=True,
            issues=[],
            duration=0.0,
            raw_output=f"Gate {self.gate_id} does not support fix",
        )

    # -- Shared infrastructure ------------------------------------------------

    def _run(
        self,
        cmd: list[str],
        cwd: Path,
        timeout: int = c.Infra.Timeouts.DEFAULT,
        env: Mapping[str, str] | None = None,
    ) -> m.Infra.Core.CommandOutput:
        """Execute a subprocess command and return output."""
        result = u.Infra.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
        if result.is_failure:
            return m.Infra.Core.CommandOutput(
                stdout="",
                stderr=result.error or "command execution failed",
                exit_code=1,
            )
        cmd_output: m.Infra.Core.CommandOutput = result.value
        return m.Infra.Core.CommandOutput(
            stdout=cmd_output.stdout,
            stderr=cmd_output.stderr,
            exit_code=cmd_output.exit_code,
            duration=cmd_output.duration,
        )

    def _build_gate_result(
        self,
        *,
        project: str,
        passed: bool,
        issues: list[m.Infra.Check.Issue],
        duration: float,
        raw_output: str = "",
    ) -> m.Infra.Check.GateExecution:
        """Build a standardized gate execution result."""
        model = m.Infra.Check.GateResult(
            gate=self.gate_id,
            project=project,
            passed=passed,
            errors=[issue.formatted for issue in issues],
            duration=round(duration, 3),
        )
        return m.Infra.Check.GateExecution(
            result=model,
            issues=issues,
            raw_output=raw_output,
        )

    def _result_exit_code(self, result: m.Infra.Core.CommandOutput) -> int:
        """Extract exit code from command output."""
        return result.exit_code if hasattr(result, "exit_code") else 1

    def _existing_check_dirs(self, project_dir: Path) -> list[str]:
        """Return check directories that exist in the project."""
        dirs = (
            c.Infra.Check.DEFAULT_CHECK_DIRS
            if project_dir.resolve() == self._workspace_root.resolve()
            else c.Infra.Check.CHECK_DIRS_SUBPROJECT
        )
        return [d for d in dirs if (project_dir / d).is_dir()]

    @staticmethod
    def _dirs_with_py(project_dir: Path, dirs: list[str]) -> list[str]:
        """Filter directories to those containing Python files."""
        out: list[str] = []
        for directory in dirs:
            path = project_dir / directory
            if not path.is_dir():
                continue
            if next(path.rglob(c.Infra.Extensions.PYTHON_GLOB), None) or next(
                path.rglob("*.pyi"),
                None,
            ):
                out.append(directory)
        return out


__all__ = [
    "FlextInfraGate",
    "FlextInfraGateContext",
    "FlextInfraGateProtocol",
]
