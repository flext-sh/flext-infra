"""Apply orchestration for the project-layout engine.

Executes the typed findings produced by the planning mixin, composing the
file/retirement primitives and the gitignore owner through FLEXT.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import p, r, t, u
from flext_infra.codegen._layout import (
    FlextInfraCodegenLayoutFiles,
    FlextInfraCodegenLayoutGitignore,
)


class FlextInfraCodegenLayoutApply(
    FlextInfraCodegenLayoutFiles,
    FlextInfraCodegenLayoutGitignore,
):
    """Execute layout findings idempotently against one project directory."""

    def apply_project(
        self,
        project_dir: Path,
        report: p.Infra.LayoutProjectReport,
    ) -> p.Result[p.Infra.LayoutProjectReport]:
        """Execute every planned finding and return the updated report.

        Returns:
            The resulting ``p.Result[p.Infra.LayoutProjectReport]``.

        """
        if report.actionable and not report.inputs:
            return r[p.Infra.LayoutProjectReport].fail(
                "layout apply requires captured configuration inputs",
            )
        with u.Infra.state_leases((project_dir,)):
            verified = u.Cli.atomic_verify_binary_file_states(report.inputs)
            if verified.failure:
                return r[p.Infra.LayoutProjectReport].from_failure(verified)
            return self._apply_findings(project_dir, report)

    def _apply_findings(
        self,
        project_dir: Path,
        report: p.Infra.LayoutProjectReport,
    ) -> p.Result[p.Infra.LayoutProjectReport]:
        """Apply one authenticated plan while holding the native writer lease.

        Returns:
            The updated report or the first original failure.

        """
        findings: list[p.Infra.LayoutFinding] = []
        gitignore_status: t.Infra.LayoutStatus = "noop"
        actionable: tuple[p.Infra.LayoutFinding, ...] = report.actionable
        gitignore_patterns = tuple(
            finding.target for finding in actionable if finding.rule == "gitignore"
        )
        if gitignore_patterns:
            applied = self._apply_gitignore(project_dir, gitignore_patterns)
            if applied.failure:
                return r[p.Infra.LayoutProjectReport].from_failure(applied)
            gitignore_status = applied.value
        for finding in report.findings:
            if finding.rule == "review":
                findings.append(finding)
                continue
            if finding.rule == "gitignore":
                findings.append(finding.model_copy(update={"status": gitignore_status}))
                continue
            executed = self._execute_path_finding(project_dir, finding, report.inputs)
            if executed.failure:
                return r[p.Infra.LayoutProjectReport].from_failure(executed)
            findings.append(executed.value)
        return r[p.Infra.LayoutProjectReport].ok(
            report.model_copy(update={"findings": tuple(findings)}),
        )

    def _execute_path_finding(
        self,
        project_dir: Path,
        finding: p.Infra.LayoutFinding,
        inputs: Sequence[p.Cli.AtomicFileState],
    ) -> p.Result[p.Infra.LayoutFinding]:
        """Execute one path finding; missing sources are no-ops.

        Returns:
            The resulting ``p.Result[p.Infra.LayoutFinding]``.

        """
        source = project_dir / finding.path
        if not source.exists() and not source.is_symlink():
            return r[p.Infra.LayoutFinding].ok(
                finding.model_copy(update={"status": "noop"}),
            )
        if finding.rule == "move":
            return self._apply_move(project_dir, finding, source, inputs)
        if finding.rule == "prune":
            pruned = self._prune_empty_dirs(source)
            if pruned.failure:
                return r[p.Infra.LayoutFinding].from_failure(pruned)
            return r[p.Infra.LayoutFinding].ok(
                finding.model_copy(update={"status": "applied"}),
            )
        return self._apply_retire(project_dir, finding, source, inputs)

    def _apply_move(
        self,
        project_dir: Path,
        finding: p.Infra.LayoutFinding,
        source: Path,
        inputs: Sequence[p.Cli.AtomicFileState],
    ) -> p.Result[p.Infra.LayoutFinding]:
        """Move one file/dir to its canonical target, merging dir collisions.

        Returns:
            The resulting ``p.Result[p.Infra.LayoutFinding]``.

        """
        target = project_dir / finding.target
        if source.is_dir() and not source.is_symlink() and target.exists():
            if not target.is_dir() or target.is_symlink():
                return r[p.Infra.LayoutFinding].fail(
                    f"layout collision preserves divergent paths: {source} -> {target}",
                )
            merge = self._merge_directory(project_dir, source, target, inputs)
            if merge.failure:
                return r[p.Infra.LayoutFinding].from_failure(merge)
            if source.exists():
                return r[p.Infra.LayoutFinding].fail(
                    f"layout merge left preserved source content: {source}",
                )
            return r[p.Infra.LayoutFinding].ok(
                finding.model_copy(update={"status": "applied"}),
            )
        moved = self._move_entry(project_dir, source, target, inputs)
        if moved.failure:
            return r[p.Infra.LayoutFinding].from_failure(moved)
        status, message = moved.value
        return r[p.Infra.LayoutFinding].ok(
            finding.model_copy(update={"status": status, "message": message}),
        )

    def _apply_retire(
        self,
        project_dir: Path,
        finding: p.Infra.LayoutFinding,
        source: Path,
        inputs: Sequence[p.Cli.AtomicFileState],
    ) -> p.Result[p.Infra.LayoutFinding]:
        """Retire one entry only after proving its content is preserved in Git.

        Returns:
            The resulting ``p.Result[p.Infra.LayoutFinding]``.

        """
        retired = self._retire_path(project_dir, source, inputs)
        if retired.failure:
            return r[p.Infra.LayoutFinding].from_failure(retired)
        status, message = retired.value
        return r[p.Infra.LayoutFinding].ok(
            finding.model_copy(update={"status": status, "message": message}),
        )

    def _merge_directory(
        self,
        project_dir: Path,
        source: Path,
        target: Path,
        inputs: Sequence[p.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Merge a docs dir into an existing target dir file-by-file.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        files = sorted(path for path in source.rglob("*") if path.is_file())
        for file_path in files:
            rel = file_path.relative_to(source).as_posix()
            moved = self._move_entry(
                project_dir,
                file_path,
                target / rel,
                inputs,
            )
            if moved.failure:
                return r[bool].from_failure(moved)
        return self._prune_empty_dirs(source)


__all__: list[str] = ["FlextInfraCodegenLayoutApply"]
