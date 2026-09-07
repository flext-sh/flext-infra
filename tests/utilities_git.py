"""Repository-construction Git fixture test utilities for flext-infra."""

from __future__ import annotations

from pathlib import Path

from flext_cli import cli as cli_facade
from flext_infra import config, u
from flext_tests import tm
from tests import c, m, t
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin


class TestsFlextInfraUtilitiesGitMixin:
    """Real Git repository construction and inspection fixture helpers."""

    @staticmethod
    def integration_branch(repo_root: Path) -> str:
        """Resolve the integration branch the fixture publishes, as production does."""
        return tm.ok(
            u.Infra.repository_baseline_branch(
                repo_root,
                preference=tuple(
                    config.Infra.codegen.branch_policy.integration_branch_preference
                ),
            )
        )

    @staticmethod
    def checkout_integration(repo_root: Path) -> str:
        """Move the fixture onto its integration branch and return its name."""
        branch = TestsFlextInfraUtilitiesGitMixin.integration_branch(repo_root)
        tm.ok(
            cli_facade.run_checked(
                [c.Infra.GIT, "switch", "--create", branch], cwd=repo_root
            )
        )
        return branch

    @staticmethod
    def merge_pull_request(repo_root: Path, subject: str) -> None:
        """Land one pull request the way GitHub does: a merge commit titled ``subject``."""
        branch = f"pr/{abs(hash(subject))}"
        current = tm.ok(
            u.Infra.git_current_branch(m.Infra.GitRepoRequest(repo_root=repo_root))
        ).text
        run = cli_facade.run_checked
        tm.ok(run([c.Infra.GIT, "switch", "--create", branch], cwd=repo_root))
        change = repo_root / "CHANGES.md"
        with change.open("a", encoding="utf-8") as handle:
            handle.write(f"{subject}\n")
        tm.ok(run([c.Infra.GIT, "add", "CHANGES.md"], cwd=repo_root))
        tm.ok(run([c.Infra.GIT, "commit", "-m", f"work: {subject}"], cwd=repo_root))
        tm.ok(run([c.Infra.GIT, "switch", current], cwd=repo_root))
        tm.ok(
            run([c.Infra.GIT, "merge", "--no-ff", "-m", subject, branch], cwd=repo_root)
        )

    @staticmethod
    def commit_git_changes(repo_root: Path, message: str) -> None:
        """Commit the current real fixture changes with deterministic identity."""
        TestsFlextInfraUtilitiesGitMixin.git_bootstrap(repo_root, ("add", "-A"))
        tm.ok(
            u.Infra.git_commit(
                m.Infra.GitCommitRequest(repo_root=repo_root, message=message)
            )
        )

    @staticmethod
    def git_ref_exists(repo_root: Path, ref_name: str) -> bool:
        """Return whether a real Git fixture contains the exact ref."""
        report = tm.ok(
            u.Infra.git_ref_exists(
                m.Infra.GitRefRequest(repo_root=repo_root, reference=ref_name)
            )
        )
        exists: bool = t.Infra.BOOL_ADAPTER.validate_python(report.value)
        return exists

    @staticmethod
    def configure_local_origin(repo_root: Path, remote_root: Path) -> Path:
        """Attach and seed a local bare origin for push behavior tests.

        ``initialize_git_repo`` already seeds a placeholder origin, so the
        remote is re-pointed rather than added: a second ``remote add``
        fails with "remote origin already exists".
        """
        bootstrap = TestsFlextInfraUtilitiesGitMixin.git_bootstrap
        bare_remote = remote_root / "origin.git"
        bare_remote.mkdir(parents=True, exist_ok=True)
        bootstrap(bare_remote, ("init", "--bare"))
        bootstrap(
            repo_root, ("remote", "set-url", c.Infra.GIT_ORIGIN, str(bare_remote))
        )
        tm.ok(
            u.Infra.git_push_upstream(
                m.Infra.GitPushRequest(
                    repo_root=repo_root,
                    remote=c.Infra.GIT_ORIGIN,
                    branch=c.Infra.GIT_MAIN,
                )
            )
        )
        bootstrap(
            bare_remote,
            ("symbolic-ref", c.Infra.GIT_HEAD, f"refs/heads/{c.Infra.GIT_MAIN}"),
        )
        return bare_remote

    @staticmethod
    def configure_git_identity(repository_root: Path) -> None:
        """Set deterministic repository-local identity for real Git fixtures."""
        bootstrap = TestsFlextInfraUtilitiesGitMixin.git_bootstrap
        bootstrap(
            repository_root, ("config", "--local", "user.email", "tests@flext.local")
        )
        bootstrap(repository_root, ("config", "--local", "user.name", "Flext Tests"))

    @staticmethod
    def isolated_git_keys() -> t.StrSequence:
        """Return the repository-local Git variables a fixture must not inherit.

        Git exports GIT_DIR, GIT_WORK_TREE and GIT_INDEX_FILE while running
        hooks. A fixture that inherits them silently operates on the calling
        repository instead of its own tmp_path, so repository construction
        must never inherit them. The set is whatever the installed Git
        declares, never a hardcoded list.
        """
        declared = cli_facade.capture([c.Infra.GIT, "rev-parse", "--local-env-vars"])
        tm.ok(declared)
        return tuple(declared.value.split())

    @staticmethod
    def git_bootstrap(
        repo_root: Path,
        command: t.StrSequence,
        *,
        overrides: t.StrMapping | None = None,
    ) -> None:
        """Run one repository-construction command isolated from the caller.

        Only repository creation belongs here: once a worktree exists, every
        behavioral operation is expressed through the typed ``u.Infra.git_*``
        facade, which binds the repository explicitly.

        Isolation is expressed with ``remove_env_keys`` because ``env`` is an
        overlay that can only add or replace keys, never remove them
        ``overrides`` carries topology the fixture itself requires, such as
        permitting the file transport for a local bare origin.
        """
        tm.ok(
            cli_facade.run_checked(
                [c.Infra.GIT, *command],
                cwd=repo_root,
                env=overrides,
                remove_env_keys=TestsFlextInfraUtilitiesGitMixin.isolated_git_keys(),
            )
        )

    @staticmethod
    def initialize_git_repo(repo_root: Path, origin_url: str | None = None) -> None:
        """Initialize and commit a deterministic Git fixture.

        The initial commit allows an empty tree so fixtures that seed
        hooks or config before any file still get a resolvable HEAD.
        A fake remote baseline ref is created so workspace discovery
        matches a real clone. The baseline branch is read from the same
        provider config production reads. ``origin_url`` defaults to the
        repository itself; fixtures that must be recognised as
        provider-governed pass their declared provider URL instead.
        """
        baseline_branch = TestsFlextInfraUtilitiesProjectFixtureMixin.provider().branch
        bootstrap = TestsFlextInfraUtilitiesGitMixin.git_bootstrap
        bootstrap(repo_root, ("init", "-b", c.Infra.GIT_MAIN))
        bootstrap(repo_root, ("config", "user.email", "tests@flext.local"))
        bootstrap(repo_root, ("config", "user.name", "Flext Tests"))
        bootstrap(
            repo_root,
            ("remote", "add", c.Infra.GIT_ORIGIN, origin_url or str(repo_root)),
        )
        bootstrap(repo_root, ("add", "-A"))
        bootstrap(repo_root, ("commit", "--allow-empty", "-m", "init"))
        bootstrap(
            repo_root,
            (
                "update-ref",
                f"refs/remotes/{c.Infra.GIT_ORIGIN}/{baseline_branch}",
                c.Infra.GIT_HEAD,
            ),
        )


__all__: list[str] = ["TestsFlextInfraUtilitiesGitMixin"]
