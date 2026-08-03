"""HTTPS, SSH, and deploy-key host aliases share one repository identity."""

from __future__ import annotations

from flext_infra import u
from flext_tests import tm


class TestsGitRemoteIdentity:
    """Private CI may rewrite origin to aliased SSH without changing the repo."""

    def test_https_ssh_and_host_alias_urls_match(self) -> None:
        https = "https://github.com/datacosmos-br/cosmos-charts.git"
        ssh = "git@github.com:datacosmos-br/cosmos-charts.git"
        alias = "git@charts-github:datacosmos-br/cosmos-charts.git"
        identity = u.Infra.git_remote_identity(https)
        tm.that(identity, eq="datacosmos-br/cosmos-charts")
        tm.that(u.Infra.git_remote_identity(ssh), eq=identity)
        tm.that(u.Infra.git_remote_identity(alias), eq=identity)

    def test_different_repositories_do_not_match(self) -> None:
        left = "https://github.com/datacosmos-br/cosmos-charts.git"
        right = "git@charts-github:datacosmos-br/cosmos-gitops.git"
        tm.that(
            u.Infra.git_remote_identity(left) == u.Infra.git_remote_identity(right),
            eq=False,
        )


__all__: tuple[str, ...] = ()
