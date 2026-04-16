"""Gate execution methods for workspace checker."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence
from pathlib import Path
from typing import ClassVar

from flext_core import FlextProtocols
from flext_infra import (
    FlextInfraBanditGate,
    FlextInfraGate,
    FlextInfraGoGate,
    FlextInfraMarkdownGate,
    FlextInfraMypyGate,
    FlextInfraPyreflyGate,
    FlextInfraPyrightGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
    FlextInfraSilentFailureGate,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    GATE_CLASSES: t.Infra.VariadicTuple[type[FlextInfraGate]] = (
        FlextInfraRuffLintGate,
        FlextInfraRuffFormatGate,
        FlextInfraPyreflyGate,
        FlextInfraMypyGate,
        FlextInfraPyrightGate,
        FlextInfraSilentFailureGate,
        FlextInfraBanditGate,
        FlextInfraMarkdownGate,
        FlextInfraGoGate,
    )

    def __init__(self) -> None:
        """Build the gate-id to gate-class mapping used by check execution."""
        self._gates: Mapping[str, type[FlextInfraGate]] = {
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


class FlextInfraWorkspaceCheckGatesMixin:
    """Gate execution, project loop, and individual gate runner methods."""

    _workspace_root: Path
    _registry: FlextInfraGateRegistry
    _default_reports_dir: Path
    _gate_logger: ClassVar[FlextProtocols.Logger] = u.fetch_logger(__name__)

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
            u.Infra.progress(index, total, project_name, c.Infra.SEVERITY_SKIP)
            return None
        u.Infra.progress(index, total, project_name, c.Infra.VERB_CHECK)
        project_ctx = self._isolate_context(ctx, project_name)
        _ = u.Cli.ensure_dir(project_ctx.reports_dir)
        start = time.monotonic()
        project_result = self._check_project_with_ctx(
            project_dir,
            resolved_gates,
            project_ctx,
        )
        elapsed = time.monotonic() - start
        u.Infra.status(
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
        results: MutableSequence[m.Infra.ProjectResult] = []
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

    def _gate_ctx(
        self,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateContext:
        return m.Infra.GateContext(
            workspace=self._workspace_root,
            reports_dir=reports_dir or self._default_reports_dir,
        )

    def _run_gate(
        self,
        gate_id: str,
        project_dir: Path,
        reports_dir: Path | None = None,
        *,
        ctx: m.Infra.GateContext | None = None,
    ) -> m.Infra.GateExecution:
        gate = self._registry.create(gate_id, self._workspace_root)
        if gate is None:
            return m.Infra.GateExecution(
                result=m.Infra.GateResult(
                    gate=gate_id,
                    project=project_dir.name,
                    passed=False,
                    errors=[f"{gate_id} gate not registered"],
                    duration=0.0,
                ),
                issues=(),
                raw_output=f"{gate_id} gate not registered",
            )
        return gate.check(project_dir, ctx or self._gate_ctx(reports_dir))

    def _check_project_with_ctx(
        self,
        project_dir: Path,
        gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        """Run gates for one project as independent DAG stages."""
        project_name = project_dir.name
        result = m.Infra.ProjectResult(project=project_name)

        stages: MutableSequence[m.Cli.PipelineStageSpec] = []
        for gate_id in gates:
            gate_instance = self._registry.create(gate_id, self._workspace_root)
            if gate_instance is None:
                continue
            stages.append(
                m.Cli.PipelineStageSpec(
                    stage_id=gate_id,
                    handler=self._make_gate_handler(
                        gate_instance,
                        project_dir,
                        ctx,
                        result.gates,
                    ),
                ),
            )

        if not stages:
            return result

        pipeline_ctx = m.Cli.PipelineStageContext(
            workspace_root=project_dir,
        )
        u.Cli.execute_pipeline(
            stages,
            pipeline_ctx,
            fail_fast=ctx.fail_fast,
            logger=self._gate_logger,
        )
        return result

    # ------------------------------------------------------------------
    # Pipeline stage helpers
    # ------------------------------------------------------------------

    def _make_gate_handler(
        self,
        gate_instance: FlextInfraGate,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        gates_sink: MutableMapping[str, m.Infra.GateExecution],
    ) -> Callable[[m.Cli.PipelineStageContext], p.Result[m.Cli.PipelineStageResult]]:
        """Build a pipeline stage handler that executes a single gate.

        The handler writes GateExecution into *gates_sink* as a side-effect
        (same pattern as _CodegenPipelineState in the codegen pipeline).
        """
        gate_id = gate_instance.gate_id
        project_name = project_dir.name

        def _handler(
            _pipeline_ctx: m.Cli.PipelineStageContext,
        ) -> p.Result[m.Cli.PipelineStageResult]:
            execution = self._execute_gate(gate_instance, project_dir, ctx)
            gates_sink[gate_id] = execution
            self._gate_logger.debug(
                "gate_executed",
                project=project_name,
                gate=gate_id,
                passed=execution.result.passed,
            )
            u.Infra.gate_result(
                gate_id,
                len(execution.issues),
                passed=execution.result.passed,
                elapsed=execution.result.duration,
            )
            status: t.Cli.PipelineStageStatus = (
                c.Cli.PipelineStageStatus.OK
                if execution.result.passed
                else c.Cli.PipelineStageStatus.FAILED
            )
            return r[m.Cli.PipelineStageResult].ok(
                m.Cli.PipelineStageResult(
                    stage_id=gate_id,
                    status=status,
                    output={"issues": len(execution.issues)},
                ),
            )

        return _handler

    @staticmethod
    def _execute_gate(
        gate_instance: FlextInfraGate,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run fix-then-check or check-only for a single gate instance."""
        if ctx.apply_fixes and (not ctx.check_only) and gate_instance.can_fix:
            fix_execution = gate_instance.fix(project_dir, ctx)
            if not fix_execution.result.passed:
                return fix_execution
        return gate_instance.check(project_dir, ctx)


__all__: list[str] = ["FlextInfraGateRegistry", "FlextInfraWorkspaceCheckGatesMixin"]
