"""Gate execution methods for workspace checker.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import MutableMapping
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_cli import cli

from flext_infra import c, config, m, p, r, t, u
from flext_infra.check import FlextInfraWorkspaceCheckUnionMixin

if TYPE_CHECKING:
    from flext_infra.check import FlextInfraGateRegistry
    from flext_infra.gates import FlextInfraGate


class FlextInfraWorkspaceCheckGatesMixin(FlextInfraWorkspaceCheckUnionMixin):
    """Gate execution, project loop, and individual gate runner methods."""

    _repository_root: Path
    _registry: FlextInfraGateRegistry
    _default_reports_dir: Path
    _gate_logger: ClassVar[p.Logger] = u.fetch_logger(__name__)

    def _run_single_project(
        self,
        target: m.Infra.CheckProjectTarget,
        resolved_gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        """Check one project after the loop has validated its target.

        Returns:
            The resulting ``m.Infra.ProjectResult``.

        """
        project_dir = target.path
        project_ctx = self._isolate_context(ctx, target)
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
            target.name,
            result=project_result.passed,
            elapsed=elapsed,
        )
        return project_result

    def _run_project_loop(
        self,
        projects: t.SequenceOf[m.Infra.CheckProjectTarget],
        resolved_gates: t.StrSequence,
        ctx: m.Infra.GateContext,
        *,
        fail_fast: bool,
    ) -> m.Infra.LoopOutcome:
        """Execute gate checks across projects, collecting results and timing.

        Retain the interrupted project's result before stopping the invocation.
        Ordinary failed verdicts keep the caller's fail-fast policy.

        Returns:
            The resulting ``m.Infra.LoopOutcome``.

        """
        results: t.MutableSequenceOf[m.Infra.ProjectResult] = []
        total = len(projects)
        failed = 0
        loop_start = time.monotonic()
        union_gates = self._union_gate_ids(projects, resolved_gates, ctx)
        union_executions = self._run_union_gates(projects, union_gates, ctx)
        project_gates = tuple(
            gate_id for gate_id in resolved_gates if gate_id not in union_gates
        )
        for index, target in enumerate(projects, 1):
            u.Cli.progress(index, total, target.name, c.Infra.VERB_CHECK)
            project_result = self._run_single_project(
                target,
                tuple(
                    gate_id
                    for gate_id in project_gates
                    if ctx.selected_files or gate_id in target.applicable_gates
                ),
                ctx,
            )
            if union_gates:
                project_result = self._merged_union_result(
                    project_result,
                    resolved_gates,
                    {
                        gate_id: executions[target.path]
                        for gate_id, executions in union_executions.items()
                        if target.path in executions
                    },
                )
            results.append(project_result)
            if not project_result.gates and ctx.check_progress is not None:
                ctx.check_progress(target.path, project_result)
            project_passed: bool = project_result.passed
            if not project_passed:
                failed += 1
            if any(
                execution.interrupted for execution in project_result.gates.values()
            ) or (not project_passed and fail_fast):
                break
        return m.Infra.LoopOutcome(
            results=tuple(results),
            failed=failed,
            total_elapsed=time.monotonic() - loop_start,
        )

    @staticmethod
    def _gate_parallelism(stage_count: int) -> int:
        """Bound concurrent read-only gates by the typed Mypy memory reservation.

        Each concurrent gate may host one whole-program checker, so the host's
        physical memory divided by the memory the tooling policy reserves for
        one Mypy run caps the concurrency.

        Returns:
            The number of gates that may run at once, at least one.

        """
        physical_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        reserved_bytes = u.Infra.mypy_resource_limit().memory_limit_bytes
        return max(1, min(stage_count, physical_bytes // reserved_bytes))

    def _gate_ctx(self, reports_dir: Path | None = None) -> m.Infra.GateContext:
        """Gate ctx.

        Returns:
            The resulting ``m.Infra.GateContext``.

        """
        return m.Infra.GateContext(
            repository_root=self._repository_root,
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
        """Run gate.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        gate = self._registry.create(gate_id, self._repository_root)
        if gate is None:
            gate_ctx = ctx or self._gate_ctx(reports_dir)
            message = f"{gate_id} gate not registered"
            receipt = gate_ctx.reports_dir / (
                f"{gate_id}{config.Infra.tooling.raw_check_receipt_suffix}"
            )
            u.Cli.atomic_write_text_file(receipt, message).unwrap()
            return m.Infra.GateExecution(
                result=m.Infra.GateResult(
                    gate=gate_id,
                    project=project_dir.name,
                    passed=False,
                    errors=[message],
                    duration=0.0,
                ),
                issues=(),
                raw_output=message,
                raw_receipt=receipt,
                outcome=c.Infra.ToolOutcome.ERROR,
            )
        return gate.check(project_dir, ctx or self._gate_ctx(reports_dir))

    def _check_project_with_ctx(
        self,
        project_dir: Path,
        gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        """Run gates for one project and retain every executed gate in order.

        Read-only gates share no mutable state, so they run concurrently
        through the public CLI pipeline inside one process signal wave,
        bounded by the memory the typed Mypy policy reserves per
        whole-program checker. Repairs share mutable files and keep their
        declared serial order and locks; an explicit fail-fast run stays
        serial so it can stop at the first failure. Every operation retains
        its verdict and receipt, reported in declared order.

        Returns:
            The resulting ``m.Infra.ProjectResult``.

        """
        result = m.Infra.ProjectResult(project=project_dir.name)
        mutating = ctx.apply_fixes and not ctx.check_only
        executions: MutableMapping[str, m.Infra.GateExecution] = {}
        instances = self._gate_instances(gates, mutating=mutating)
        concurrent = (
            self._run_concurrent_stages(instances, project_dir, ctx, executions)
            if not mutating and not ctx.fail_fast and len(instances) > 1
            else {}
        )
        for gate_instance in instances:
            gate_id = gate_instance.gate_id
            pipeline_result = (
                concurrent[gate_id]
                if gate_id in concurrent
                else self._run_gate_stage(
                    gate_instance, project_dir, ctx, executions, ctx.signal_wave
                )
            )
            execution = executions[gate_id]
            if execution.result.passed:
                pipeline_result.unwrap()
            result.gates[gate_id] = execution
            if ctx.check_progress is not None:
                ctx.check_progress(project_dir, result)
            self._report_gate_execution(gate_id, execution)
            # A concurrent wave already ran every gate: each one is reported.
            if not concurrent and (
                execution.interrupted or (not execution.result.passed and ctx.fail_fast)
            ):
                break
        return result

    def _gate_instances(
        self,
        gates: t.StrSequence,
        *,
        mutating: bool,
    ) -> t.SequenceOf[FlextInfraGate]:
        """Create every requested gate before any of them runs.

        Returns:
            The gate instances, in requested order.

        Raises:
            ValueError: If a gate is unregistered or a selected repair is unsupported.

        """
        instances: t.MutableSequenceOf[FlextInfraGate] = []
        for gate_id in gates:
            gate_instance = self._registry.create(gate_id, self._repository_root)
            if gate_instance is None:
                msg = f"{gate_id} gate not registered"
                raise ValueError(msg)
            if mutating and not gate_instance.can_fix:
                msg = f"Gate {gate_id} does not support repair"
                raise ValueError(msg)
            instances.append(gate_instance)
        return instances

    def _run_concurrent_stages(
        self,
        instances: t.SequenceOf[FlextInfraGate],
        project_dir: Path,
        ctx: m.Infra.GateContext,
        executions: MutableMapping[str, m.Infra.GateExecution],
    ) -> t.MappingKV[str, p.Result[m.Cli.PipelineResult]]:
        """Run read-only gate stages concurrently in one signal wave.

        The main thread owns operator-signal forwarding; each stage receives
        the wave, so its child process groups subscribe to it. The first
        stage exception escapes in declared order.

        Returns:
            Every stage's pipeline result by gate id.

        """
        waved = u.Cli.run_in_signal_wave(
            tuple(
                partial(
                    self._run_gate_stage, gate_instance, project_dir, ctx, executions
                )
                for gate_instance in instances
            ),
            max_workers=self._gate_parallelism(len(instances)),
        )
        return {
            gate_instance.gate_id: stage_result
            for gate_instance, stage_result in zip(instances, waved, strict=True)
        }

    @staticmethod
    def _report_gate_execution(gate_id: str, execution: m.Infra.GateExecution) -> None:
        """Report one gate's verdict and, when it is not clean, its receipt."""
        u.Cli.gate_result(
            gate_id,
            execution.finding_count,
            passed=execution.result.passed,
            elapsed=execution.result.duration,
        )
        if (
            execution.issues or not execution.result.passed
        ) and execution.raw_receipt is not None:
            u.Cli.info(
                f"{gate_id}: {execution.outcome.value}; "
                f"Native output receipt: {execution.raw_receipt}",
            )

    # ------------------------------------------------------------------
    # Pipeline stage helpers
    # ------------------------------------------------------------------

    def _run_gate_stage(
        self,
        gate_instance: FlextInfraGate,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        executions: MutableMapping[str, m.Infra.GateExecution],
        signal_wave: p.Cli.SignalWave | None,
    ) -> p.Result[m.Cli.PipelineResult]:
        """Run one gate stage through the public CLI pipeline.

        A stage run inside a concurrent wave receives that wave, so its child
        process groups subscribe to the main thread's signal forwarding.

        Returns:
            The stage's pipeline result.

        """
        stage = m.Cli.PipelineStageSpec(
            stage_id=gate_instance.gate_id,
            handler=self._make_gate_handler(
                gate_instance,
                project_dir,
                ctx.model_copy(update={"signal_wave": signal_wave}),
                executions,
            ),
        )
        return cli.pipeline(
            (stage,),
            context=m.Cli.PipelineStageContext(repository_root=project_dir),
            logger=self._gate_logger,
        )

    def _make_gate_handler(
        self,
        gate_instance: FlextInfraGate,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        gates_sink: MutableMapping[str, m.Infra.GateExecution],
    ) -> p.Cli.PipelineStage:
        """Build a pipeline stage handler that executes a single gate.

        The handler only records the GateExecution into *gates_sink*; reporting
        happens after the individual stage, in declared gate order.

        Returns:
            The resulting ``p.Cli.PipelineStage``.

        """
        gate_id = gate_instance.gate_id
        project_name = project_dir.name

        def _handler(
            _pipeline_ctx: p.Cli.PipelineStageContext,
            /,
        ) -> p.Result[m.Cli.PipelineStageResult]:
            """Run the gate and record its execution in the sink.

            Returns:
                The resulting ``p.Result[m.Cli.PipelineStageResult]``.

            """
            del _pipeline_ctx
            gate_ctx = ctx.model_copy()
            execution = self._execute_gate(gate_instance, project_dir, gate_ctx)
            gates_sink[gate_id] = execution
            self._gate_logger.info(
                "gate_executed",
                project=project_name,
                gate=gate_id,
                passed=execution.result.passed,
                elapsed=execution.result.duration,
            )
            if not execution.result.passed:
                return r[m.Cli.PipelineStageResult].fail(
                    f"{gate_id} failed for {project_name} "
                    f"with {len(execution.issues)} findings",
                )
            return r[m.Cli.PipelineStageResult].ok(
                m.Cli.PipelineStageResult(
                    stage_id=gate_id,
                    status=c.Cli.PipelineStageStatus.OK,
                    output={"findings": execution.finding_count},
                ),
            )

        return _handler

    @staticmethod
    def _execute_gate(
        gate_instance: FlextInfraGate,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Dispatch exactly the requested repair or read-only operation.

        A gate without a repair contract cannot substitute a read-only check.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            ValueError: If a repair selects a gate without a repair contract.

        """
        if ctx.apply_fixes and not ctx.check_only:
            if not gate_instance.can_fix:
                msg = f"Gate {gate_instance.gate_id} does not support repair"
                raise ValueError(msg)
            return gate_instance.fix(project_dir, ctx)
        if ctx.selected_files:
            return gate_instance.check_files(ctx.selected_files, project_dir, ctx)
        return gate_instance.check(project_dir, ctx)


__all__: list[str] = ["FlextInfraWorkspaceCheckGatesMixin"]
