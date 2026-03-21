from __future__ import annotations

from flext_tests import u

from flext_infra.deps.detection import dm


class TestFlextInfraDependencyDetectorModels:
    def test_dependency_limits_info_creation(self) -> None:
        info = dm.DependencyLimitsInfo(python_version=None, limits_path="")
        u.Tests.Matchers.that(info.python_version, eq=None)
        u.Tests.Matchers.that(info.limits_path, eq="")

    def test_pip_check_report_creation(self) -> None:
        report = dm.PipCheckReport(ok=True, lines=[])
        u.Tests.Matchers.that(report.ok, eq=True)
        u.Tests.Matchers.that(report.lines, eq=[])

    def test_workspace_dependency_report_creation(self) -> None:
        report = dm.WorkspaceDependencyReport(workspace="test-workspace", projects={})
        u.Tests.Matchers.that(report.workspace, eq="test-workspace")
        u.Tests.Matchers.that(report.projects, eq={})
        u.Tests.Matchers.that(report.pip_check, eq=None)
        u.Tests.Matchers.that(report.dependency_limits, eq=None)
