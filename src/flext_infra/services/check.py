"""Public check service mixin for the infra API facade."""

from __future__ import annotations

import importlib
from collections.abc import Sequence

from flext_core import r
from flext_infra import FlextInfraModelsCheck, FlextInfraModelsGates


class FlextInfraServiceCheckMixin:
    """Expose check operations through the public infra facade."""

    def run_workspace_checks(
        self,
        params: FlextInfraModelsCheck.RunCommand,
    ) -> r[bool]:
        """Run quality gates for the selected projects."""
        workspace_check_module = importlib.import_module(
            "flext_infra.check.workspace_check"
        )
        checker_cls = workspace_check_module.FlextInfraWorkspaceChecker
        project_names = params.project_names or []
        if not project_names:
            return r[bool].fail("no projects specified")
        checker_workspace = params.workspace_path
        checker = checker_cls(workspace_root=checker_workspace)
        gates = checker_cls.parse_gate_csv(params.gates)
        ruff_args = checker_cls.parse_tool_args(params.ruff_args)
        pyright_args = checker_cls.parse_tool_args(
            params.pyright_args,
        )
        gate_ctx = FlextInfraModelsGates.GateContext(
            workspace=checker_workspace,
            reports_dir=params.reports_dir_path,
            apply_fixes=params.fix,
            check_only=params.check_only,
            ruff_args=tuple(ruff_args),
            pyright_args=tuple(pyright_args),
        )
        run_result = checker.run_projects(
            projects=project_names,
            gates=gates,
            reports_dir=params.reports_dir_path,
            fail_fast=params.fail_fast,
            ctx=gate_ctx,
        )
        if run_result.is_failure:
            return r[bool].fail(run_result.error or "check failed")
        run_results: Sequence[FlextInfraModelsCheck.ProjectResult] = run_result.value
        failed_projects = [project for project in run_results if not project.passed]
        if failed_projects:
            failed_names = ", ".join(project.project for project in failed_projects)
            return r[bool].fail(f"quality gates failed for: {failed_names}")
        return r[bool].ok(True)

    def fix_pyrefly_config(
        self,
        params: FlextInfraModelsCheck.FixPyreflyConfigCommand,
    ) -> r[bool]:
        """Repair workspace pyrefly configuration through the public facade."""
        fixer_module = importlib.import_module("flext_infra.deps.fix_pyrefly_config")
        fixer_cls = fixer_module.FlextInfraConfigFixer
        fixer = fixer_cls(workspace=params.workspace_path)
        fix_result = fixer.run(
            projects=params.project_names or [],
            dry_run=params.dry_run,
            verbose=params.verbose,
        )
        if fix_result.is_failure:
            return r[bool].fail(
                fix_result.error or "pyrefly config fix failed",
            )
        return r[bool].ok(True)


__all__: Sequence[str] = ("FlextInfraServiceCheckMixin",)
