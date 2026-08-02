"""Gate execution methods for workspace checker."""

from __future__ import annotations

import time
from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar, Literal

from flext_cli import cli
from flext_infra import c, config, m, p, r, t, u
from flext_infra.gates.actionlint import FlextInfraActionlintGate
from flext_infra.gates.bandit import FlextInfraBanditGate
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.gates.canonical_alias import FlextInfraCanonicalAliasGate
from flext_infra.gates.layout import FlextInfraLayoutGate
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.namespace import FlextInfraNamespaceGate
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_infra.gates.pyright import FlextInfraPyrightGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
from flext_infra.gates.runtime_census import FlextInfraRuntimeCensusGate
from flext_infra.gates.silent_failure import FlextInfraSilentFailureGate
from flext_infra.gates.smells import FlextInfraSmellsGate
from flext_infra.gates.tier_whitelist import FlextInfraTierWhitelistGate


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    def __init__(self) -> None:
        """Build the gate-id to gate-class mapping used by check execution."""
        classes = self._gate_classes()
        gate_ids = tuple(gate_cls.gate_id for gate_cls in classes)
        if len(set(gate_ids)) != len(gate_ids):
            msg = "workspace gate identifiers must be unique"
            raise ValueError(msg)
        missing_metadata = set(gate_ids) - set(c.Infra.SARIF_TOOL_INFO)
        if missing_metadata:
            msg = "workspace gates require SARIF metadata: " + ", ".join(
                sorted(missing_metadata)
            )
            raise ValueError(msg)
        implementations = dict(zip(gate_ids, classes, strict=True))
        policy = config.Infra.codegen.make.check
        if set(policy.gate_ids) != set(implementations):
            missing = set(policy.gate_ids) - set(implementations)
            undeclared = set(implementations) - set(policy.gate_ids)
            msg = (
                "configured and implemented check gates must match exactly; "
                f"missing={','.join(sorted(missing)) or '-'}; "
                f"undeclared={','.join(sorted(undeclared)) or '-'}"
            )
            raise ValueError(msg)
        self._gates = {gate.id: implementations[gate.id] for gate in policy.gates}
        self._policy = policy

    @staticmethod
    def _gate_classes() -> t.VariadicTuple[type[FlextInfraGate]]:
        """Return the runtime gate classes registered for workspace checks."""
        return (
            FlextInfraRuffLintGate,
            FlextInfraPyreflyGate,
            FlextInfraMypyGate,
            FlextInfraPyrightGate,
            FlextInfraSilentFailureGate,
            FlextInfraBanditGate,
            FlextInfraMarkdownGate,
            FlextInfraActionlintGate,
            FlextInfraCanonicalAliasGate,
            FlextInfraRuntimeCensusGate,
            FlextInfraNamespaceGate,
            FlextInfraLayoutGate,
            FlextInfraTierWhitelistGate,
            FlextInfraSmellsGate,
        )

    def get(self, gate_id: str) -> type[FlextInfraGate] | None:
        """Return the registered gate class for one gate id, when present."""
        return self._gates.get(gate_id)

    @property
    def gate_ids(self) -> tuple[str, ...]:
        """The sole ordered catalog of executable check gates."""
        return tuple(self._gates)

    def resolve(self, requested: t.StrSequence) -> p.Result[tuple[str, ...]]:
        """Normalize an explicit selection, or select every registered gate."""
        normalized = tuple(
            dict.fromkeys(item.strip() for item in requested if item.strip())
        )
        selected = normalized or self.gate_ids
        unknown = tuple(item for item in selected if item not in self._gates)
        if unknown:
            return r[tuple[str, ...]].fail(f"ERROR: unknown gate '{unknown[0]}'")
        return r[tuple[str, ...]].ok(selected)

    def mode_for(self, gate_id: str) -> Literal["error", "warn"]:
        """Return the config-owned failure posture for one registered gate."""
        return self.spec_for(gate_id).mode

    def spec_for(self, gate_id: str) -> m.Infra.MakeCheckGateSpec:
        """Return the complete config-owned execution row for one gate."""
        spec = self._policy.gate_for(gate_id)
        if spec is None:
            msg = f"workspace gate {gate_id!r} has no configured execution row"
            raise ValueError(msg)
        return spec

    def profile_gate_ids(self, profile: str) -> tuple[str, ...]:
        """Return one config-owned ordered reusable gate subset."""
        return self._policy.profile_gate_ids(profile)

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
        description="Number of projects not executed after fail-fast."
    )
    total_elapsed: float = m.Field(
        description="Total time elapsed in seconds for the entire loop."
    )


