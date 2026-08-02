"""Test detector main behavior."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_infra import main, r
from flext_infra.deps.detector_runtime import FlextInfraDependencyDetectorRuntime
from flext_tests import tm
from tests import TestsFlextInfraUtilities as u, m, p, t


class _DepsStub(p.Infra.DepsService, p.Infra.PipCheckDepsService):
    def __init__(self, project: Path) -> None:
        self._project = project
        self.deptry_calls = 0

    @override
    def discover_project_paths(
        self, workspace_root: Path, *, projects_filter: t.StrSequence | None = None
    ) -> p.Result[Sequence[Path]]:
        del workspace_root, projects_filter
        return r[Sequence[Path]].ok([self._project])

    @override
    def run_deptry(
        self, project_path: Path, venv_bin: Path
    ) -> p.Result[t.Pair[Sequence[t.JsonMapping], int]]:
        del project_path, venv_bin
        self.deptry_calls += 1
        return r[t.Pair[Sequence[t.JsonMapping], int]].ok(([], 0))

    @override
    def build_project_report(
        self, project_name: str, deptry_issues: t.SequenceOf[t.JsonMapping]
    ) -> m.Infra.ProjectDependencyReport:
        del deptry_issues
        return m.Infra.ProjectDependencyReport(
            project=project_name,
            deptry=m.Infra.DeptryReport(
                missing=[], unused=[], transitive=[], dev_in_runtime=[], raw_count=0
            ),
        )

    @override
    def run_pip_check(
        self, workspace_root: Path, venv_bin: Path
    ) -> p.Result[tuple[t.StrSequence, int]]:
        del workspace_root, venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], 0))


class _DetectorStub:
    """Minimal stub satisfying p.Infra.DetectorRuntime."""

    def __init__(self, deps: p.Infra.DepsService) -> None:
        self.deps = deps
        self.runner: p.Infra.RunnerService = u.Cli
        self.log = u.fetch_logger(__name__)


class TestsFlextInfraDepsDetectorMain:
    """Test flext infra deps detector main behavior."""

    def test_run_executes_deptry_once(self, tmp_path: Path) -> None:
        """Verify the runtime delegates dependency analysis exactly once."""
        project_path = tmp_path / "proj-a"
        (project_path / "src").mkdir(parents=True)
        deptry_path = tmp_path / ".venv" / "bin" / "deptry"
        deptry_path.parent.mkdir(parents=True)
        deptry_path.write_text("", encoding="utf-8")
        deps = _DepsStub(project_path)

        runtime = FlextInfraDependencyDetectorRuntime(
            detector=_DetectorStub(deps=deps),
            workspace_report_factory=m.Infra.WorkspaceDependencyReport,
            pip_check_factory=m.Infra.PipCheckReport,
        )

        tm.ok(
            runtime.run(
                m.Infra.DetectCommand(workspace=str(tmp_path), no_pip_check=True)
            )
        )
        tm.that(deps.deptry_calls, eq=1)

    def test_main_returns_failure_code_on_run_failure(self) -> None:
        """Verify main returns failure code on run failure."""
        tm.that(
            main([
                "deps",
                "detect",
                "--workspace",
                "/nonexistent/path",
                "--no-pip-check",
            ]),
            eq=1,
        )
