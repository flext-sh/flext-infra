"""Git operations utilities for repository interaction."""

from __future__ import annotations

import shutil
from pathlib import Path

from flext_core import r
from flext_infra import FlextInfraUtilitiesIo, FlextInfraUtilitiesSubprocess, c, m


class FlextInfraUtilitiesGit:
    """Static Git operations utilities."""

    @staticmethod
    def git_run(cmd: list[str], cwd: Path | None = None) -> r[str]:
        return FlextInfraUtilitiesSubprocess.capture([c.Infra.Cli.GIT, *cmd], cwd=cwd)

    @staticmethod
    def git_run_checked(cmd: list[str], cwd: Path | None = None) -> r[bool]:
        return FlextInfraUtilitiesSubprocess.run_checked(
            [c.Infra.Cli.GIT, *cmd], cwd=cwd
        )

    @staticmethod
    def git_is_repo(path: Path) -> bool:
        return FlextInfraUtilitiesSubprocess.run_checked(
            [c.Infra.Cli.GIT, "rev-parse", "--is-inside-work-tree"], cwd=path
        ).is_success

    @staticmethod
    def git_current_branch(root: Path) -> r[str]:
        return FlextInfraUtilitiesSubprocess.capture(
            [c.Infra.Cli.GIT, "rev-parse", "--abbrev-ref", "HEAD"], cwd=root
        )

    @staticmethod
    def git_has_changes(root: Path) -> r[bool]:
        return FlextInfraUtilitiesSubprocess.capture(
            [c.Infra.Cli.GIT, "status", "--porcelain"], cwd=root
        ).map(lambda v: bool(v.strip()))

    @staticmethod
    def git_diff_names(root: Path, *, cached: bool = False) -> r[str]:
        cmd = [c.Infra.Cli.GIT, "diff", "--name-only"]
        if cached:
            cmd.insert(2, "--cached")
        return FlextInfraUtilitiesSubprocess.capture(cmd, cwd=root)

    @staticmethod
    def git_checkout(
        root: Path, branch: str, *, create: bool = False, track: str | None = None
    ) -> r[bool]:
        cmd = [c.Infra.Cli.GIT, "checkout"]
        if create:
            cmd.append("-B")
        cmd.append(branch)
        if track:
            cmd.append(track)
        return FlextInfraUtilitiesSubprocess.run_checked(cmd, cwd=root)

    @staticmethod
    def git_fetch(root: Path, remote: str = "", branch: str = "") -> r[bool]:
        cmd = [c.Infra.Cli.GIT, "fetch"]
        if remote:
            cmd.append(remote)
        if branch:
            cmd.append(branch)
        return FlextInfraUtilitiesSubprocess.run_checked(cmd, cwd=root)

    @staticmethod
    def git_add(root: Path, *paths: str) -> r[bool]:
        return FlextInfraUtilitiesSubprocess.run_checked(
            [c.Infra.Cli.GIT, "add", *(paths or ["-A"])], cwd=root
        )

    @staticmethod
    def git_commit(root: Path, msg: str) -> r[bool]:
        return FlextInfraUtilitiesSubprocess.run_checked(
            [c.Infra.Cli.GIT, "commit", "-m", msg], cwd=root
        )

    @staticmethod
    def git_push(
        root: Path, remote: str = "", branch: str = "", *, upstream: bool = False
    ) -> r[bool]:
        cmd = [c.Infra.Cli.GIT, "push"]
        if upstream:
            cmd.append("-u")
        if remote:
            cmd.append(remote)
        if branch:
            cmd.append(branch)
        return FlextInfraUtilitiesSubprocess.run_checked(cmd, cwd=root)

    @staticmethod
    def git_pull(
        root: Path, *, rebase: bool = False, remote: str = "", branch: str = ""
    ) -> r[bool]:
        cmd = [c.Infra.Cli.GIT, "pull"]
        if rebase:
            cmd.append("--rebase")
        if remote:
            cmd.append(remote)
        if branch:
            cmd.append(branch)
        return FlextInfraUtilitiesSubprocess.run_checked(cmd, cwd=root)

    @staticmethod
    def git_tag_exists(root: Path, tag: str) -> r[bool]:
        return FlextInfraUtilitiesSubprocess.capture(
            [c.Infra.Cli.GIT, "tag", "-l", tag], cwd=root
        ).map(lambda v: v.strip() == tag)

    @staticmethod
    def git_create_tag(root: Path, tag: str, msg: str = "") -> r[bool]:
        return FlextInfraUtilitiesSubprocess.run_checked(
            [c.Infra.Cli.GIT, "tag", "-a", tag, "-m", msg or f"release: {tag}"],
            cwd=root,
        )

    @staticmethod
    def git_list_tags(root: Path, *, sort: str = "-v:refname") -> r[str]:
        return FlextInfraUtilitiesSubprocess.capture(
            [c.Infra.Cli.GIT, "tag", f"--sort={sort}"], cwd=root
        )

    @staticmethod
    def lint_workflows(
        root: Path, *, report_path: Path | None = None, strict: bool = False
    ) -> r[m.Infra.WorkflowLintResult]:
        """Run actionlint and return results."""
        exe = shutil.which("actionlint")
        if not exe:
            res = m.Infra.WorkflowLintResult(status="skipped", reason="not installed")
            if report_path:
                FlextInfraUtilitiesIo.write_json(report_path, res, sort_keys=True)
            return r[m.Infra.WorkflowLintResult].ok(res)

        out_res = FlextInfraUtilitiesSubprocess.run_raw([exe], cwd=root)
        if out_res.is_success:
            p = m.Infra.WorkflowLintResult(
                status="ok",
                exit_code=out_res.value.exit_code,
                stdout=out_res.value.stdout,
                stderr=out_res.value.stderr,
            )
        else:
            p = m.Infra.WorkflowLintResult(
                status="fail", exit_code=1, detail=out_res.error or ""
            )
        if report_path:
            FlextInfraUtilitiesIo.write_json(report_path, p, sort_keys=True)
        return (
            r[m.Infra.WorkflowLintResult].fail(out_res.error or "lint failed")
            if p.status == "fail" and strict
            else r[m.Infra.WorkflowLintResult].ok(p)
        )


__all__ = ["FlextInfraUtilitiesGit"]