class FlextInfraWorkspaceCheckGatesMixin:
    """Gate execution, project loop, and individual gate runner methods."""

    _workspace_root: Path
    _registry: FlextInfraGateRegistry
    _default_reports_dir: Path
    _gate_logger: ClassVar[p.Logger] = u.fetch_logger(__name__)

    def _isolate_context(
        self, ctx: m.Infra.GateContext, target: m.Infra.CheckProjectTarget
    ) -> m.Infra.GateContext:
        """Create a fresh GateContext scoped to a single project."""
        return m.Infra.GateContext(
            workspace=ctx.workspace_root,
            reports_dir=ctx.reports_dir / target.name,
            apply_fixes=ctx.apply_fixes,
            check_only=ctx.check_only,
            fail_fast=ctx.fail_fast,
            ruff_args=ctx.ruff_args,
            pyright_args=ctx.pyright_args,
        )

    def _run_single_project(
        self,
        target: m.Infra.CheckProjectTarget,
        index: int,
        total: int,
        resolved_gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        """Check one previously validated project target."""
        project_dir = target.path
        u.Cli.progress(index, total, target.name, c.Infra.VERB_CHECK)
        project_ctx = self._isolate_context(ctx, target)
        _ = u.Cli.ensure_dir(project_ctx.reports_dir)
        start = time.monotonic()
        project_result = self._check_project_with_ctx(
            project_dir, resolved_gates, project_ctx
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
    ) -> _LoopOutcome:
        """Execute gate checks across projects, collecting results and timing."""
        results: t.MutableSequenceOf[m.Infra.ProjectResult] = []
        total = len(projects)
        failed = 0
        loop_start = time.monotonic()
        for index, target in enumerate(projects, 1):
            project_result = self._run_single_project(
                target, index, total, resolved_gates, ctx
            )
            results.append(project_result)
            if not project_result.passed:
                failed += 1
                if fail_fast:
                    break
        return _LoopOutcome(
            results=tuple(results),
            failed=failed,
            skipped=total - len(results),
            total_elapsed=time.monotonic() - loop_start,
        )

    def _gate_ctx(self, reports_dir: Path | None = None) -> m.Infra.GateContext:
        """Gate ctx."""
        return m.Infra.GateContext(
            workspace=self._workspace_root,
            reports_dir=reports_dir or self._default_reports_dir,
        )

    def _configured_gate_context(
        self, gate_id: str, ctx: m.Infra.GateContext
    ) -> m.Infra.GateContext:
        """Overlay one gate's typed execution row onto the shared context."""
        spec = self._registry.spec_for(gate_id)
        return ctx.model_copy(
            update={
                "gate_mode": spec.mode,
                "gate_command": spec.command,
                "gate_execution_scope": spec.execution_scope,
            }
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
        base_ctx = ctx or self._gate_ctx(reports_dir)
        return gate.check(project_dir, self._configured_gate_context(gate_id, base_ctx))

    def _check_project_with_ctx(
        self, project_dir: Path, gates: t.StrSequence, ctx: m.Infra.GateContext
    ) -> m.Infra.ProjectResult:
        """Run gates for one project as independent DAG stages."""
        project_name = project_dir.name
        result = m.Infra.ProjectResult(project=project_name)

        stages: t.MutableSequenceOf[m.Cli.PipelineStageSpec] = []
        for gate_id in gates:
            gate_instance = self._registry.create(gate_id, self._workspace_root)
            if gate_instance is None:
                result.gates[gate_id] = self._run_gate(gate_id, project_dir, ctx=ctx)
                continue
            stages.append(
                cli.stage(
                    gate_id,
                    handler=self._make_gate_handler(
                        gate_instance, project_dir, ctx, result.gates
                    ),
                )
            )

        if not stages:
            return result

        cli.pipeline(
            stages,
            context=cli.stage_context(project_dir),
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
            """Run the gate and record its execution in the sink."""
            gate_ctx = self._configured_gate_context(gate_id, ctx)
            execution = self._execute_gate(gate_instance, project_dir, gate_ctx)
            gates_sink[gate_id] = execution
            self._gate_logger.debug(
                "gate_executed",
                project=project_name,
                gate=gate_id,
                passed=execution.result.passed,
            )
            u.Cli.gate_result(
                gate_id,
                execution.error_count,
                passed=execution.result.passed,
                elapsed=execution.result.duration,
            )
            if not execution.result.passed:
                inline_errors = execution.result.errors[
                    : c.Infra.GATE_ERROR_OUTPUT_LIMIT
                ]
                for error in inline_errors:
                    u.Cli.error(error)
                remaining = len(execution.result.errors) - len(inline_errors)
                if remaining > 0:
                    u.Cli.error(
                        f"... {remaining} additional diagnostics in the check report"
                    )
                if not inline_errors and execution.raw_output.strip():
                    u.Cli.error(execution.raw_output.strip())
            status: t.Cli.PipelineStageStatus = (
                c.Cli.PipelineStageStatus.OK
                if execution.result.passed
                else c.Cli.PipelineStageStatus.FAILED
            )
            return r[m.Cli.PipelineStageResult].ok(
                cli.stage_result(
                    gate_id, status=status, output={"errors": execution.error_count}
                )
            )

        return _handler

    @staticmethod
    def _execute_gate(
        gate_instance: FlextInfraGate, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run fix-then-check or check-only for a single gate instance."""
        if ctx.apply_fixes and (not ctx.check_only) and gate_instance.can_fix:
            fix_execution = gate_instance.fix(project_dir, ctx)
            if not fix_execution.result.passed:
                return fix_execution
        return gate_instance.check(project_dir, ctx)


__all__: list[str] = ["FlextInfraGateRegistry", "FlextInfraWorkspaceCheckGatesMixin"]
