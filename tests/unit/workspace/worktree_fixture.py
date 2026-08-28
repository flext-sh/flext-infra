"""Shared real-Git fixture for worktree service behavior."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, t
from flext_tests import tm
from tests import u


class WorktreeFixture:
    """Provide one repository and lane-path contract without collecting tests."""

    @staticmethod
    def _lane(primary_root: Path, outermost_project: Path, branch: str) -> Path:
        """Derive the configured collision-safe test contract."""
        digest = u.Cli.sha256_content(str(primary_root.resolve()))[
            : c.Infra.WORKTREE_NAMESPACE_DIGEST_LENGTH
        ]
        namespace = f"{primary_root.resolve().name}-{digest}"
        return (
            outermost_project.resolve().parent
            / c.Infra.WORKTREES_DIRNAME
            / namespace
            / branch
        )

    @staticmethod
    def _repository(tmp_path: Path) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            'description = "A standard PEP 621 description string"\n',
            encoding="utf-8",
        )
        (repository / "Makefile").write_text(
            ".PHONY: setup\n"
            "setup:\n"
            '\t@test "$(WORKSPACE)" = "$(CURDIR)"\n'
            '\t@grep -q "^\\[project\\]" "$(WORKSPACE)/pyproject.toml"\n'
            '\t@printf "setting up %s\\n" "$(WORKSPACE)"\n',
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(repository)
        return repository

    @staticmethod
    def _commit_fixture(repository: Path, message: str) -> None:
        """Commit one deliberate fixture mutation."""
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "add", "Makefile", "pyproject.toml"], cwd=repository
            )
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "commit", "-m", message], cwd=repository))

    @staticmethod
    def write_python_project(root: Path, distribution: str) -> Path:
        """Write the minimum typed project used by real Git fixtures."""
        root.mkdir(parents=True, exist_ok=True)
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n',
            encoding="utf-8",
        )
        package = root / "src" / distribution.replace("-", "_")
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        return pyproject

    @staticmethod
    def governed_repository_url(distribution: str) -> str:
        """Build a fixture repository URL from the configured provider."""
        provider = u.Tests.provider()
        return f"{provider.base_url.rstrip('/')}/{distribution}.git"

    @staticmethod
    def write_beads_project(
        root: Path,
        *,
        workspace: str,
        database: str,
        issue_prefix: str,
        custom_issue_types: tuple[str, ...] = (),
    ) -> Path:
        """Write one repository-local Beads identity input."""
        path = root / "config" / "beads.yaml"
        payload: dict[str, t.JsonValue] = {
            "version": 1,
            "workspace": workspace,
            "database": database,
            "issue_prefix": issue_prefix,
        }
        if custom_issue_types:
            custom_types: list[t.JsonValue] = [*custom_issue_types]
            payload["custom_issue_types"] = custom_types
        tm.ok(u.Cli.yaml_dump(path, payload))
        return path

    @classmethod
    def initialize_governed_project(
        cls,
        root: Path,
        distribution: str,
        *,
        workspace: str,
        database: str,
        issue_prefix: str,
        custom_issue_types: tuple[str, ...] = (),
    ) -> Path:
        """Create one self-identifying governed project with a real Git origin."""
        pyproject = cls.write_python_project(root, distribution)
        cls.write_beads_project(
            root,
            workspace=workspace,
            database=database,
            issue_prefix=issue_prefix,
            custom_issue_types=custom_issue_types,
        )
        u.Tests.initialize_git_repo(
            root, origin_url=cls.governed_repository_url(distribution)
        )
        return pyproject

    @classmethod
    def write_gitmodules(cls, root: Path, projects: tuple[str, ...]) -> Path:
        """Declare governed subprojects from the configured provider contract."""
        provider = u.Tests.provider()
        path = root / c.Infra.GITMODULES
        path.write_text(
            "".join(
                (
                    f'[submodule "{project}"]\n'
                    f"\tpath = {project}\n"
                    f"\turl = {cls.governed_repository_url(project)}\n"
                    f"\tbranch = {provider.branch}\n"
                )
                for project in projects
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def repository_snapshot(root: Path) -> tuple[tuple[tuple[str, bytes], ...], str]:
        """Capture all non-Git bytes and exact porcelain status."""
        tree = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
                and c.Infra.GIT_DIR not in path.relative_to(root).parts
            )
        )
        status = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=root,
            )
        )
        return tree, status


__all__: tuple[str, ...] = ("WorktreeFixture",)
