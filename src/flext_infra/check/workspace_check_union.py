"""Union-gate execution for the workspace checker.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, u

if TYPE_CHECKING:
    from flext_infra.check import FlextInfraGateRegistry


class FlextInfraWorkspaceCheckUnion:
    """Run each multi-root gate once per configuration group and split it back."""

    _repository_root: Path
    _registry: FlextInfraGateRegistry

    @staticmethod
    def _isolate_context(
        ctx: m.Infra.GateContext,
        target: m.Infra.CheckProjectTarget,
    ) -> m.Infra.GateContext:
        """Create a fresh GateContext scoped to a physical project path.

        Returns:
            The resulting ``m.Infra.GateContext``.

        Raises:
            ValueError: If the context carries runtime dependency inputs
                that belong to a different project target, or the project
                is outside the invoked repository.

        """
        if (
            ctx.runtime_dependency_inputs is not None
            and ctx.runtime_dependency_inputs.target_root != target.path
        ):
            msg = "dependency provenance belongs to another project"
            raise ValueError(msg)
        root = ctx.repository_root.resolve()
        relative = target.path.resolve().relative_to(root)
        receipt_path = Path(root.name) / relative
        return ctx.model_copy(update={"reports_dir": ctx.reports_dir / receipt_path})

    def _union_gate_ids(
        self,
        projects: Sequence[m.Infra.CheckProjectTarget],
        resolved_gates: Sequence[str],
        ctx: m.Infra.GateContext,
    ) -> Sequence[str]:
        """Elect the gates whose tool runs once over every project's targets.

        A multi-project run executes each multi-root tool in one invocation;
        a literal file selection keeps its single-owner contract.

        Returns:
            The union-capable gate ids, empty for a single-project run.

        Raises:
            ValueError: If a requested gate is not registered.

        """
        if len(projects) < c.Infra.UNION_GATE_MIN_PROJECTS or ctx.selected_files:
            return ()
        elected: MutableSequence[str] = []
        for gate_id in resolved_gates:
            gate = self._registry.create(gate_id, self._repository_root)
            if gate is None:
                msg = f"{gate_id} gate not registered"
                raise ValueError(msg)
            if gate.union_capable:
                elected.append(gate_id)
        return tuple(elected)

    def _run_union_gates(
        self,
        projects: Sequence[m.Infra.CheckProjectTarget],
        union_gates: Sequence[str],
        ctx: m.Infra.GateContext,
    ) -> Mapping[str, Mapping[Path, m.Infra.GateExecution]]:
        """Run every union gate once per configuration group, split per project.

        Returns:
            Per gate, the execution each selected project receives.

        Raises:
            ValueError: If a union gate is not registered.

        """
        executions: MutableMapping[str, Mapping[Path, m.Infra.GateExecution]] = {}
        for gate_id in union_gates:
            gate = self._registry.create(gate_id, self._repository_root)
            if gate is None:
                msg = f"{gate_id} gate not registered"
                raise ValueError(msg)
            groups: MutableMapping[
                str, MutableSequence[m.Infra.CheckProjectTarget]
            ] = {}
            for target in projects:
                if gate_id in target.applicable_gates:
                    groups.setdefault(gate.union_group_key(target.path), []).append(
                        target,
                    )
            split: MutableMapping[Path, m.Infra.GateExecution] = {}
            for selected in groups.values():
                owner_ctx = self._isolate_context(ctx, selected[0])
                _ = u.Cli.ensure_dir(owner_ctx.reports_dir)
                directories = tuple(target.path for target in selected)
                execution = (
                    gate.fix_union(directories, owner_ctx)
                    if ctx.apply_fixes and not ctx.check_only
                    else gate.check_union(directories, owner_ctx)
                )
                u.Cli.gate_result(
                    gate_id,
                    execution.finding_count,
                    passed=execution.result.passed,
                    elapsed=execution.result.duration,
                )
                split.update(self._split_union_execution(execution, selected))
            if split:
                executions[gate_id] = split
        return executions

    @staticmethod
    def _split_union_execution(
        execution: m.Infra.GateExecution,
        selected: Sequence[m.Infra.CheckProjectTarget],
    ) -> Mapping[Path, m.Infra.GateExecution]:
        """Assign each finding of one union group to its deepest owning project.

        A native tool error fails every selected project with the complete
        diagnostics; otherwise a project passes when no finding is its own.

        Returns:
            The execution each selected project reports.

        Raises:
            ValueError: If a finding lies outside every selected project.

        """
        # The group's first project owned the invocation's working directory,
        # so a relative finding resolves against it.
        root = selected[0].path.resolve()
        owners = sorted(
            ((target, target.path.resolve()) for target in selected),
            key=lambda owner: len(owner[1].parts),
            reverse=True,
        )
        native_error = execution.outcome is c.Infra.ToolOutcome.ERROR
        owned: MutableMapping[Path, MutableSequence[m.Infra.Issue]] = {
            target.path: [] for target in selected
        }
        for issue in execution.issues:
            location = Path(issue.file)
            absolute = (
                location if location.is_absolute() else root / location
            ).resolve()
            owner = next(
                (
                    (target, path)
                    for target, path in owners
                    if absolute.is_relative_to(path)
                ),
                None,
            )
            if owner is None:
                msg = f"union finding outside every selected project: {issue.file}"
                raise ValueError(msg)
            target, path = owner
            owned[target.path].append(
                issue.model_copy(
                    update={"file": absolute.relative_to(path).as_posix()}
                ),
            )
        return {
            target.path: execution.model_copy(
                update={
                    "issues": tuple(owned[target.path]),
                    "result": execution.result.model_copy(
                        update={
                            "project": target.name,
                            "passed": execution.result.passed
                            or (not native_error and not owned[target.path]),
                        },
                    ),
                },
            )
            for target in selected
        }

    @staticmethod
    def _merged_union_result(
        project_result: m.Infra.ProjectResult,
        resolved_gates: Sequence[str],
        union_executions: Mapping[str, m.Infra.GateExecution],
    ) -> m.Infra.ProjectResult:
        """Report the union and per-project executions in declared gate order.

        Returns:
            The project's result with every executed gate in declared order.

        """
        executed = {**project_result.gates, **union_executions}
        return project_result.model_copy(
            update={
                "gates": {
                    gate_id: executed[gate_id]
                    for gate_id in resolved_gates
                    if gate_id in executed
                },
            },
        )


__all__: list[str] = ["FlextInfraWorkspaceCheckUnion"]
