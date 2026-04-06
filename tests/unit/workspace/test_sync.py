"""Tests for FlextInfraSyncService workspace synchronization."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraSyncService


class TestSyncService:
    def test_sync_generates_basemk_and_gitignore(self, tmp_path: Path) -> None:
        canonical = tmp_path / "canonical"
        project = tmp_path / "project"
        canonical.mkdir(parents=True)
        project.mkdir(parents=True)
        _ = (canonical / "base.mk").write_text("BASE = 1\n", encoding="utf-8")

        service = FlextInfraSyncService(
            canonical_root=canonical,
            workspace=project,
        )
        result = service.execute()
        tm.ok(result)
        sync_result = result.value

        tm.that(sync_result.files_changed, gte=1)
        tm.that((project / "base.mk").exists(), eq=True)
        tm.that((project / ".gitignore").exists(), eq=True)

    def test_sync_is_idempotent_on_second_run(self, tmp_path: Path) -> None:
        canonical = tmp_path / "canonical"
        project = tmp_path / "project"
        canonical.mkdir(parents=True)
        project.mkdir(parents=True)
        _ = (canonical / "base.mk").write_text("BASE = 1\n", encoding="utf-8")

        service = FlextInfraSyncService(
            canonical_root=canonical,
            workspace=project,
        )
        _ = service.execute()
        second_result = service.execute()
        tm.ok(second_result)
        second = second_result.value

        tm.that(second.files_changed, eq=0)
