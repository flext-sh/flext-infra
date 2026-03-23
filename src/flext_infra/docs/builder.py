"""Documentation builder service.

Builds MkDocs sites for workspace projects, returning structured
r reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_core import FlextLogger

from flext_infra import c, m, p, r, u

logger = FlextLogger.create_module_logger(__name__)


class FlextInfraDocBuilder:
    """Infrastructure service for documentation building.

    Runs MkDocs build for workspace projects and returns
    structured r reports.
    """

    def __init__(self) -> None:
        """Initialize the documentation builder."""
        self._runner: p.Infra.CommandRunner = u.Infra()

    @staticmethod
    def _write_reports(
        scope: m.Infra.DocScope,
        report: m.Infra.DocsPhaseReport,
    ) -> None:
        """Persist build JSON summary and markdown report."""
        _ = u.Infra.write_json(
            scope.report_dir / "build-summary.json",
            {c.Infra.ReportKeys.SUMMARY: report.model_dump()},
        )
        _ = u.Infra.write_markdown(
            scope.report_dir / "build-report.md",
            [
                "# Docs Build Report",
                "",
                f"Scope: {report.scope}",
                f"Result: {report.result}",
                f"Reason: {report.reason}",
                f"Site dir: {report.site_dir}",
            ],
        )

    def build(
        self,
        workspace_root: Path,
        *,
        project: str | None = None,
        projects: str | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Build MkDocs sites across project scopes.

        Args:
            workspace_root: Workspace root directory.
            project: Single project name filter.
            projects: Comma-separated project names.
            output_dir: Report output directory.

        Returns:
            r with list of BuildReport objects.

        """
        scopes_result = u.Infra.build_scopes(
            workspace_root=workspace_root,
            project=project,
            projects=projects,
            output_dir=output_dir,
        )
        if scopes_result.is_failure:
            return r[Sequence[m.Infra.DocsPhaseReport]].fail(
                scopes_result.error or "scope error",
            )
        reports: MutableSequence[m.Infra.DocsPhaseReport] = []
        for scope in scopes_result.value:
            report = self._build_scope(scope)
            reports.append(report)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok(reports)

    def _build_scope(
        self,
        scope: m.Infra.DocScope,
    ) -> m.Infra.DocsPhaseReport:
        """Run mkdocs build --strict for a single scope."""
        report = self._run_mkdocs(scope)
        self._write_reports(scope, report)
        logger.info(
            "docs_build_scope_completed",
            project=scope.name,
            phase=c.Infra.Directories.BUILD,
            result=report.result,
            reason=report.reason,
        )
        return report

    def _run_mkdocs(
        self,
        scope: m.Infra.DocScope,
    ) -> m.Infra.DocsPhaseReport:
        """Run mkdocs build --strict and return the result."""
        config = scope.path / "mkdocs.yml"
        if not config.exists():
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result="SKIP",
                reason="mkdocs.yml not found",
                site_dir="",
                passed=True,
            )
        site_dir = (
            scope.path / c.Infra.DEFAULT_DOCS_OUTPUT_DIR / c.Infra.Directories.SITE
        ).resolve()
        site_dir.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "mkdocs",
            c.Infra.Directories.BUILD,
            "--strict",
            "-f",
            str(config),
            "-d",
            str(site_dir),
        ]
        completed = self._runner.run_raw(cmd, cwd=scope.path)
        if completed.is_failure:
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.Status.FAIL,
                reason=completed.error or "mkdocs build failed",
                site_dir=site_dir.as_posix(),
                passed=False,
            )
        output = completed.value
        if output.exit_code == 0:
            return m.Infra.DocsPhaseReport(
                phase="build",
                scope=scope.name,
                result=c.Infra.Status.OK,
                reason="build succeeded",
                site_dir=site_dir.as_posix(),
                passed=True,
            )
        reason = (output.stderr or output.stdout).strip().splitlines()
        tail = reason[-1] if reason else f"mkdocs exited {output.exit_code}"
        return m.Infra.DocsPhaseReport(
            phase="build",
            scope=scope.name,
            result=c.Infra.Status.FAIL,
            reason=tail,
            site_dir=site_dir.as_posix(),
            passed=False,
        )


__all__ = ["FlextInfraDocBuilder"]
