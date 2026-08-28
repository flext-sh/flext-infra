"""Public behavior tests for FlextInfraStubSupplyChain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestStubChain:
    """Declarative public-contract tests for stub-chain validation."""

    @staticmethod
    def make_chain(
        *, workspace_root: Path, stdout: str = "", projects: t.StrSequence | None = None
    ) -> FlextInfraStubSupplyChain:
        return FlextInfraStubSupplyChain(
            workspace_root=workspace_root,
            selected_projects=projects,
            runner=u.Tests.DeptryRunner(r.ok(u.Tests.stub_run(stdout=stdout))),
        )

    @staticmethod
    def _stub_output(*lines: str) -> str:
        return "\n".join(lines)

    def test_init_defaults(self, tmp_path: Path) -> None:
        chain = FlextInfraStubSupplyChain(workspace_root=tmp_path)
        tm.that(chain.runner is None, eq=True)
        tm.that(chain.project_names is None, eq=True)
        tm.that(chain.project_dirs is None, eq=True)

    def test_project_names_and_dirs_are_normalized(self, tmp_path: Path) -> None:
        chain = FlextInfraStubSupplyChain(
            workspace_root=tmp_path, selected_projects=[" alpha, beta ", "gamma delta"]
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

    def test_analyze_classifies_public_results(self, tmp_path: Path) -> None:
        project_dir = u.Tests.mk_project(
            tmp_path,
            "project",
            pyproject="[project]\nname = 'project'\n",
            with_src=True,
        )
        chain = self.make_chain(
            workspace_root=tmp_path,
            stdout=self._stub_output(
                "note: hint: install stub package `types-definitely-missing-external`",
                "src/project.py:1: error: Cannot find module `definitely_missing_external` [missing-import]",
                "src/project.py:2: error: Cannot find module `flext_core` [missing-import]",
            ),
        )

        result = chain.analyze(project_dir, tmp_path)

        tm.ok(result)
        tm.that(
            result.value,
            eq=m.Infra.StubAnalysisReport(
                project="project",
                mypy_hints=["types-definitely-missing-external"],
                internal_missing=["flext_core"],
                unresolved_missing=["definitely_missing_external"],
                total_missing=2,
            ),
        )

    def test_build_report_uses_only_the_local_project(self, tmp_path: Path) -> None:
        project = u.Tests.mk_project(
            tmp_path,
            "project",
            pyproject="[project]\nname = 'project'\n",
            with_src=True,
        )
        result = self.make_chain(workspace_root=project).build_report(project)

        tm.ok(result)
        tm.that(result.value.summary, eq="typed dependency chain: 1 projects, 0 issues")
        tm.that(result.value.violations, empty=True)

    def test_build_report_uses_explicit_project_dirs(self, tmp_path: Path) -> None:
        project_a = u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        _project_b = u.Tests.mk_project(tmp_path, "project-b", with_src=True)

        result = self.make_chain(workspace_root=tmp_path).build_report(
            tmp_path, project_dirs=[project_a]
        )

        tm.ok(result)
        tm.that(result.value.summary, eq="typed dependency chain: 1 projects, 0 issues")

    def test_build_report_fails_for_missing_workspace(self, tmp_path: Path) -> None:
        result = self.make_chain(workspace_root=tmp_path).build_report(
            tmp_path / "missing"
        )
        tm.fail(result)

    def test_execute_fails_when_report_has_violations(self, tmp_path: Path) -> None:
        project = u.Tests.mk_project(
            tmp_path,
            "project-a",
            pyproject="[project]\nname = 'project-a'\n",
            with_src=True,
        )
        chain = self.make_chain(
            workspace_root=project,
            stdout=self._stub_output(
                "note: hint: install stub package `types-definitely-missing-external`"
            ),
        )

        result = chain.execute()

        tm.fail(result)
        tm.that(result.error, has="typed dependency chain: 1 projects, 1 issues")

    def test_execute_passes_for_selected_projects(self, tmp_path: Path) -> None:
        u.Tests.mk_project(tmp_path, "project-a", with_src=True)
        u.Tests.mk_project(tmp_path, "project-b", with_src=True)
        chain = self.make_chain(workspace_root=tmp_path, projects=["project-a"])

        result = chain.execute()

        tm.ok(result)
        tm.that(result.value, eq=True)


__all__: t.StrSequence = []
