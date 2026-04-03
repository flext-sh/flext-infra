"""CLI mixin for github commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r
from flext_infra import c, m, t, u

if TYPE_CHECKING:
    import typer


class FlextInfraCliGithub:
    """GitHub CLI group — composed into FlextInfraCli via MRO."""

    def register_github(self, app: typer.Typer) -> None:
        """Register github commands on the given Typer app."""
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="workflows",
                help_text="Sync GitHub workflow files across workspace",
                model_cls=m.Infra.GithubWorkflowsInput,
                handler=self._handle_workflows,
                failure_message="Workflow sync failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name=c.Infra.LINT_SECTION,
                help_text="Lint GitHub workflow files",
                model_cls=m.Infra.GithubLintInput,
                handler=self._handle_lint,
                failure_message="Workflow lint failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name=c.Infra.PR,
                help_text="Manage pull requests for a single project",
                model_cls=m.Infra.GithubPrInput,
                handler=self._handle_pr,
                failure_message="PR operation failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="pr-workspace",
                help_text="Manage pull requests across workspace projects",
                model_cls=m.Infra.GithubPrWorkspaceInput,
                handler=self._handle_pr_workspace,
                failure_message="PR workspace orchestration failed",
            ),
        )

    @staticmethod
    def _handle_workflows(params: m.Infra.GithubWorkflowsInput) -> r[bool]:
        """Sync GitHub workflow files."""
        result = u.github_sync_workspace_workflows(
            workspace_root=Path(params.workspace),
            params=m.Infra.WorkflowSyncParams(
                apply=params.apply,
                prune=params.prune,
            ),
        )
        if result.is_failure:
            return r[bool].fail(result.error or "workflow sync failed")
        return r[bool].ok(True)

    @staticmethod
    def _handle_lint(params: m.Infra.GithubLintInput) -> r[m.Infra.WorkflowLintResult]:
        """Lint GitHub workflow files across workspace."""
        report_path = Path(params.report) if params.report else None
        result: r[m.Infra.WorkflowLintResult] = u.github_lint_workflows(
            workspace_root=Path(params.workspace),
            report_path=report_path,
            strict=params.strict,
        )
        if result.is_failure:
            return result
        if result.value.status != "ok" and params.strict:
            return r[m.Infra.WorkflowLintResult].fail(
                f"Workflow lint found issues: {result.value.detail}",
            )
        return result

    @staticmethod
    def _handle_pr(params: m.Infra.GithubPrInput) -> r[m.Infra.PrExecutionResultModel]:
        """Manage pull requests for a single project."""
        repo_root = Path(params.repo_root)
        pr_args: t.StrMapping = {
            "action": params.action,
            "base": params.base,
            "head": params.head or "",
            "number": u.ensure_str(params.number),
            "title": params.title or "",
            "body": params.body or "",
            "draft": "1" if params.draft else "0",
            "merge_method": params.merge_method,
            "auto": "1" if params.auto else "0",
            "delete_branch": "1" if params.delete_branch else "0",
            "checks_strict": "1" if params.checks_strict else "0",
            "release_on_merge": "1" if params.release_on_merge else "0",
        }
        result = u.github_pr_run_single(
            repo_root=repo_root,
            workspace_root=repo_root,
            pr_args=pr_args,
        )
        if result.is_failure:
            return result
        if result.value.exit_code != 0:
            return r[m.Infra.PrExecutionResultModel].fail(
                f"PR operation exited with code {result.value.exit_code}",
            )
        return result

    @staticmethod
    def _handle_pr_workspace(
        params: m.Infra.GithubPrWorkspaceInput,
    ) -> r[m.Infra.PrOrchestrationResult]:
        """Manage PRs across workspace."""
        project_names: t.StrSequence | None = None
        if params.project:
            project_names = u.project_names_from_values(params.project)
        pr_model = m.Infra.PrWorkspaceArgs(
            include_root=params.include_root,
            branch=params.branch,
            checkpoint=params.checkpoint,
            fail_fast=params.fail_fast,
            pr_action=params.pr_action,
            pr_base=params.pr_base,
            pr_head=params.pr_head,
            pr_number=u.ensure_str(params.pr_number),
            pr_title=params.pr_title,
            pr_body=params.pr_body,
            pr_draft=params.pr_draft,
            pr_merge_method=params.pr_merge_method,
            pr_auto=params.pr_auto,
            pr_delete_branch=params.pr_delete_branch,
            pr_checks_strict=params.pr_checks_strict,
            pr_release_on_merge=params.pr_release_on_merge,
        )
        return u.github_pr_orchestrate(
            workspace_root=Path(params.workspace),
            params=m.Infra.PrOrchestrateParams(
                projects=project_names,
                include_root=pr_model.include_root,
                branch=pr_model.branch,
                checkpoint=pr_model.checkpoint,
                fail_fast=pr_model.fail_fast,
                pr_args=pr_model.as_orchestrate_dict(),
            ),
        )
