"""Reusable strict code-review-graph execution and synchronization."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from flext_infra import c, m, p, r, t, u


class FlextInfraUtilitiesCodeReviewGraph:
    """Own the external CRG process and per-project graph state lifecycle."""

    @staticmethod
    def code_review_graph_run(
        project_root: Path,
        state_dir: Path,
        command: t.StrSequence,
        *,
        stdout_pattern: str | None = None,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run one documented CRG command with authenticated output."""
        state_dir.mkdir(parents=True, exist_ok=True)
        sys.stderr.write(f"mod: start {' '.join(command)}\n")
        sys.stderr.flush()
        run = u.Cli.run_raw(
            command,
            cwd=project_root,
            timeout=c.Infra.CODE_REVIEW_GRAPH_TIMEOUT_SECONDS,
            env={
                c.Infra.CRG_DATA_DIR: str(state_dir),
                c.Infra.CRG_HOME: str(state_dir),
            },
        )
        if run.failure:
            sys.stderr.write(f"mod: finish {command[0]} failure\n")
            sys.stderr.flush()
            return r[p.Cli.CommandOutput].from_failure(run)
        output = run.value
        sys.stderr.write(
            f"mod: finish {command[0]} exit={output.exit_code} "
            f"duration={output.duration:.2f}s\n"
        )
        sys.stderr.flush()
        if output.exit_code != 0:
            detail = "\n".join(
                value.strip()
                for value in (output.stdout, output.stderr)
                if value.strip()
            )
            return r[p.Cli.CommandOutput].fail(
                f"{command[0]} exited with code {output.exit_code}: {detail}"
            )
        stdout = output.stdout.strip()
        if not stdout:
            return r[p.Cli.CommandOutput].fail(f"{command[0]} produced empty stdout")
        if re.search(r"(?im)^(?:WARNING|ERROR|CRITICAL|Traceback)\b", stdout):
            return r[p.Cli.CommandOutput].fail(stdout)
        if stdout_pattern and re.fullmatch(stdout_pattern, stdout) is None:
            return r[p.Cli.CommandOutput].fail(
                f"unexpected {command[0]} stdout: {stdout}"
            )
        stderr = output.stderr.strip()
        if stderr:
            if any(
                not any(
                    re.fullmatch(pattern, line)
                    for pattern in c.Infra.CODE_REVIEW_GRAPH_INFO_LINE_PATTERNS
                )
                for line in stderr.splitlines()
            ):
                return r[p.Cli.CommandOutput].fail(stderr)
            sys.stderr.write(f"{stderr}\n")
            sys.stderr.flush()
        return r[p.Cli.CommandOutput].ok(output)

    @classmethod
    def _code_review_graph_status(
        cls, project_root: Path, state_dir: Path
    ) -> m.Infra.CodeReviewGraphStatusReport:
        output = cls.code_review_graph_run(
            project_root,
            state_dir,
            (
                c.Infra.CODE_REVIEW_GRAPH,
                "status",
                "--json",
                "--repo",
                str(project_root),
            ),
        ).unwrap()
        return m.Infra.CodeReviewGraphStatusReport.model_validate_json(output.stdout)

    @staticmethod
    def _code_review_graph_require_tracked(
        project_root: Path, files: t.SequenceOf[Path]
    ) -> None:
        for path in files:
            resolved = path.resolve()
            if not resolved.is_relative_to(project_root):
                raise ValueError(f"CRG input escapes project: {resolved}")
            tracked = u.Infra.git_is_tracked(
                m.Infra.GitRelativePathRequest(
                    repo_root=project_root,
                    relative_path=resolved.relative_to(project_root).as_posix(),
                )
            ).unwrap()
            if not tracked.value:
                raise ValueError(
                    f"CRG 2.3.8 cannot index affected untracked file: {resolved}"
                )

    @staticmethod
    def _code_review_graph_git_identity(project_root: Path) -> tuple[str, str]:
        request = m.Infra.GitRepoRequest(repo_root=project_root)
        branch = u.Infra.git_current_branch(request).unwrap().text.strip()
        head = u.Infra.git_resolve_commit(
            m.Infra.GitCommitishRequest(
                repo_root=project_root, commitish=c.Infra.GIT_HEAD
            )
        ).unwrap().oid
        if not branch:
            raise ValueError(f"CRG requires a Git branch: {project_root}")
        return branch, head

    @staticmethod
    def _code_review_graph_require_current(
        report: m.Infra.CodeReviewGraphStatusReport, branch: str, head: str
    ) -> None:
        if report.files <= 0 or report.nodes <= 0 or not report.languages:
            raise ValueError("CRG status reports an empty graph")
        if report.current_branch != branch or report.current_sha != head:
            raise ValueError("CRG current Git identity disagrees with u.Infra")
        if report.built_on_branch != branch or report.built_at_commit != head:
            raise ValueError("CRG graph is not synchronized to current HEAD")

    @classmethod
    def code_review_graph_synchronize(
        cls, workspace_root: Path, project_root: Path, files: t.SequenceOf[Path]
    ) -> Path:
        """Build or update one affected project's canonical external graph."""
        cls._code_review_graph_require_tracked(project_root, files)
        branch, head = cls._code_review_graph_git_identity(project_root)
        state_dir = u.Infra.external_tool_state_dir(
            workspace_root, project_root, c.Infra.CODE_REVIEW_GRAPH
        )
        full_build = not (
            state_dir / c.Infra.CODE_REVIEW_GRAPH_DATABASE_FILENAME
        ).is_file()
        base = head
        if not full_build:
            status = cls._code_review_graph_status(project_root, state_dir)
            base = status.built_at_commit or head
            full_build = (
                status.built_on_branch != branch or status.built_at_commit is None
            )
            if not full_build:
                full_build = not u.Infra.git_is_ancestor(
                    m.Infra.GitCommitishRequest(
                        repo_root=project_root, commitish=base
                    )
                ).unwrap().value
        command = (
            (c.Infra.CODE_REVIEW_GRAPH, "build", "--repo", str(project_root))
            if full_build
            else (
                c.Infra.CODE_REVIEW_GRAPH,
                "update",
                "--base",
                base,
                "--repo",
                str(project_root),
            )
        )
        receipt = (
            r"Full build: \d+ files, \d+ nodes, \d+ edges \(postprocess=full\)"
            if full_build
            else r"Incremental: \d+ files updated, \d+ nodes, \d+ edges \(postprocess=full\)"
        )
        cls.code_review_graph_run(
            project_root, state_dir, command, stdout_pattern=receipt
        ).unwrap()
        cls._code_review_graph_require_current(
            cls._code_review_graph_status(project_root, state_dir), branch, head
        )
        return state_dir


__all__: list[str] = ["FlextInfraUtilitiesCodeReviewGraph"]
