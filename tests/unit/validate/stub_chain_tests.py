"""Public behavior tests for FlextInfraStubSupplyChain."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraStubSupplyChain
from tests import c, m, t, u


class TestStubChain:
    """Declarative public-contract tests for stub-chain validation."""

    @staticmethod
    def make_chain(
        *,
        workspace_root: Path,
        stdout: str = "",
        projects: t.StrSequence | None = None,
        all_projects: bool = False,
    ) -> FlextInfraStubSupplyChain:
        return FlextInfraStubSupplyChain(
            workspace=workspace_root,
            selected_projects=projects,
            all_projects=all_projects,
            runner=u.Tests.DeptryRunner(
                u.Tests.ok_result(
                    u.Tests.stub_run(stdout=stdout),
                ),
            ),
        )

    @staticmethod
    def _stub_output(*lines: str) -> str:
        return "\n".join(lines)

    def test_init_defaults(self, tmp_path: Path) -> None:
        chain = FlextInfraStubSupplyChain(workspace=tmp_path)
        tm.that(chain.runner is None, eq=True)
        tm.that(chain.project_names is None, eq=True)
        tm.that(chain.project_dirs is None, eq=True)

    def test_project_names_and_dirs_are_normalized(self, tmp_path: Path) -> None:
        chain = FlextInfraStubSupplyChain(
            workspace=tmp_path,
            selected_projects=[" alpha, beta ", "gamma delta"],
        )
        tm.that(chain.project_names, eq=["alpha", "beta", "gamma", "delta"])
        tm.that(
            chain.project_dirs,
            eq=[
                tmp_path / "alpha",
                tmp_path / "beta",
                tmp_path / "gamma",
                tmp_path / "delta",
            ],
        )

    def test_project_dirs_are_disabled_for_all_projects(self, tmp_path: Path) -> None:
        chain = FlextInfraStubSupplyChain(
            workspace=tmp_path,
            selected_projects=["alpha"],
            all_projects=True,
        )
        tm.that(chain.project_dirs is None, eq=True)

    @pytest.mark.parametrize(
        ("stub_path", "expected_unresolved"),
        [
            (None, ["requests"]),
            ("typings/requests.pyi", []),
        ],
    )
    def test_analyze_classifies_public_results(
        self,
        tmp_path: Path,
        stub_path: str | None,
        expected_unresolved: t.StrSequence,
    ) -> None:
        project_dir = u.Tests.mk_project(
            tmp_path,
            "project",
            pyproject="[project]\nname = 'project'\n",
            with_src=True,
        )
        if stub_path is not None:
            stub_file = tmp_path / stub_path
            stub_file.parent.mkdir(parents=True, exist_ok=True)
            stub_file.write_text("", encoding="utf-8")
        chain = self.make_chain(
            workspace_root=tmp_path,
            stdout=self._stub_output(
                "note: hint: install stub package `types-requests`",
                "src/project.py:1: error: Cannot find module `requests` [missing-import]",
                "src/project.py:2: error: Cannot find module `flext_core` [missing-import]",
            ),
        )

        result = chain.analyze(project_dir, tmp_path)

        tm.ok(result)
        tm.that(
            result.value,
            eq=m.Infra.StubAnalysisReport(
                project="project",
                mypy_hints=["types-requests"],
                internal_missing=["flext_core"],
                unresolved_missing=list(expected_unresolved),
                total_missing=2,
            ),
        )

    def test_build_report_discovers_only_valid_projects(self, tmp_path: Path) -> None:
        u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / c.Infra.PYPROJECT_FILENAME).write_text(
            "",
            encoding="utf-8",
        )
        (hidden_dir / c.Infra.DEFAULT_SRC_DIR).mkdir()
        u.Tests.mk_project(tmp_path, "project-b", with_src=False)

        result = self.make_chain(workspace_root=tmp_path).build_report(tmp_path)

        tm.ok(result)
        tm.that(result.value.summary, eq="stub chain: 1 projects, 0 issues")
        tm.that(result.value.violations, empty=True)

    def test_build_report_uses_explicit_project_dirs(self, tmp_path: Path) -> None:
        project_a = u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        _project_b = u.Tests.mk_project(tmp_path, "project-b", with_src=True)

        result = self.make_chain(workspace_root=tmp_path).build_report(
            tmp_path,
            project_dirs=[project_a],
        )

        tm.ok(result)
        tm.that(result.value.summary, eq="stub chain: 1 projects, 0 issues")

    def test_build_report_ignores_untracked_git_projects(self, tmp_path: Path) -> None:
        init_result = u.Cli.run_raw(["git", "init"], cwd=tmp_path)
        assert init_result.success
        assert init_result.value.exit_code == 0
        email_result = u.Cli.run_raw(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
        )
        assert email_result.success
        assert email_result.value.exit_code == 0
        name_result = u.Cli.run_raw(
            ["git", "config", "user.name", "Test User"],
            cwd=tmp_path,
        )
        assert name_result.success
        assert name_result.value.exit_code == 0
        tracked_project = u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        _untracked_project = u.Tests.mk_project(
            tmp_path,
            "project-b",
            with_src=True,
        )
        add_result = u.Cli.run_raw(
            ["git", "add", "project-a"],
            cwd=tmp_path,
        )
        assert add_result.success
        assert add_result.value.exit_code == 0

        result = self.make_chain(workspace_root=tmp_path).build_report(tmp_path)

        tm.ok(result)
        tm.that(result.value.summary, eq="stub chain: 1 projects, 0 issues")
        tm.that(tracked_project.exists(), eq=True)

    def test_build_report_fails_for_missing_workspace(self, tmp_path: Path) -> None:
        result = self.make_chain(
            workspace_root=tmp_path,
        ).build_report(tmp_path / "missing")
        tm.fail(result)

    def test_execute_fails_when_report_has_violations(self, tmp_path: Path) -> None:
        u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        chain = self.make_chain(
            workspace_root=tmp_path,
            stdout=self._stub_output(
                "src/project.py:1: error: Cannot find module `requests` [missing-import]",
            ),
            all_projects=True,
        )

        result = chain.execute()

        tm.fail(result)
        tm.that(result.error, has="stub chain: 1 projects, 1 issues")

    def test_execute_passes_for_selected_projects(self, tmp_path: Path) -> None:
        u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        u.Tests.mk_project(tmp_path, "project-b", with_src=True)
        chain = self.make_chain(
            workspace_root=tmp_path,
            projects=["project-a"],
        )

        result = chain.execute()

        tm.ok(result)
        tm.that(result.value, eq=True)


__all__: t.StrSequence = []
