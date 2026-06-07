"""Per-project gate execution engine (DAG stages + single-gate runner) — extracted."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_cli import cli
from flext_infra import (
    FlextInfraGate,
    c,
    m,
    p,
    r,
    t,
    u,
)

if TYPE_CHECKING:
    from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry


class FlextInfraWorkspaceCheckGateEngineMixin:
    """Run the registered gates for one project as independent pipeline stages.

    Composed into FlextInfraWorkspaceCheckGatesMixin via inheritance; borrows
    ``_workspace_root``/``_registry``/``_default_reports_dir`` from the checker
    via MRO.
    """

    _gate_logger: ClassVar[p.Logger] = u.fetch_logger(__name__)

    if TYPE_CHECKING:
        _workspace_root: Path
        _registry: FlextInfraGateRegistry
        _default_reports_dir: Path

    def _gate_ctx(
        self,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateContext:
        """Gate ctx."""
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
        """Run gate."""
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

        stages: t.MutableSequenceOf[m.Cli.PipelineStageSpec] = []
        for gate_id in gates:
            gate_instance = self._registry.create(gate_id, self._workspace_root)
            if gate_instance is None:
                continue
            stages.append(
                cli.stage(
                    gate_id,
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

        cli.pipeline(
            stages,
            workspace_root=project_dir,
            fail_fast=ctx.fail_fast,
            logger=self._gate_logger,
        )
        return result

    def _make_gate_handler(
        self,
        gate_instance: FlextInfraGate,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        gates_sink: MutableMapping[str, m.Infra.GateExecution],
    ) -> t.Cli.PipelineHandler:
        """Build a pipeline stage handler that executes a single gate.

        The handler writes GateExecution into *gates_sink* as a side-effect
        (same pattern as _CodegenPipelineState in the codegen pipeline).
        """
        gate_id = gate_instance.gate_id
        project_name = project_dir.name

        def _handler(
            _pipeline_ctx: m.Cli.PipelineStageContext,
        ) -> p.Result[m.Cli.PipelineStageResult]:
            """Handler."""
            execution = self._execute_gate(gate_instance, project_dir, ctx)
            gates_sink[gate_id] = execution
            self._gate_logger.debug(
                "gate_executed",
                project=project_name,
                gate=gate_id,
                passed=execution.result.passed,
            )
            u.Cli.gate_result(
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
                cli.stage_result(
                    gate_id,
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


__all__: list[str] = ["FlextInfraWorkspaceCheckGateEngineMixin"]
