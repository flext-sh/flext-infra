"""GitHub integration utility functions and automation helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGithubPr,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
    c,
    m,
    r,
)


class FlextInfraUtilitiesGithub(
    FlextInfraUtilitiesGithubPr,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
):
    """Utilities for GitHub automation including PRs and Workflows."""

    @classmethod
    def github_lint_workflows(
        cls,
        request: m.Infra.GithubWorkflowLintRequest,
    ) -> r[m.Infra.GithubWorkflowLintOutcome]:
        """Run actionlint on the repository and return results."""
        actionlint = shutil.which("actionlint")
        workspace_root = request.workspace_path
        if actionlint is None:
            payload_skipped = m.Infra.GithubWorkflowLintOutcome(
                status="skipped",
                reason="actionlint not installed",
            )
            if request.report_path is not None:
                _ = u.Cli.json_write(
                    request.report_path,
                    payload_skipped,
                    sort_keys=True,
                )
            return r[m.Infra.GithubWorkflowLintOutcome].ok(
                payload_skipped,
            )
        result = u.Cli.run_raw([actionlint], cwd=workspace_root)
        if result.is_success:
            output = result.value
            payload = m.Infra.GithubWorkflowLintOutcome(
                status="ok",
                exit_code=output.exit_code,
                stdout=output.stdout,
                stderr=output.stderr,
            )
        else:
            payload = m.Infra.GithubWorkflowLintOutcome(
                status="fail",
                exit_code=1,
                detail=result.error or "",
            )
        if request.report_path is not None:
            _ = u.Cli.json_write(request.report_path, payload, sort_keys=True)
        if payload.status == "fail" and request.strict:
            return r[m.Infra.GithubWorkflowLintOutcome].fail(
                result.error or "actionlint found issues",
            )
        return r[m.Infra.GithubWorkflowLintOutcome].ok(payload)

    @classmethod
    def github_sync_workflows(
        cls,
        request: m.Infra.GithubWorkflowSyncRequest,
    ) -> r[m.Infra.GithubWorkflowSyncReport]:
        """Sync workflows across all workspace projects."""
        workspace_root = request.workspace_path
        source_result = cls._github_resolve_source_workflow(
            workspace_root,
            None,
        )
        if source_result.is_failure:
            return r[m.Infra.GithubWorkflowSyncReport].fail(
                source_result.error or "source resolution failed",
            )
        template_result = cls._github_render_template(source_result.value)
        if template_result.is_failure:
            return r[m.Infra.GithubWorkflowSyncReport].fail(
                template_result.error or "template render failed",
            )
        projects_result = cls.resolve_projects(workspace_root, [])
        if projects_result.is_failure:
            return r[m.Infra.GithubWorkflowSyncReport].fail(
                projects_result.error or "project discovery failed",
            )
        all_operations: MutableSequence[m.Infra.GithubWorkflowSyncOperation] = []
        for project in projects_result.value:
            ctx = m.Infra.GithubWorkflowSyncContext(
                project_name=project.name,
                project_root=project.path,
                rendered_template=template_result.value,
                request=request,
            )
            ops_result = cls._github_sync_project(ctx)
            if ops_result.is_success:
                all_operations.extend(ops_result.value)
        report = m.Infra.GithubWorkflowSyncReport.from_operations(
            apply=request.apply,
            operations=all_operations,
        )
        if request.report_path is not None:
            _ = u.Cli.json_write(request.report_path, report, sort_keys=True)
        return r[m.Infra.GithubWorkflowSyncReport].ok(report)

    @classmethod
    def _github_render_template(cls, template_path: Path) -> r[str]:
        try:
            body = template_path.read_text(
                encoding=c.Infra.Encoding.DEFAULT,
            )
        except OSError as exc:
            return r[str].fail(f"failed to read template: {exc}")
        header_template = c.Infra.SourceCode.GENERATED_SHELL_HEADER
        header = header_template.format(source="flext_infra.github.workflows")
        if body.startswith(header):
            return r[str].ok(body)
        return r[str].ok(header + body)

    @classmethod
    def _github_resolve_source_workflow(
        cls,
        workspace_root: Path,
        source_workflow: Path | None = None,
    ) -> r[Path]:
        if source_workflow is not None:
            candidate = (
                source_workflow
                if source_workflow.is_absolute()
                else workspace_root / source_workflow
            ).resolve()
            if candidate.exists():
                return r[Path].ok(candidate)
            return r[Path].fail(f"missing source workflow: {candidate}")
        default_source = (workspace_root / ".github" / "workflows" / "ci.yml").resolve()
        if default_source.exists():
            return r[Path].ok(default_source)
        return r[Path].fail(f"missing source workflow: {default_source}")

    @classmethod
    def _github_sync_project(
        cls,
        ctx: m.Infra.GithubWorkflowSyncContext,
    ) -> r[Sequence[m.Infra.GithubWorkflowSyncOperation]]:
        operations: MutableSequence[m.Infra.GithubWorkflowSyncOperation] = []
        try:
            cls._github_sync_ci_yml(ctx, operations)
            if ctx.prune and ctx.workflows_dir.exists():
                cls._github_prune_workflows(ctx, operations)
        except OSError as exc:
            return r[Sequence[m.Infra.GithubWorkflowSyncOperation]].fail(
                f"sync error: {exc}",
            )
        return r[Sequence[m.Infra.GithubWorkflowSyncOperation]].ok(
            operations,
        )

    @classmethod
    def _github_sync_ci_yml(
        cls,
        ctx: m.Infra.GithubWorkflowSyncContext,
        operations: MutableSequence[m.Infra.GithubWorkflowSyncOperation],
    ) -> None:
        """Sync a single ci.yml file for a project."""
        destination = ctx.ci_destination
        rel_path = str(destination.relative_to(ctx.project_root))
        if destination.exists():
            current = destination.read_text(
                encoding=c.Infra.Encoding.DEFAULT,
            )
            if current != ctx.rendered_template:
                if ctx.apply:
                    _ = destination.write_text(
                        ctx.rendered_template,
                        encoding=c.Infra.Encoding.DEFAULT,
                    )
                operations.append(
                    m.Infra.GithubWorkflowSyncOperation.model_validate(
                        {
                            "project": ctx.project_name,
                            "path": rel_path,
                            "action": "update",
                            "reason": "force overwrite ci.yml",
                        },
                    ),
                )
            else:
                operations.append(
                    m.Infra.GithubWorkflowSyncOperation.model_validate(
                        {
                            "project": ctx.project_name,
                            "path": rel_path,
                            "action": "noop",
                            "reason": "already synced",
                        },
                    ),
                )
        else:
            if ctx.apply:
                ctx.workflows_dir.mkdir(parents=True, exist_ok=True)
                _ = destination.write_text(
                    ctx.rendered_template,
                    encoding=c.Infra.Encoding.DEFAULT,
                )
            operations.append(
                m.Infra.GithubWorkflowSyncOperation.model_validate(
                    {
                        "project": ctx.project_name,
                        "path": rel_path,
                        "action": "create",
                        "reason": "missing ci.yml",
                    },
                ),
            )

    @staticmethod
    def _github_prune_workflows(
        ctx: m.Infra.GithubWorkflowSyncContext,
        operations: MutableSequence[m.Infra.GithubWorkflowSyncOperation],
    ) -> None:
        """Remove non-canonical workflow files from a project."""
        candidates = sorted(ctx.workflows_dir.glob("*.yml")) + sorted(
            ctx.workflows_dir.glob("*.yaml"),
        )
        for path in candidates:
            if path.name in c.Infra.MANAGED_FILES:
                continue
            if ctx.apply:
                path.unlink()
            operations.append(
                m.Infra.GithubWorkflowSyncOperation.model_validate(
                    {
                        "project": ctx.project_name,
                        "path": str(path.relative_to(ctx.project_root)),
                        "action": "prune",
                        "reason": "remove non-canonical workflow",
                    },
                ),
            )
