"""Repository-local GitHub PR dispatch contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def _repository(tmp_path: Path) -> Path:
    repository = u.Tests.create_github_workspace(tmp_path)
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "demo-project"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    package = repository / "src" / "demo_project"
    package.mkdir(parents=True)
    (package / "__init__.py").touch()
    return repository


def test_pull_request_dispatch_processes_only_supplied_repository(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)

    report = tm.ok(
        u.Infra.run_github_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(repository),
                action=c.Infra.PullRequestAction.STATUS,
                fail_fast=False,
            )
        )
    )

    tm.that(report.total, eq=1)
    tm.that(report.success + report.fail, eq=1)


def test_pull_request_dispatch_accepts_only_repository_alias(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    tm.ok(
        u.Infra.run_github_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(repository), projects=["."], fail_fast=True
            )
        )
    )
    tm.fail(
        u.Infra.run_github_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(repository), projects=["another-project"]
            )
        ),
        has="unknown project locators",
    )
