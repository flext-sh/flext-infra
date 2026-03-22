"""GitHub integration utility functions and automation helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
import shutil
import time
from collections.abc import Mapping, MutableMapping
from pathlib import Path

from pydantic import JsonValue

from flext_core import r
from flext_infra import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
    FlextInfraUtilitiesTemplates,
    c,
    m,
)


class FlextInfraUtilitiesGithub(
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
        root: Path,
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
        result = cls.run_raw([actionlint], cwd=root)
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
        *,
        source_workflow: Path | None = None,
        report_path: Path | None = None,
        apply: bool = False,
        prune: bool = False,
    ) -> r[list[m.Infra.SyncOperation]]:
        """Sync workflows across all workspace projects."""
        source_result = cls._github_resolve_source_workflow(
            workspace_root,
            source_workflow,
        )
        if source_result.is_failure:
            return r[list[m.Infra.SyncOperation]].fail(
                source_result.error or "source resolution failed",
            )
        template_result = cls._github_render_template(source_result.value)
        if template_result.is_failure:
            return r[list[m.Infra.SyncOperation]].fail(
                template_result.error or "template render failed",
            )
        projects_result = cls.resolve_projects(workspace_root, [])
        if projects_result.is_failure:
            return r[list[m.Infra.SyncOperation]].fail(
                projects_result.error or "project discovery failed",
            )
        all_operations: list[m.Infra.SyncOperation] = []
        for project in projects_result.value:
            ops_result = cls._github_sync_project(
                project_name=project.name,
                project_root=project.path,
                rendered_template=template_result.value,
                apply=apply,
                prune=prune,
            )
            if ops_result.is_success:
                all_operations.extend(ops_result.value)
        if report_path is not None:
            cls._github_write_report(
                report_path, apply=apply, operations=all_operations
            )
        return r[list[m.Infra.SyncOperation]].ok(all_operations)

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
        *,
        project_name: str,
        project_root: Path,
        rendered_template: str,
        apply: bool = False,
        prune: bool = False,
    ) -> r[list[m.Infra.SyncOperation]]:
        operations: list[m.Infra.SyncOperation] = []
        workflows_dir = project_root / ".github" / "workflows"
        destination = workflows_dir / "ci.yml"
        try:
            if destination.exists():
                current = destination.read_text(encoding=c.Infra.Encoding.DEFAULT)
                if current != rendered_template:
                    if apply:
                        _ = destination.write_text(
                            rendered_template,
                            encoding=c.Infra.Encoding.DEFAULT,
                        )
                    operations.append(
                        m.Infra.SyncOperation(
                            project=project_name,
                            path=str(destination.relative_to(project_root)),
                            action="update",
                            reason="force overwrite ci.yml",
                        ),
                    )
                else:
                    operations.append(
                        m.Infra.SyncOperation(
                            project=project_name,
                            path=str(destination.relative_to(project_root)),
                            action="noop",
                            reason="already synced",
                        ),
                    )
            else:
                if apply:
                    workflows_dir.mkdir(parents=True, exist_ok=True)
                    _ = destination.write_text(
                        rendered_template,
                        encoding=c.Infra.Encoding.DEFAULT,
                    )
                operations.append(
                    m.Infra.SyncOperation(
                        project=project_name,
                        path=str(destination.relative_to(project_root)),
                        action="create",
                        reason="missing ci.yml",
                    ),
                )
            if prune and workflows_dir.exists():
                candidates = sorted(workflows_dir.glob("*.yml")) + sorted(
                    workflows_dir.glob("*.yaml"),
                )
                for path in candidates:
                    if path.name in c.Infra.MANAGED_FILES:
                        continue
                    if apply:
                        path.unlink()
                    operations.append(
                        m.Infra.SyncOperation(
                            project=project_name,
                            path=str(path.relative_to(project_root)),
                            action="prune",
                            reason="remove non-canonical workflow",
                        ),
                    )
        except OSError as exc:
            return r[list[m.Infra.SyncOperation]].fail(f"sync error: {exc}")
        return r[list[m.Infra.SyncOperation]].ok(operations)

    @classmethod
    def _github_write_report(
        cls,
        report_path: Path,
        *,
        apply: bool,
        operations: list[m.Infra.SyncOperation],
    ) -> None:
        by_action: MutableMapping[str, int] = {}
        for op in operations:
            by_action[op.action] = by_action.get(op.action, 0) + 1
        summary_dict: dict[str, JsonValue] = dict(by_action)
        ops_list: list[JsonValue] = [
            {
                c.Infra.Toml.PROJECT: op.project,
                c.Infra.Toml.PATH: op.path,
                c.Infra.ReportKeys.ACTION: op.action,
                "reason": op.reason,
            }
            for op in operations
        ]
        payload: JsonValue = {
            "mode": "apply" if apply else "dry-run",
            c.Infra.ReportKeys.SUMMARY: summary_dict,
            "operations": ops_list,
        }
        cls.write_json(report_path, payload, sort_keys=True)

    @classmethod
    def github_pr_orchestrate(
        cls,
        workspace_root: Path,
        *,
        projects: list[str] | None = None,
        include_root: bool = True,
        branch: str = "",
        checkpoint: bool = True,
        fail_fast: bool = False,
        pr_args: Mapping[str, str] | None = None,
    ) -> r[m.Infra.PrOrchestrationResult]:
        """Run PR operations across workspace repositories."""
        projects_result = cls.resolve_projects(workspace_root, projects or [])
        if projects_result.is_failure:
            return r[m.Infra.PrOrchestrationResult].fail(
                projects_result.error or "project resolution failed",
            )
        repos = [p.path for p in projects_result.value]
        if include_root:
            repos.append(workspace_root)
        effective_args = pr_args or {
            c.Infra.ReportKeys.ACTION: c.Infra.ReportKeys.STATUS,
            "base": c.Infra.Git.MAIN,
        }
        failures = 0
        results: list[m.Infra.PrExecutionResultModel] = []
        for repo_root in repos:
            if branch:
                cls.git_checkout(repo_root, branch)
            if checkpoint:
                cls._github_pr_checkpoint(repo_root, branch)
            run_result: r[m.Infra.PrExecutionResultModel] = cls._github_pr_run_single(
                repo_root,
                workspace_root,
                effective_args,
            )
            if run_result.is_success:
                pr_data = run_result.value
                results.append(pr_data)
                if pr_data.exit_code != 0:
                    failures += 1
                    if fail_fast:
                        break
            else:
                failures += 1
                if fail_fast:
                    break
        total = len(repos)
        orchestration_results: tuple[m.Infra.PrExecutionResultModel, ...] = tuple(
            results
        )
        return r[m.Infra.PrOrchestrationResult].ok(
            m.Infra.PrOrchestrationResult(
                total=total,
                success=total - failures,
                fail=failures,
                results=orchestration_results,
            ),
        )

    @classmethod
    def _github_pr_checkpoint(cls, repo_root: Path, branch: str) -> r[bool]:
        changes_result = cls.git_has_changes(repo_root)
        if changes_result.is_failure:
            return r[bool].fail(changes_result.error or "changes check failed")
        if not changes_result.value:
            return r[bool].ok(True)
        add_result = cls.git_add(repo_root)
        if add_result.is_failure:
            return r[bool].fail(add_result.error or "git add failed")
        staged_result = cls.git_diff_names(repo_root, cached=True)
        if staged_result.is_success and (not staged_result.value.strip()):
            return r[bool].ok(True)
        commit_result = cls.git_commit(
            repo_root,
            "chore: checkpoint pending changes",
        )
        if commit_result.is_failure:
            return r[bool].fail(commit_result.error or "git commit failed")
        return cls.git_push(
            repo_root,
            remote=c.Infra.Git.ORIGIN if branch else "",
            branch=branch,
            upstream=bool(branch),
        )

    @classmethod
    def github_pr_run_single(
        cls,
        repo_root: Path,
        workspace_root: Path,
        pr_args: Mapping[str, str],
    ) -> r[m.Infra.PrExecutionResultModel]:
        """Execute one PR command for a single repository."""
        return cls._github_pr_run_single(
            repo_root=repo_root,
            workspace_root=workspace_root,
            pr_args=pr_args,
        )

    @classmethod
    def _github_pr_run_single(
        cls,
        repo_root: Path,
        workspace_root: Path,
        pr_args: Mapping[str, str],
    ) -> r[m.Infra.PrExecutionResultModel]:
        display = workspace_root.name if repo_root == workspace_root else repo_root.name
        report_dir = cls.get_report_dir(
            workspace_root,
            c.Infra.ReportKeys.WORKSPACE,
            c.Infra.Cli.GhCmd.PR,
        )
        with contextlib.suppress(OSError):
            report_dir.mkdir(parents=True, exist_ok=True)
        log_path = report_dir / f"{display}.log"
        if repo_root == workspace_root:
            command = [
                c.Infra.Toml.PYTHON,
                "-m",
                "flext_infra.github.pr",
                "--repo-root",
                str(repo_root),
                "--action",
                pr_args.get(c.Infra.ReportKeys.ACTION, c.Infra.ReportKeys.STATUS),
                "--base",
                pr_args.get("base", c.Infra.Git.MAIN),
                "--draft",
                pr_args.get("draft", "0"),
                "--merge-method",
                pr_args.get("merge_method", c.Infra.Cli.GhCmd.SQUASH),
                "--auto",
                pr_args.get("auto", "0"),
                "--delete-branch",
                pr_args.get("delete_branch", "0"),
                "--checks-strict",
                pr_args.get("checks_strict", "0"),
                "--release-on-merge",
                pr_args.get("release_on_merge", "1"),
            ]
        else:
            command = [
                c.Infra.Cli.MAKE,
                "-C",
                str(repo_root),
                c.Infra.Cli.GhCmd.PR,
                f"PR_ACTION={pr_args.get('action', 'status')}",
                f"PR_BASE={pr_args.get('base', 'main')}",
                f"PR_DRAFT={pr_args.get('draft', '0')}",
                f"PR_MERGE_METHOD={pr_args.get('merge_method', 'squash')}",
                f"PR_AUTO={pr_args.get('auto', '0')}",
                f"PR_DELETE_BRANCH={pr_args.get('delete_branch', '0')}",
                f"PR_CHECKS_STRICT={pr_args.get('checks_strict', '0')}",
                f"PR_RELEASE_ON_MERGE={pr_args.get('release_on_merge', '1')}",
            ]
        for key, flag in (
            ("head", "PR_HEAD"),
            ("number", "PR_NUMBER"),
            ("title", "PR_TITLE"),
            ("body", "PR_BODY"),
        ):
            value = pr_args.get(key, "")
            if value:
                if repo_root == workspace_root:
                    command.extend([f"--{key}", value])
                else:
                    command.append(f"{flag}={value}")
        started = time.monotonic()
        to_file_result: r[int] = cls.run_to_file(command, log_path)
        if to_file_result.is_failure:
            return r[m.Infra.PrExecutionResultModel].fail(
                to_file_result.error or "command execution error",
            )
        exit_code = to_file_result.value
        elapsed = int(time.monotonic() - started)
        status = c.Infra.Status.OK if exit_code == 0 else c.Infra.Status.FAIL
        return r[m.Infra.PrExecutionResultModel].ok(
            m.Infra.PrExecutionResultModel(
                display=display,
                status=status,
                elapsed=elapsed,
                exit_code=exit_code,
                log_path=str(log_path),
            ),
        )
