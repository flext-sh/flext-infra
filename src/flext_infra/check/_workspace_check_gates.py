"""Gate execution methods for workspace checker."""

from __future__ import annotations

import time
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraGateRegistry,
    c,
    m,
    t,
    u,
)


class _LoopOutcome(m.ArbitraryTypesModel):
    """Bundled results from the project-checking loop."""

    results: Sequence[m.Infra.ProjectResult]
    failed: int
    skipped: int
    total_elapsed: float


class FlextInfraWorkspaceCheckGatesMixin:
    """Gate execution, project loop, and individual gate runner methods."""

    _workspace_root: Path
    _registry: FlextInfraGateRegistry
    _default_reports_dir: Path

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
        pyproject_path = project_dir / c.Infra.Files.PYPROJECT_FILENAME
        if not project_dir.is_dir() or not pyproject_path.exists():
            u.progress(index, total, project_name, c.Infra.Severity.SKIP)
            return None
        u.progress(index, total, project_name, c.Infra.Verbs.CHECK)
        start = time.monotonic()
        project_result = self._check_project_with_ctx(
            project_dir,
            resolved_gates,
            ctx,
        )
        elapsed = time.monotonic() - start
        u.status(
            c.Infra.Verbs.CHECK,
            project_name,
            project_result.passed,
            elapsed,
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
            results=results,
            failed=failed,
            skipped=skipped,
            total_elapsed=time.monotonic() - loop_start,
        )

    def _gate_ctx(
        self,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateContext:
        return m.Infra.GateContext(
            workspace_root=self._workspace_root,
            reports_dir=reports_dir or self._default_reports_dir,
        )

    def _run_pyrefly(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.PYREFLY, project_dir, reports_dir)

    def _run_mypy(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.MYPY, project_dir, reports_dir)

    def _run_pyright(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.PYRIGHT, project_dir, reports_dir)

    def _run_bandit(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.SECURITY, project_dir, reports_dir)

    def _run_markdown(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.MARKDOWN, project_dir, reports_dir)

    def _run_go(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.GO, project_dir, reports_dir)

    def _run_ruff_format(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.FORMAT, project_dir, reports_dir)

    def _run_ruff_lint(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.LINT, project_dir, reports_dir)

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
                issues=[],
                raw_output=f"{gate_id} gate not registered",
            )
        return gate.check(project_dir, ctx or self._gate_ctx(reports_dir))

    def _check_project_with_ctx(
        self,
        project_dir: Path,
        gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        """Run gates for one project using a pre-built GateContext."""
        result = m.Infra.ProjectResult(project=project_dir.name)
        for gate in gates:
            gate_instance = self._registry.create(gate, self._workspace_root)
            if gate_instance is None:
                continue
            if ctx.apply_fixes and (not ctx.check_only) and gate_instance.can_fix:
                fix_execution = gate_instance.fix(project_dir, ctx)
                if not fix_execution.result.passed:
                    result.gates[gate] = fix_execution
                    u.gate_result(
                        gate,
                        len(fix_execution.issues),
                        fix_execution.result.passed,
                        fix_execution.result.duration,
                    )
                    continue
            execution = gate_instance.check(project_dir, ctx)
            result.gates[gate] = execution
            u.gate_result(
                gate,
                len(execution.issues),
                execution.result.passed,
                execution.result.duration,
            )
        return result

    def _check_project(
        self,
        project_dir: Path,
        gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        return self._check_project_with_ctx(project_dir, gates, ctx)


__all__ = ["FlextInfraWorkspaceCheckGatesMixin"]
