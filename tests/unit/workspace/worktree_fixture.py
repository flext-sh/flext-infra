"""Shared real-Git fixture for worktree service behavior."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config
from flext_tests import tm
from tests import m, u


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

    @classmethod
    def codegen_member_lane(
        cls, tmp_path: Path
    ) -> tuple[
        Path,
        Path,
        Path,
        m.Infra.WorkspaceSpec,
        tuple[tuple[tuple[str, bytes], ...], str],
        tuple[tuple[tuple[str, bytes], ...], str],
    ]:
        """Create a governed member lane with both owning checkouts dirty."""
        provider = config.Infra.codegen.providers[0]
        root_repository = u.Tests.repository_ref("fixture-workspace").model_copy(
            update={"path": Path(), "package": False, "editable": False}
        )
        member = u.Tests.repository_ref(
            "flext-cli", role=c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        source = tmp_path / "member-source"
        cls.write_python_project(source, member.distribution)
        u.Tests.initialize_git_repo(source, member.url)
        u.Tests.git_bootstrap(source, ("switch", "-c", provider.branch))

        superproject = tmp_path / "workspace"
        cls.write_python_project(superproject, root_repository.distribution)
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root_repository.distribution,
            repository=root_repository,
            members=(member,),
            ledger_id="governing-ledger",
            ledger_prefix="governing-prefix",
        )
        tm.ok(
            u.Cli.yaml_dump(
                superproject / "config" / "workspace.yaml",
                workspace.model_dump(
                    mode="json",
                    exclude_none=True,
                    exclude={"external_dependency_paths"},
                ),
            )
        )
        u.Tests.initialize_git_repo(superproject, root_repository.url)
        u.Tests.git_bootstrap(
            superproject,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-b",
                provider.branch,
                str(source),
                member.path.as_posix(),
            ),
        )
        primary = superproject / member.path
        u.Tests.git_bootstrap(
            superproject,
            (
                "config",
                "-f",
                c.Infra.GITMODULES,
                f"submodule.{member.path.as_posix()}.url",
                member.url,
            ),
        )
        u.Tests.git_bootstrap(
            primary, ("remote", "set-url", c.Infra.GIT_ORIGIN, member.url)
        )
        u.Tests.configure_git_identity(primary)
        u.Tests.git_bootstrap(superproject, ("add", "-A"))
        u.Tests.git_bootstrap(superproject, ("commit", "-m", "Attach governed member"))
        lane = tmp_path / "member-lane"
        tm.ok(
            u.Infra.git_add_lane_worktree(
                m.Infra.GitWorktreeAddRequest(
                    repo_root=primary,
                    lane=lane,
                    branch="bugfix/member-lane",
                    base=c.Infra.GIT_HEAD,
                )
            )
        )
        primary_pyproject = primary / "pyproject.toml"
        primary_pyproject.write_text(
            f"{primary_pyproject.read_text(encoding='utf-8')}# human member WIP\n",
            encoding="utf-8",
        )
        (superproject / "operator-notes.txt").write_text(
            "human superproject WIP\n", encoding="utf-8"
        )
        return (
            superproject,
            primary,
            lane,
            workspace,
            cls.repository_snapshot(superproject),
            cls.repository_snapshot(primary),
        )


__all__: tuple[str, ...] = ("WorktreeFixture",)
