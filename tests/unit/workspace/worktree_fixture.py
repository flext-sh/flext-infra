"""Shared real-Git fixture for worktree service behavior."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, m, t
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.worktree import FlextInfraWorktreeService
from flext_tests import tm
from tests import u


class WorktreeFixture:
    """Provide one repository and lane-path contract without collecting tests."""

    @staticmethod
    def add_worktree(repository: Path, branch: str, *, base: str = "HEAD") -> str:
        """Create one applied worktree and return Git's canonical lane path."""
        return tm.ok(
            FlextInfraWorktreeService(
                repository_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=base,
                apply_changes=True,
            ).execute()
        )

    @staticmethod
    def override_repository_manifest(
        repository: Path, updates: Mapping[str, t.JsonValue]
    ) -> m.Infra.RepositoryRef:
        """Re-select the observed repository, apply overrides, rewrite its manifest."""
        observed = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(repository))
        declared = observed.repository.model_copy(update=dict(updates))
        tm.ok(
            u.Cli.yaml_dump(
                repository / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME,
                {
                    "version": 3,
                    "name": declared.name,
                    "repository": declared.model_dump(mode="json"),
                },
            )
        )
        return declared

    @classmethod
    def attach_member_child(cls, root: Path) -> Path:
        """Initialize the standard child member and link it to the root ledger."""
        child = root / "fixture-child"
        cls.initialize_governed_project(
            child,
            "fixture-child",
            workspace="fixture-child",
            database="fixture_child",
            issue_prefix="fixture-child",
            beads_owner=False,
        )
        cls.link_member_beads(
            child,
            root,
            workspace_name="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        return child

    @staticmethod
    def _lane(primary_root: Path, outermost_project: Path, branch: str) -> Path:
        """Resolve the lane through the production topology owner."""
        _ = outermost_project
        return tm.ok(
            FlextInfraWorktreeService.canonical_lane_path(primary_root, branch)
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
        """Write the minimum typed project used by real Git fixtures.

        ``[project.urls].Repository`` is part of that minimum: it is the
        declared identity the declaration-only Makefile projection reads when a
        repository ships no ``config/workspace.yaml``, and every governed
        repository publishes it.
        """
        root.mkdir(parents=True, exist_ok=True)
        pyproject = root / "pyproject.toml"
        repository_url = WorktreeFixture.governed_repository_url(distribution)
        pyproject.write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            f'[project.urls]\nRepository = "{repository_url}"\n',
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

    @classmethod
    def link_member_beads(
        cls,
        member: Path,
        workspace: Path,
        *,
        workspace_name: str,
        database: str,
        issue_prefix: str,
    ) -> Path:
        """Create the checked-in member route to the workspace-owned ledger."""
        member.mkdir(parents=True, exist_ok=True)
        route = member / ".beads"
        route.symlink_to(os.path.relpath(workspace / ".beads", member))
        cls.write_beads_project(
            member,
            workspace=workspace_name,
            database=database,
            issue_prefix=issue_prefix,
        )
        return route

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
        beads_owner: bool = True,
    ) -> Path:
        """Create one self-identifying governed project with a real Git origin.

        Every governed repository commits its own checksum-verified Mise seeds;
        ``codegen conform`` validates them and never mints them, so the fixture
        carries them exactly as a real checkout does.
        """
        pyproject = cls.write_python_project(root, distribution)
        u.Tests.copy_tracked_mise_seeds(root)
        if beads_owner:
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
        provider = u.Tests.provider()
        baseline = tm.ok(u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "remote.origin.skipDefaultUpdate", "true"],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    baseline,
                ],
                cwd=root,
            )
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
        """Capture all repository bytes and porcelain status.

        Git metadata is excluded; every runtime-state owner lives outside the
        repository checkout by construction.
        """
        excluded_roots = frozenset({c.Infra.GIT_DIR})
        tree = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
                and not excluded_roots.intersection(path.relative_to(root).parts)
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
