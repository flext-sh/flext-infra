"""Mandatory code-review-graph analysis for ``make mod``."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import c, m, p, r, t, u


class FlextInfraCodeReviewGraphGate:
    """Orchestrate graph-backed impact and refactor analysis."""

    @staticmethod
    def _analyze(project_root: Path, state_dir: Path) -> None:
        u.Infra.code_review_graph_run(
            project_root,
            state_dir,
            (
                c.Infra.CODE_REVIEW_GRAPH,
                "detect-changes",
                "--base",
                c.Infra.GIT_HEAD,
                "--brief",
                "--repo",
                str(project_root),
            ),
        ).unwrap()
        output = u.Infra.code_review_graph_run(
            project_root,
            state_dir,
            (
                c.Infra.CODE_REVIEW_GRAPH,
                "refactor",
                "suggest",
                "--repo",
                str(project_root),
            ),
        ).unwrap()
        report = m.Infra.CodeReviewGraphRefactorReport.model_validate_json(
            output.stdout
        )
        shown = len(report.suggestions)
        if report.total < shown or report.truncated != (report.total > shown):
            raise ValueError("CRG refactor suggestion counts are inconsistent")
        if report.hints.warnings:
            raise RuntimeError("\n".join(report.hints.warnings))

    @classmethod
    def validate(
        cls,
        workspace_root: Path,
        project_groups: t.SequenceOf[tuple[Path, t.SequenceOf[Path]]],
    ) -> p.Result[bool]:
        for index, (project_root, files) in enumerate(project_groups, start=1):
            resolved_project = project_root.resolve()
            sys.stderr.write(
                f"mod: CRG project {index}/{len(project_groups)} "
                f"{resolved_project} files={len(files)}\n"
            )
            sys.stderr.flush()
            state_dir = u.Infra.code_review_graph_synchronize(
                workspace_root.resolve(), resolved_project, files
            )
            cls._analyze(resolved_project, state_dir)
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodeReviewGraphGate"]
