"""Gate execution methods for workspace checker."""

from __future__ import annotations

import time
from pathlib import Path

from flext_infra import (
    FlextInfraAbstractionBoundaryGate,
    FlextInfraBanditGate,
    FlextInfraGate,
    FlextInfraGoGate,
    FlextInfraLocCapGate,
    FlextInfraMarkdownGate,
    FlextInfraMypyGate,
    FlextInfraPyreflyGate,
    FlextInfraPyrightGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
    FlextInfraSilentFailureGate,
    c,
    m,
    t,
    u,
)
from flext_infra.check._check_gate_engine import (
    FlextInfraWorkspaceCheckGateEngineMixin,
)


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    GATE_CLASSES: t.VariadicTuple[type[FlextInfraGate]] = (
        FlextInfraRuffLintGate,
        FlextInfraRuffFormatGate,
        FlextInfraPyreflyGate,
        FlextInfraMypyGate,
        FlextInfraPyrightGate,
        FlextInfraSilentFailureGate,
        FlextInfraBanditGate,
        FlextInfraMarkdownGate,
        FlextInfraGoGate,
        FlextInfraLocCapGate,
        FlextInfraAbstractionBoundaryGate,
    )

    def __init__(self) -> None:
        """Build the gate-id to gate-class mapping used by check execution."""
        self._gates: dict[str, type[FlextInfraGate]] = {
            g.gate_id: g for g in self.GATE_CLASSES
        }

    def get(self, gate_id: str) -> type[FlextInfraGate] | None:
        """Return the registered gate class for one gate id, when present."""
        return self._gates.get(gate_id)

    def create(self, gate_id: str, workspace_root: Path) -> FlextInfraGate | None:
        """Instantiate one registered gate for ``workspace_root`` when available."""
        gate_cls = self._gates.get(gate_id)
        return gate_cls(workspace_root) if gate_cls else None

    @classmethod
    def default(cls) -> FlextInfraGateRegistry:
        """Return the default registry instance for workspace checks."""
        return cls()


class _LoopOutcome(m.ArbitraryTypesModel):
    """Bundled results from the project-checking loop."""

    results: tuple[m.Infra.ProjectResult, ...] = m.Field(
        description="Individual project execution results."
    )
    failed: int = m.Field(
        description="Number of projects that failed one or more gates."
    )
    skipped: int = m.Field(
        description="Number of projects that were skipped during execution."
    )
    total_elapsed: float = m.Field(
        description="Total time elapsed in seconds for the entire loop."
    )


class FlextInfraWorkspaceCheckGatesMixin(FlextInfraWorkspaceCheckGateEngineMixin):
    """Project-iteration loop + isolation around the per-gate execution engine."""

    _workspace_root: Path
    _registry: FlextInfraGateRegistry
    _default_reports_dir: Path

    def _isolate_context(
        self,
        ctx: m.Infra.GateContext,
        project_name: str,
    ) -> m.Infra.GateContext:
        """Create a fresh GateContext scoped to a single project."""
        return m.Infra.GateContext(
            workspace=ctx.workspace_root,
            reports_dir=ctx.reports_dir / project_name,
            apply_fixes=ctx.apply_fixes,
            check_only=ctx.check_only,
            fail_fast=ctx.fail_fast,
            ruff_args=ctx.ruff_args,
            pyright_args=ctx.pyright_args,
        )

    def _run_single_project(
        self,
        project_name: str,
        index: int,
        total: int,
        resolved_gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult | None:
        """Check one project, returning None when the project should be skipped."""
        project_dir = self._workspace_root / project_name
        pyproject_path = project_dir / c.Infra.PYPROJECT_FILENAME
        if not project_dir.is_dir() or not pyproject_path.exists():
            u.Cli.progress(index, total, project_name, c.Infra.SeverityLevel.SKIP)
            return None
        u.Cli.progress(index, total, project_name, c.Infra.VERB_CHECK)
        project_ctx = self._isolate_context(ctx, project_name)
        _ = u.Cli.ensure_dir(project_ctx.reports_dir)
        start = time.monotonic()
        project_result = self._check_project_with_ctx(
            project_dir,
            resolved_gates,
            project_ctx,
        )
        elapsed = time.monotonic() - start
        u.Cli.status(
            c.Infra.VERB_CHECK,
            project_name,
            result=project_result.passed,
            elapsed=elapsed,
        )
        return project_result

    def _run_project_loop(
        self,
        projects: t.StrSequence,
        resolved_gates: t.StrSequence,
        ctx: m.Infra.GateContext,
        *,
        fail_fast: bool,
    ) -> _LoopOutcome:
        """Execute gate checks across projects, collecting results and timing."""
        results: t.MutableSequenceOf[m.Infra.ProjectResult] = []
        total = len(projects)
        failed = 0
        skipped = 0
        loop_start = time.monotonic()
        for index, project_name in enumerate(projects, 1):
            project_result = self._run_single_project(
                project_name,
                index,
                total,
                resolved_gates,
                ctx,
            )
            if project_result is None:
                skipped += 1
                continue
            results.append(project_result)
            if not project_result.passed:
                failed += 1
                if fail_fast:
                    break
        return _LoopOutcome(
            results=tuple(results),
            failed=failed,
            skipped=skipped,
            total_elapsed=time.monotonic() - loop_start,
        )


__all__: list[str] = ["FlextInfraGateRegistry", "FlextInfraWorkspaceCheckGatesMixin"]
