"""Public cleanup tests for superseded lazy-init sidecars."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c
from tests import u


# mro-i6nq.10: Cleanup is proven through the real generator, not private mixins.
class TestsFlextInfraLazyInitCleanup:
    """Validate stale generated sidecars are reported or removed truthfully."""

    @staticmethod
    def _workspace_with_sidecars(tmp_path: Path) -> tuple[Path, Path, tuple[Path, ...]]:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextTestsModels", alias="m"
        )
        stale_paths = (
            package_root / c.Infra.ROOT_EXPORTS_FILENAME,
            package_root / "_exports_lazy.py",
            package_root / "_exports_lazy_part_01.py",
        )
        for path in stale_paths:
            path.write_text(
                f"{c.Infra.AUTOGEN_HEADER}\n", encoding=c.Cli.ENCODING_DEFAULT
            )
        return workspace_root, package_root, stale_paths

    def test_apply_removes_sidecars_and_keeps_manifest(self, tmp_path: Path) -> None:
        """Apply deletes superseded registries after producing the root manifest."""
        workspace_root, package_root, stale_paths = self._workspace_with_sidecars(
            tmp_path
        )

        result = u.Tests.run_lazy_init(workspace_root)

        tm.that(result, eq=0)
        tm.that(all(not path.exists() for path in stale_paths), eq=True)
        tm.that((package_root / c.Infra.UNIT_PY).is_file(), eq=True)

    def test_check_reports_sidecars_without_removing(self, tmp_path: Path) -> None:
        """Check-only records every stale sidecar and preserves all bytes."""
        workspace_root, _package_root, stale_paths = self._workspace_with_sidecars(
            tmp_path
        )
        service = u.Tests.create_lazy_init_service(workspace_root)

        result = service.generate_inits(check_only=True)

        tm.that(result, eq=0)
        tm.that(all(path.exists() for path in stale_paths), eq=True)
        tm.that(
            set(map(str, stale_paths)).issubset(set(service.modified_files)), eq=True
        )


__all__: list[str] = ["TestsFlextInfraLazyInitCleanup"]
