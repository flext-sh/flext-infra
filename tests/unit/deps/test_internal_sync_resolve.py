from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_cli import cli
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from tests.utilities import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsInternalSyncResolve:
    """Behavior contract for test_internal_sync_resolve."""

    # mro-wkii.4.15: the shared fixture owns singleton lifecycle for this suite.

    @staticmethod
    def create_git_repo(tmp_path: Path, name: str) -> Path:
        repo = tmp_path / name
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
        u.Tests.initialize_git_repo(repo)
        return repo

    def test_resolve_ref_prefers_github_head_ref(self, tmp_path: Path) -> None:
        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().resolve_ref(Path(sys.argv[1])))"
                ),
                str(tmp_path),
            ],
            env={
                "GITHUB_ACTIONS": "true",
                "GITHUB_HEAD_REF": "feature/test",
                "GITHUB_REF_NAME": "main",
            },
        )

        tm.ok(result)
        tm.that(result.value, eq="feature/test")

    def test_resolve_ref_uses_github_ref_name_when_head_ref_is_empty(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().resolve_ref(Path(sys.argv[1])))"
                ),
                str(tmp_path),
            ],
            env={
                "GITHUB_ACTIONS": "true",
                "GITHUB_HEAD_REF": "",
                "GITHUB_REF_NAME": "main",
            },
        )

        tm.ok(result)
        tm.that(result.value, eq="main")

    def test_resolve_ref_uses_current_git_branch(self, tmp_path: Path) -> None:
        repo = self.create_git_repo(tmp_path, "repo")
        assert u.Cli.run_checked(["git", "checkout", "-B", "develop"], cwd=repo).success

        result = FlextInfraInternalDependencySyncService().resolve_ref(repo)

        assert result == "develop"

    def test_resolve_ref_uses_exact_tag_on_detached_head(self, tmp_path: Path) -> None:
        repo = self.create_git_repo(tmp_path, "repo")
        assert u.Cli.run_checked(
            ["git", "tag", "-a", "v1.0.0", "-m", "release"],
            cwd=repo,
        ).success
        assert u.Cli.run_checked(["git", "checkout", "v1.0.0"], cwd=repo).success

        result = FlextInfraInternalDependencySyncService().resolve_ref(repo)

        assert result == "v1.0.0"

    def test_resolve_ref_falls_back_to_main_for_non_repo(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()

        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().resolve_ref(Path(sys.argv[1])))"
                ),
                str(project),
            ],
            remove_env_keys=(
                "GITHUB_ACTIONS",
                "GITHUB_HEAD_REF",
                "GITHUB_REF_NAME",
            ),
        )

        tm.ok(result)
        tm.that(result.value, eq="main")

    def test_infer_owner_from_origin_reads_real_remote(self, tmp_path: Path) -> None:
        repo = self.create_git_repo(tmp_path, "repo")
        _ = cli.run_checked(
            [
                "git",
                "remote",
                "add",
                "origin",
                "git@github.com:flext-sh/flext-core.git",
            ],
            cwd=repo,
        )

        result = FlextInfraInternalDependencySyncService().infer_owner_from_origin(repo)

        assert result == "flext-sh"

    def test_infer_owner_from_origin_returns_none_without_remote(
        self,
        tmp_path: Path,
    ) -> None:
        repo = self.create_git_repo(tmp_path, "repo")

        result = FlextInfraInternalDependencySyncService().infer_owner_from_origin(repo)

        assert result is None

    def test_synthesized_repo_map_builds_public_urls(self) -> None:
        result = FlextInfraInternalDependencySyncService().synthesized_repo_map(
            "flext-sh",
            {"flext-core", "flext-api"},
        )

        assert result["flext-core"].ssh_url == "git@github.com:flext-sh/flext-core.git"
        assert (
            result["flext-api"].https_url == "https://github.com/flext-sh/flext-api.git"
        )
