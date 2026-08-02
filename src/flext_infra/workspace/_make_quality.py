"""Quality operation adapters for the typed Make runtime."""

from __future__ import annotations

import time

from flext_core import r
from flext_infra import c, m, p, u
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
from flext_infra.validate.pytest_selector import FlextInfraPytestSelectorValidator
from flext_infra.workspace._make_lifecycle import FlextInfraMakeLifecycleMixin


class FlextInfraMakeQualityMixin(FlextInfraMakeLifecycleMixin):
    """Route check, test, format, and fix to each canonical quality owner."""

    def _execute_quality_check(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        gates = self._input_values(context.invocation, "gates")
        fail_fast = self._input_flag(context.invocation, "fail-fast")
        reports = u.Cli.resolve_report_dir(
            context.workspace_root, c.Infra.PROJECT, c.Infra.VERB_CHECK
        )
        gate_context = m.Infra.GateContext(
            workspace=context.workspace_root, reports_dir=reports, fail_fast=fail_fast
        )
        checked = FlextInfraWorkspaceChecker(
            workspace_root=context.workspace_root
        ).run_projects(
            tuple(
                m.Infra.CheckProjectTarget(
                    name=selected.repository.name, path=selected.root
                )
                for selected in context.targets
            ),
            gates,
            reports_dir=reports,
            fail_fast=fail_fast,
            ctx=gate_context,
        )
        if checked.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(checked)
            )
        failed = tuple(item.project for item in checked.value if not item.passed)
        if failed:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.FAIL),
                f"quality check failed for: {', '.join(failed)}",
            )
        return r.ok(self._success_exit())

    def _pytest_targets(
        self, context: m.Infra.MakeExecutionContext, file_value: str | None
    ) -> p.Result[tuple[m.Infra.MakeTargetSpec, ...]]:
        if file_value is None:
            return r.ok(context.targets)
        resolved = FlextInfraPytestSelectorValidator.resolve_file(
            context.target.root, file_value
        )
        if resolved.failure:
            return r.fail(r.require_error(resolved))
        governed = self._governed_targets(context.workspace_root, context.workspace)
        owners = tuple(
            item for item in governed if resolved.value.is_relative_to(item.root)
        )
        if not owners:
            return r.fail(f"no governed project owns pytest file: {file_value}")
        owner = max(owners, key=lambda item: len(item.root.parts))
        if owner not in context.targets:
            return r.fail(
                f"pytest file owner was not selected: {owner.repository.name}"
            )
        return r.ok((owner,))

    @staticmethod
    def _pytest_file_for_target(
        context: m.Infra.MakeExecutionContext,
        selected: m.Infra.MakeTargetSpec,
        file_value: str | None,
    ) -> str | None:
        if file_value is None:
            return None
        prefix, separator, node = file_value.partition("::")
        relative = (
            (context.target.root / prefix)
            .resolve()
            .relative_to(selected.root)
            .as_posix()
        )
        return f"{relative}::{node}" if separator else relative

    def _execute_quality_test(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        file_value = next(iter(self._input_values(context.invocation, "file")), None)
        selected_targets = self._pytest_targets(context, file_value)
        if selected_targets.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(selected_targets)
            )
        started_at = time.monotonic()
        failures: list[str] = []
        fail_fast = self._input_flag(context.invocation, "fail-fast")
        match_value = next(iter(self._input_values(context.invocation, "match")), None)
        for selected in selected_targets.value:
            tested = FlextInfraPytestRunner(
                workspace_root=selected.root,
                started_at_monotonic=started_at,
                file=self._pytest_file_for_target(context, selected, file_value),
                match=match_value,
                what="all",
                target=None,
                reports=str(context.make.test.reports_dir),
                fail_fast=fail_fast,
                verbose=self._input_flag(context.invocation, "verbose"),
                diagnostic=self._input_flag(context.invocation, "diag"),
            ).execute()
            if tested.failure:
                failures.append(r.require_error(tested))
            elif tested.value != 0:
                failures.append(f"pytest failed: {selected.root}")
            if failures and fail_fast:
                break
        if failures:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.FAIL), "; ".join(failures)
            )
        return r.ok(self._success_exit())

    def _execute_quality_format(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        reports = u.Cli.resolve_report_dir(
            context.workspace_root, c.Infra.PROJECT, "fmt"
        )
        gate_context = m.Infra.GateContext(
            workspace=context.workspace_root,
            reports_dir=reports,
            apply_fixes=context.invocation.applying,
        )
        gate = FlextInfraRuffFormatGate(context.workspace_root)
        for selected in context.targets:
            execution = (
                gate.fix(selected.root, gate_context)
                if context.invocation.applying
                else gate.check(selected.root, gate_context)
            )
            if not execution.result.passed:
                detail = execution.raw_output.strip() or "; ".join(
                    execution.result.errors
                )
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.FAIL),
                    f"Ruff format failed: {selected.root}: "
                    f"{detail if detail else '<no diagnostic>'}",
                )
        return r.ok(self._success_exit())

    def _execute_quality_fix(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        reports = u.Cli.resolve_report_dir(
            context.workspace_root, c.Infra.PROJECT, "fix"
        )
        gate_context = m.Infra.GateContext(
            workspace=context.workspace_root, reports_dir=reports, apply_fixes=True
        )
        gate = FlextInfraRuffLintGate(context.workspace_root)
        for selected in context.targets:
            execution = gate.fix(selected.root, gate_context)
            if not execution.result.passed:
                detail = execution.raw_output.strip() or "; ".join(
                    execution.result.errors
                )
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.FAIL),
                    f"Ruff fix failed: {selected.root}: "
                    f"{detail if detail else '<no diagnostic>'}",
                )
        return r.ok(self._success_exit())


__all__: list[str] = ["FlextInfraMakeQualityMixin"]
