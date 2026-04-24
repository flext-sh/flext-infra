from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService
from tests import m, u


class TestsFlextInfraDepsDetectionDiscover:
    def test_success(self, tmp_path: Path) -> None:
        service = FlextInfraDependencyDetectionService()
        proj = m.Infra.ProjectInfo(
            name="proj",
            path=tmp_path / "proj",
            stack="py",
        )
        proj.path.mkdir()
        (proj.path / "pyproject.toml").write_text("")
        service.selector = u.Infra.Tests.DeptrySelector(
            u.Infra.Tests.ok_result([proj]),
        )
        result = service.discover_project_paths(tmp_path)
        tm.that(result.success, eq=True)
        if result.success:
            tm.that(len(result.value), eq=1)

    def test_failure(self, tmp_path: Path) -> None:
        service = FlextInfraDependencyDetectionService()
        service.selector = u.Infra.Tests.DeptrySelector(
            u.Infra.Tests.fail_result("failed"),
        )
        tm.fail(service.discover_project_paths(tmp_path))

    def test_filters_without_pyproject(
        self,
        tmp_path: Path,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        proj = m.Infra.ProjectInfo(
            name="no-pyproject",
            path=tmp_path / "no-pyproject",
            stack="py",
        )
        proj.path.mkdir()
        service.selector = u.Infra.Tests.DeptrySelector(
            u.Infra.Tests.ok_result([proj]),
        )
        result = service.discover_project_paths(tmp_path)
        tm.that(result.success, eq=True)
        if result.success:
            tm.that(result.value, empty=True)
