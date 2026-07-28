"""Native GitHub pull-request publication through the FLEXT process facade."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r
from flext_infra import c, m

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraUtilitiesGithubPrExecutionMixin:
    """Execute the minimal, native pull-request publication contract."""

    @staticmethod
    def _github_pr_list_command(
        request: m.Infra.GithubPullRequestRequest, head: str, *, url_only: bool
    ) -> list[str]:
        """Build the native idempotence/status query."""
        command = [
            c.Infra.GH,
            c.Infra.PR,
            "list",
            "--state",
            "open",
            "--head",
            head,
            "--json",
            "url" if url_only else c.Infra.PULL_REQUEST_JSON_FIELDS,
            "--limit",
            "1",
        ]
        if request.base is not None:
            command.extend(["--base", request.base])
        if url_only:
            command.extend(["--jq", '.[0].url // ""'])
        return command

    @staticmethod
    def _github_pr_create_command(
        request: m.Infra.GithubPullRequestRequest, head: str
    ) -> p.Result[t.StrSequence]:
        """Build one fully non-interactive native create command."""
        if request.title is None:
            return r.fail("title is required for pull-request creation")
        if request.body is None:
            return r.fail("body is required for pull-request creation")
        command = [
            c.Infra.GH,
            c.Infra.PR,
            c.Infra.PullRequestAction.CREATE,
            "--head",
            head,
            "--title",
            request.title,
            "--body",
            request.body,
        ]
        if request.base is not None:
            command.extend(["--base", request.base])
        if request.draft:
            command.append("--draft")
        return r.ok(tuple(command))

    @staticmethod
    def _github_pr_write_log(
        log_path: Path, output: p.Cli.CommandOutput
    ) -> p.Result[bool]:
        """Persist one command result through the canonical file facade."""
        content = output.stdout
        if output.stderr:
            content = f"{content}{output.stderr}"
        if not content:
            content = f"exit_code={output.exit_code}\n"
        return u.Cli.files_write_text(log_path, content)

    @classmethod
    def _github_pr_outcome(
        cls, *, display: str, log_path: Path, output: p.Cli.CommandOutput
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Translate one external command result into the owned outcome."""
        write_result = cls._github_pr_write_log(log_path, output)
        if write_result.failure:
            return r.fail(write_result.error or f"failed to write {log_path}")
        status = (
            c.Infra.ResultStatus.OK
            if output.exit_code == 0
            else c.Infra.ResultStatus.FAIL
        )
        return r.ok(
            m.Infra.GithubPullRequestOutcome(
                display=display,
                status=status,
                elapsed=int(output.duration),
                exit_code=output.exit_code,
                log_path=str(log_path),
            )
        )

    @staticmethod
    def _github_pr_current_head(repo_root: Path) -> p.Result[str]:
        """Resolve a non-detached current branch."""
        result = u.Infra.git_capture(repo_root, ("branch", "--show-current"))
        if result.failure:
            return r.fail(result.error or "failed to resolve current branch")
        head = result.value.strip()
        if not head:
            return r.fail("head branch is required from a detached HEAD")
        return r.ok(head)

    @classmethod
    def _github_pr_execute_create(
        cls,
        *,
        request: m.Infra.GithubPullRequestRequest,
        repo_root: Path,
        head: str,
        display: str,
        log_path: Path,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Create at most one open pull request for the base/head pair."""
        command = cls._github_pr_create_command(request, head)
        if command.failure:
            return r.fail(command.error or "invalid pull-request create request")
        lookup = u.Cli.run_raw(
            cls._github_pr_list_command(request, head, url_only=True), cwd=repo_root
        )
        if lookup.failure:
            return r.fail(lookup.error or "pull-request lookup failed")
        lookup_output = lookup.value
        if lookup_output.exit_code != 0 or lookup_output.stdout.strip():
            return cls._github_pr_outcome(
                display=display, log_path=log_path, output=lookup_output
            )
        execution = u.Cli.run_raw(command.value, cwd=repo_root)
        if execution.failure:
            return r.fail(execution.error or "pull-request creation failed")
        return cls._github_pr_outcome(
            display=display, log_path=log_path, output=execution.value
        )

    @classmethod
    def execute_github_pull_request(
        cls,
        *,
        request: m.Infra.GithubPullRequestRequest,
        repo_root: Path,
        display: str,
        log_path: Path,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Execute one validated status or idempotent create action."""
        if not repo_root.is_dir():
            return r.fail(f"repository root is not a directory: {repo_root}")
        head_result = (
            r.ok(request.head)
            if request.head is not None
            else cls._github_pr_current_head(repo_root)
        )
        if request.action is c.Infra.PullRequestAction.STATUS and head_result.failure:
            execution = u.Cli.run_raw(
                (c.Infra.GH, c.Infra.PR, c.Infra.PullRequestAction.STATUS),
                cwd=repo_root,
            )
        elif head_result.failure:
            return r.fail(head_result.error or "head branch is required")
        elif request.action is c.Infra.PullRequestAction.CREATE:
            return cls._github_pr_execute_create(
                request=request,
                repo_root=repo_root,
                head=head_result.value,
                display=display,
                log_path=log_path,
            )
        else:
            execution = u.Cli.run_raw(
                cls._github_pr_list_command(request, head_result.value, url_only=False),
                cwd=repo_root,
            )
        if execution.failure:
            return r.fail(execution.error or "pull-request status failed")
        return cls._github_pr_outcome(
            display=display, log_path=log_path, output=execution.value
        )


__all__: list[str] = ["FlextInfraUtilitiesGithubPrExecutionMixin"]
