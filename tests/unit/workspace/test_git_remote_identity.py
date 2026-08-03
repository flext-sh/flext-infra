"""HTTPS and SSH Git remotes share one comparable identity."""

from __future__ import annotations

from flext_infra import u
from flext_tests import tm


class TestsGitRemoteIdentity:
    """Private CI may rewrite origin to SSH without changing repository identity."""

    def test_https_and_ssh_github_urls_match(self) -> None:
        https = "https://github.com/datacosmos-br/cosmos-charts.git"
        ssh = "git@github.com:datacosmos-br/cosmos-charts.git"
        tm.that(u.Infra.git_remote_identity(https), eq=u.Infra.git_remote_identity(ssh))

    def test_different_repositories_do_not_match(self) -> None:
        left = "https://github.com/datacosmos-br/cosmos-charts.git"
        right = "git@github.com:datacosmos-br/cosmos-gitops.git"
        tm.that(
            u.Infra.git_remote_identity(left) == u.Infra.git_remote_identity(right),
            eq=False,
        )


__all__: tuple[str, ...] = ()
