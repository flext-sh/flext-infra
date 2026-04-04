"""GitHub integration utility functions and automation helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGithubPr,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
    FlextInfraUtilitiesTemplates,
    c,
    m,
    t,
)


class FlextInfraUtilitiesGithub(
    FlextInfraUtilitiesGithubPr,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
    FlextInfraUtilitiesTemplates,
):
    """Utilities for GitHub automation including PRs and Workflows."""

    @classmethod
    def github_lint_workflows(
        cls,
        workspace_root: Path,
        *,
        report_path: Path | None = None,
        strict: bool = False,
    ) -> r[m.Infra.WorkflowLintResult]:
        """Run actionlint on the repository and return results."""
        actionlint = shutil.which("actionlint")
        if actionlint is None:
            payload_skipped = m.Infra.WorkflowLintResult(
                status="skipped",
                reason="actionlint not installed",
            )
            if report_path is not None:
                cls.write_json(report_path, payload_skipped, sort_keys=True)
            return r[m.Infra.WorkflowLintResult].ok(payload_skipped)
        result = cls.run_raw([actionlint], cwd=workspace_root)
        if result.is_success:
            output = result.value
            payload = m.Infra.WorkflowLintResult(
                status="ok",
                exit_code=output.exit_code,
                stdout=output.stdout,
                stderr=output.stderr,
            )
        else:
            payload = m.Infra.WorkflowLintResult(
                status="fail",
                exit_code=1,
                detail=result.error or "",
            )
        if report_path is not None:
            cls.write_json(report_path, payload, sort_keys=True)
        if payload.status == "fail" and strict:
            return r[m.Infra.WorkflowLintResult].fail(
                result.error or "actionlint found issues",
            )
        return r[m.Infra.WorkflowLintResult].ok(payload)

    @classmethod
    def github_sync_workspace_workflows(
        cls,
        workspace_root: Path,
        params: m.Infra.WorkflowSyncParams,
    ) -> r[Sequence[m.Infra.SyncOperation]]:
        """Sync workflows across all workspace projects."""
        source_result = cls._github_resolve_source_workflow(
            workspace_root,
            params.source_workflow,
        )
        if source_result.is_failure:
            return r[Sequence[m.Infra.SyncOperation]].fail(
                source_result.error or "source resolution failed",
            )
        template_result = cls._github_render_template(source_result.value)
        if template_result.is_failure:
            return r[Sequence[m.Infra.SyncOperation]].fail(
                template_result.error or "template render failed",
            )
        projects_result = cls.resolve_projects(workspace_root, [])
        if projects_result.is_failure:
            return r[Sequence[m.Infra.SyncOperation]].fail(
                projects_result.error or "project discovery failed",
            )
        all_operations: MutableSequence[m.Infra.SyncOperation] = []
        for project in projects_result.value:
            ctx = m.Infra.GithubSyncContext(
                project_name=project.name,
                project_root=project.path,
                rendered_template=template_result.value,
                apply=params.apply,
                prune=params.prune,
            )
            ops_result = cls._github_sync_project(ctx)
            if ops_result.is_success:
                all_operations.extend(ops_result.value)
        if params.report_path is not None:
            cls._github_write_report(
                params.report_path,
                apply=params.apply,
                operations=all_operations,
            )
        return r[Sequence[m.Infra.SyncOperation]].ok(all_operations)

    @classmethod
    def _github_render_template(cls, template_path: Path) -> r[str]:
        try:
            body = template_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError as exc:
            return r[str].fail(f"failed to read template: {exc}")
        header_template = cls.GENERATED_SHELL_HEADER
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
        ctx: m.Infra.GithubSyncContext,
    ) -> r[Sequence[m.Infra.SyncOperation]]:
        operations: MutableSequence[m.Infra.SyncOperation] = []
        try:
            cls._github_sync_ci_yml(ctx, operations)
            if ctx.prune and ctx.workflows_dir.exists():
                cls._github_prune_workflows(ctx, operations)
        except OSError as exc:
            return r[Sequence[m.Infra.SyncOperation]].fail(f"sync error: {exc}")
        return r[Sequence[m.Infra.SyncOperation]].ok(operations)

    @classmethod
    def _github_sync_ci_yml(
        cls,
        ctx: m.Infra.GithubSyncContext,
        operations: MutableSequence[m.Infra.SyncOperation],
    ) -> None:
        """Sync a single ci.yml file for a project."""
        destination = ctx.ci_destination
        rel_path = str(destination.relative_to(ctx.project_root))
        if destination.exists():
            current = destination.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if current != ctx.rendered_template:
                if ctx.apply:
                    _ = destination.write_text(
                        ctx.rendered_template,
                        encoding=c.Infra.Encoding.DEFAULT,
                    )
                operations.append(
                    m.Infra.SyncOperation(
                        project=ctx.project_name,
                        path=rel_path,
                        action="update",
                        reason="force overwrite ci.yml",
                    ),
                )
            else:
                operations.append(
                    m.Infra.SyncOperation(
                        project=ctx.project_name,
                        path=rel_path,
                        action="noop",
                        reason="already synced",
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
                m.Infra.SyncOperation(
                    project=ctx.project_name,
                    path=rel_path,
                    action="create",
                    reason="missing ci.yml",
                ),
            )

    @staticmethod
    def _github_prune_workflows(
        ctx: m.Infra.GithubSyncContext,
        operations: MutableSequence[m.Infra.SyncOperation],
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
                m.Infra.SyncOperation(
                    project=ctx.project_name,
                    path=str(path.relative_to(ctx.project_root)),
                    action="prune",
                    reason="remove non-canonical workflow",
                ),
            )

    @classmethod
    def _github_write_report(
        cls,
        report_path: Path,
        *,
        apply: bool,
        operations: Sequence[m.Infra.SyncOperation],
    ) -> None:
        by_action: t.MutableIntMapping = {}
        for op in operations:
            by_action[op.action] = by_action.get(op.action, 0) + 1
        summary_dict: MutableMapping[str, t.Cli.JsonValue] = dict(by_action)
        ops_list: list[t.Cli.JsonValue] = [
            {
                c.Infra.PROJECT: op.project,
                c.Infra.PATH: op.path,
                c.Infra.ReportKeys.ACTION: op.action,
                "reason": op.reason,
            }
            for op in operations
        ]
        payload: MutableMapping[str, t.Cli.JsonValue] = {
            "mode": "apply" if apply else "dry-run",
            c.Infra.ReportKeys.SUMMARY: summary_dict,
            "operations": ops_list,
        }
        cls.write_json(report_path, payload, sort_keys=True)
