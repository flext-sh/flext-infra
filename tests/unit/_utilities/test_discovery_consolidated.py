from __future__ import annotations

from pathlib import Path

from flext_tests import tm
from tests import c, m, u


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

    def test_discover_project_roots_returns_supplied_repository(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='repository'\n", encoding="utf-8"
        )

        roots = u.Infra.discover_project_roots(tmp_path)

        tm.that(roots, eq=(tmp_path.resolve(),))

    def test_iter_python_files_returns_result_with_paths(self, tmp_path: Path) -> None:
        project = tmp_path / "pkg"
        src_dir = project / c.Infra.DEFAULT_SRC_DIR
        test_dir = project / c.Infra.DIR_TESTS
        script_dir = project / "scripts"
        example_dir = project / "examples"
        src_dir.mkdir(parents=True)
        test_dir.mkdir(parents=True)
        script_dir.mkdir(parents=True)
        example_dir.mkdir(parents=True)
        module_file = src_dir / "mod.py"
        test_file = test_dir / "test_mod.py"
        script_file = script_dir / "sync.py"
        example_file = example_dir / "demo.py"
        module_file.write_text("x = 1\n", encoding="utf-8")
        test_file.write_text("def test_x():\n    assert True\n", encoding="utf-8")
        script_file.write_text("x = 2\n", encoding="utf-8")
        example_file.write_text("x = 3\n", encoding="utf-8")

        result = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(project,))
        )

        tm.ok(result)
        tm.that(result.value, has=module_file)
        tm.that(result.value, has=script_file)
        tm.that(result.value, lacks=test_file)
        tm.that(result.value, lacks=example_file)

    def test_iter_python_files_returns_failure_on_oserror(self, tmp_path: Path) -> None:
        broken_root = tmp_path / "not-a-directory"
        broken_root.write_text("x", encoding="utf-8")
        result = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(broken_root,))
        )

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
            m.Infra.SourceScanRequest(project_roots=(project,))
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
        skipped = tmp_path / ".venv"
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

    def test_find_all_pyproject_files_returns_empty_for_non_directory_root(
        self, tmp_path: Path
    ) -> None:
        broken_root = tmp_path / "not-a-directory"
        broken_root.write_text("x", encoding="utf-8")
        result = u.Infra.find_all_pyproject_files(broken_root)

        tm.ok(result)
        tm.that(result.value, eq=[])

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
