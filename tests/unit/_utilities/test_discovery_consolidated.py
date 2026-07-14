from __future__ import annotations

from pathlib import Path

from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from tests import c
from tests import m
from tests import u
from flext_tests import tm


class TestsFlextInfraUtilitiesdiscoveryconsolidated:
    @staticmethod
    def _init_git_repo(repo_root: Path) -> None:
        commands = (
            ["git", "init"],
            ["git", "config", "user.email", "test@example.com"],
            ["git", "config", "user.name", "Test User"],
        )
        for command in commands:
            result = u.Cli.run_raw(command, cwd=repo_root)
            tm.ok(result)
            tm.that(result.value.exit_code, eq=0)

    def test_discover_project_roots_with_real_workspace_root(self) -> None:
        # Walk up from the test file to find the workspace root (contains flext-core)
        candidate = Path(__file__).resolve()
        workspace_root = candidate
        while candidate != candidate.parent:
            if (candidate / "flext-core").is_dir():
                workspace_root = candidate
                break
            candidate = candidate.parent

        roots = u.Infra.discover_project_roots(workspace_root)

        assert any(root.name == "flext-core" for root in roots)
        assert all(root.is_dir() for root in roots)

    def test_discover_project_roots_from_tmp_workspace(self, tmp_path: Path) -> None:
        project = tmp_path / "demo-project"
        (project / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        (project / c.Infra.MAKEFILE_FILENAME).write_text("all:\n", encoding="utf-8")
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "[tool.poetry]\nname='demo'\n", encoding="utf-8"
        )

        roots = u.Infra.discover_project_roots(tmp_path)

        tm.that(roots, eq=[project])

    def test_discover_project_roots_prefers_tool_flext_workspace_members(
        self, tmp_path: Path
    ) -> None:
        workspace_src = tmp_path / c.Infra.DEFAULT_SRC_DIR
        workspace_src.mkdir(parents=True)
        (tmp_path / c.Infra.MAKEFILE_FILENAME).write_text("all:\n", encoding="utf-8")
        (tmp_path / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\n\n"
            "[tool.flext.workspace]\n"
            "members = ['beta', 'alpha']\n",
            encoding="utf-8",
        )
        for project_name in ("alpha", "beta"):
            project_root = tmp_path / project_name
            (project_root / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
            (project_root / c.Infra.MAKEFILE_FILENAME).write_text(
                "all:\n", encoding="utf-8"
            )
            (project_root / c.Infra.PYPROJECT_FILENAME).write_text(
                f"[project]\nname='{project_name}'\n", encoding="utf-8"
            )

        roots = u.Infra.discover_project_roots(tmp_path)

        tm.that(roots, eq=[tmp_path / "beta", tmp_path / "alpha"])

    def test_discover_project_roots_skips_untracked_git_projects(
        self, tmp_path: Path
    ) -> None:
        self._init_git_repo(tmp_path)
        tracked_project = tmp_path / "tracked"
        (tracked_project / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        (tracked_project / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='tracked'\n", encoding="utf-8"
        )
        untracked_project = tmp_path / "untracked"
        (untracked_project / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        (untracked_project / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='untracked'\n", encoding="utf-8"
        )
        add_result = u.Cli.run_raw(
            ["git", "add", "tracked/pyproject.toml"], cwd=tmp_path
        )
        tm.ok(add_result)
        tm.that(add_result.value.exit_code, eq=0)

        roots = u.Infra.discover_project_roots(tmp_path)

        tm.that(roots, eq=[tracked_project, untracked_project])

    def test_iter_python_files_returns_result_with_paths(self, tmp_path: Path) -> None:
        project = tmp_path / "pkg"
        src_dir = project / c.Infra.DEFAULT_SRC_DIR
        test_dir = project / c.Infra.DIR_TESTS
        src_dir.mkdir(parents=True)
        test_dir.mkdir(parents=True)
        module_file = src_dir / "mod.py"
        test_file = test_dir / "test_mod.py"
        module_file.write_text("x = 1\n", encoding="utf-8")
        test_file.write_text("def test_x():\n    assert True\n", encoding="utf-8")

        result = u.Infra.iter_python_files(
            workspace_root=tmp_path,
            project_roots=[project],
            include_examples=False,
            include_scripts=False,
        )

        tm.ok(result)
        tm.that(result.value, has=module_file)
        tm.that(result.value, has=test_file)

    def test_iter_python_files_returns_failure_on_oserror(self, tmp_path: Path) -> None:
        broken_root = tmp_path / "not-a-directory"
        broken_root.write_text("x", encoding="utf-8")
        result = u.Infra.iter_python_files(workspace_root=broken_root)

        tm.fail(result)
        error_text = result.error or ""
        tm.that(error_text, has="python file iteration failed")

    def test_iter_python_files_excludes_nested_virtualenv_trees(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path
        (project / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        (project / "pkg" / "container" / "venv" / "lib" / "site-packages").mkdir(
            parents=True
        )
        (project / c.Infra.MAKEFILE_FILENAME).write_text("all:\n", encoding="utf-8")
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\n", encoding="utf-8"
        )
        legit_file = project / c.Infra.DEFAULT_SRC_DIR / "mod.py"
        nested_venv_file = (
            project
            / "pkg"
            / "container"
            / "venv"
            / "lib"
            / "site-packages"
            / "ignored.py"
        )
        legit_file.write_text("x = 1\n", encoding="utf-8")
        nested_venv_file.write_text("x = 2\n", encoding="utf-8")

        result = u.Infra.iter_python_files(
            workspace_root=tmp_path, project_roots=[project]
        )

        tm.ok(result)
        tm.that(result.value, has=legit_file)
        tm.that(result.value, lacks=nested_venv_file)

    def test_iter_matching_files_uses_git_tracked_scope_when_available(
        self, tmp_path: Path
    ) -> None:
        self._init_git_repo(tmp_path)
        tracked_file = tmp_path / "tracked.py"
        tracked_file.write_text("x = 1\n", encoding="utf-8")
        untracked_file = tmp_path / "untracked.py"
        untracked_file.write_text("x = 2\n", encoding="utf-8")
        add_result = u.Cli.run_raw(["git", "add", "tracked.py"], cwd=tmp_path)
        tm.ok(add_result)
        tm.that(add_result.value.exit_code, eq=0)

        files = u.Infra.iter_matching_files(
            tmp_path, includes=[c.Infra.EXT_PYTHON_GLOB]
        )

        tm.that(files, eq=[tracked_file, untracked_file])

    def test_find_all_pyproject_files_with_project_paths(self, tmp_path: Path) -> None:
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        first_pyproject = first / c.Infra.PYPROJECT_FILENAME
        second_pyproject = second / c.Infra.PYPROJECT_FILENAME
        first_pyproject.write_text("[project]\nname='first'\n", encoding="utf-8")
        second_pyproject.write_text("[project]\nname='second'\n", encoding="utf-8")

        result = u.Infra.find_all_pyproject_files(
            tmp_path, project_paths=[first, second_pyproject]
        )

        tm.ok(result)
        tm.that(result.value, eq=[first_pyproject, second_pyproject])

    def test_find_all_pyproject_files_skips_excluded_dirs(self, tmp_path: Path) -> None:
        included = tmp_path / "project"
        skipped = tmp_path / ".flext-deps"
        included.mkdir()
        skipped.mkdir()
        included_file = included / c.Infra.PYPROJECT_FILENAME
        skipped_file = skipped / c.Infra.PYPROJECT_FILENAME
        included_file.write_text("[project]\nname='ok'\n", encoding="utf-8")
        skipped_file.write_text("[project]\nname='skip'\n", encoding="utf-8")

        result = u.Infra.find_all_pyproject_files(tmp_path)

        tm.ok(result)
        tm.that(result.value, has=included_file)
        tm.that(result.value, lacks=skipped_file)

    def test_find_all_pyproject_files_skips_hidden_agent_worktrees(
        self, tmp_path: Path
    ) -> None:
        """Hidden agent worktrees are not managed workspace projects."""
        included = tmp_path / "project"
        hidden = tmp_path / ".claude" / "worktrees" / "agent" / "project"
        included.mkdir()
        hidden.mkdir(parents=True)
        included_file = included / c.Infra.PYPROJECT_FILENAME
        hidden_file = hidden / c.Infra.PYPROJECT_FILENAME
        included_file.write_text("[project]\nname='ok'\n", encoding="utf-8")
        hidden_file.write_text("[project]\nname='hidden'\n", encoding="utf-8")

        result = u.Infra.find_all_pyproject_files(tmp_path)

        tm.ok(result)
        tm.that(result.value, has=included_file)
        tm.that(result.value, lacks=hidden_file)

    def test_find_all_pyproject_files_includes_external_workspace_siblings(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "flext"
        workspace.mkdir()
        (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='flext'\n", encoding="utf-8"
        )
        external = tmp_path / "gruponos-data"
        (external / "src" / "gruponos_data").mkdir(parents=True)
        external_pyproject = external / c.Infra.PYPROJECT_FILENAME
        external_pyproject.write_text(
            "[project]\nname='gruponos-data'\ndependencies=['flext-core']\n",
            encoding="utf-8",
        )

        result = FlextInfraUtilitiesDiscovery.find_all_pyproject_files(workspace)

        tm.ok(result)
        tm.that(result.value, has=external_pyproject)

    def test_find_all_pyproject_files_returns_empty_for_non_directory_root(
        self, tmp_path: Path
    ) -> None:
        broken_root = tmp_path / "not-a-directory"
        broken_root.write_text("x", encoding="utf-8")
        result = u.Infra.find_all_pyproject_files(broken_root)

        tm.ok(result)
        tm.that(result.value, eq=[])

    def test_discover_projects_returns_project_info(self, tmp_path: Path) -> None:
        project = tmp_path / "alpha"
        (project / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        (project / c.Infra.DIR_TESTS).mkdir(parents=True)
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='alpha'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )

        result = u.Infra.discover_projects(tmp_path)

        tm.ok(result)
        tm.that(len(result.value), eq=1)
        info = result.value[0]
        tm.that(info, is_=m.Infra.ProjectInfo)
        tm.that(info.name, eq="alpha")
        tm.that(info.has_src, eq=True)
        tm.that(info.has_tests, eq=True)
        tm.that(info.workspace_role, eq=c.Infra.WorkspaceProjectRole.ATTACHED)

    def test_discover_projects_includes_workspace_members_without_core_dep(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\n\n[tool.uv.workspace]\nmembers = ['alpha']\n",
            encoding="utf-8",
        )
        project = tmp_path / "alpha"
        (project / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='alpha'\n", encoding="utf-8"
        )

        result = u.Infra.discover_projects(tmp_path)

        tm.ok(result)
        tm.that(len(result.value), eq=1)
        assert (
            result.value[0].workspace_role
            == c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER
        )

    def test_discover_projects_accepts_project_root_as_workspace(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / c.Infra.DEFAULT_SRC_DIR / "demo_pkg").mkdir(parents=True)
        (tmp_path / c.Infra.DEFAULT_SRC_DIR / "demo_pkg" / c.Infra.INIT_PY).write_text(
            "", encoding="utf-8"
        )
        (tmp_path / c.Infra.DIR_TESTS).mkdir()
        (tmp_path / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='demo-project'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )

        result = u.Infra.discover_projects(tmp_path)

        tm.ok(result)
        tm.that(len(result.value), eq=1)
        tm.that(result.value[0].path, eq=tmp_path)
        tm.that(result.value[0].name, eq="demo-project")
        tm.that(result.value[0].has_src, eq=True)
        tm.that(result.value[0].has_tests, eq=True)

    def test_discover_projects_returns_failure_on_oserror(self, tmp_path: Path) -> None:
        broken_root = tmp_path / "not-a-directory"
        broken_root.write_text("x", encoding="utf-8")
        result = u.Infra.discover_projects(broken_root)

        tm.fail(result)
        error_text = result.error or ""
        tm.that(error_text, has="invalid workspace root")
