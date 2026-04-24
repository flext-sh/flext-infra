from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraInternalDependencySyncService


class TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge:
    def test_ensure_checkout_cleanup_failure(
        self,
        tmp_path: Path,
    ) -> None:
        dep_path = tmp_path / "dep"
        dep_path.mkdir()
        (dep_path / "file.txt").write_text("content")
        dep_path.chmod(0o500)
        try:
            error = tm.fail(
                FlextInfraInternalDependencySyncService().ensure_checkout(
                    dep_path,
                    "https://github.com/test/repo.git",
                    "main",
                ),
            )
            tm.that(error, contains="cleanup failed")
        finally:
            if dep_path.exists():
                dep_path.chmod(0o700)
