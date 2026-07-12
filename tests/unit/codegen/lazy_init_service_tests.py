"""Public service tests for lazy-init execution."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests.constants import c
from tests.utilities import u


# mro-i6nq.10: Service tests validate results and emitted public artifacts only.
class TestsFlextInfraCodegenLazyInitService:
    """Validate real service execution without mocks or internal branching asserts."""

    def test_execute_applies_complete_root_artifact_set(self, tmp_path: Path) -> None:
        """Service execution succeeds only after both root artifacts are written."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        service = u.Tests.create_lazy_init_service(workspace_root)

        result = service.execute()

        tm.that(result.success, eq=True)
        tm.that((package_root / c.Infra.INIT_PY).is_file(), eq=True)
        tm.that((package_root / c.Infra.UNIT_PY).is_file(), eq=True)
        tm.that(len(service.modified_files), eq=2)

    def test_check_mode_is_read_only_and_reports_drift(self, tmp_path: Path) -> None:
        """Validated check mode reports both missing artifacts without writing."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        init_path = package_root / c.Infra.INIT_PY
        original_init = init_path.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.check_only = True

        result = service.execute()

        tm.that(result.success, eq=True)
        tm.that(init_path.read_bytes(), eq=original_init)
        tm.that((package_root / c.Infra.UNIT_PY).exists(), eq=False)
        tm.that(len(service.modified_files), eq=2)


__all__: list[str] = ["TestsFlextInfraCodegenLazyInitService"]
