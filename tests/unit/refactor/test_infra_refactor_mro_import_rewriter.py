"""Tests for real workspace rewrites after MRO migration."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import t, u

__all__: t.StrSequence = []


class TestsFlextInfraRefactorInfraRefactorMroImportRewriter:
    """Behavior contract for test_infra_refactor_mro_import_rewriter."""

    def test_migrate_workspace_applies_consumer_rewrites(self, tmp_path: Path) -> None:
        workspace_root, constants_path, consumer_path = (
            u.Tests.build_mro_import_workspace(tmp_path)
        )

        migrations, rewrites, errors = u.Tests.migrate_workspace_mro_imports(
            workspace_root=workspace_root,
            constants_path=constants_path,
            apply=True,
        )

        assert errors == ()
        assert len(migrations) == 1
        assert migrations[0].moved_symbols == ("DEMO_VALUE",)
        assert any(item.file.endswith("consumer.py") for item in rewrites)

        constants_text = constants_path.read_text(encoding="utf-8")
        consumer_text = consumer_path.read_text(encoding="utf-8")

        assert (
            f'class {"DemoConstants"}:\n    {"DEMO_VALUE"} = "{"demo"}"'
        ) in constants_text
        assert f"from demo_pkg.constants import {'DEMO_VALUE'}" not in consumer_text
        assert f"from demo_pkg.constants import {'c'}" in consumer_text
        assert (f"value = {'c'}.{'DEMO_VALUE'}") in consumer_text
        assert constants_path.with_suffix(".py.bak").exists()
        assert consumer_path.with_suffix(".py.bak").exists()

    def test_migrate_workspace_dry_run_preserves_files(self, tmp_path: Path) -> None:
        workspace_root, constants_path, consumer_path = (
            u.Tests.build_mro_import_workspace(tmp_path)
        )
        original_constants = constants_path.read_text(encoding="utf-8")
        original_consumer = consumer_path.read_text(encoding="utf-8")

        migrations, rewrites, errors = u.Tests.migrate_workspace_mro_imports(
            workspace_root=workspace_root,
            constants_path=constants_path,
            apply=False,
        )

        assert errors == ()
        assert len(migrations) == 1
        assert any(item.file.endswith("consumer.py") for item in rewrites)
        assert constants_path.read_text(encoding="utf-8") == original_constants
        assert consumer_path.read_text(encoding="utf-8") == original_consumer

    def test_migrate_workspace_reports_protected_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        workspace_root, constants_path, consumer_path = (
            u.Tests.build_mro_import_workspace(tmp_path)
        )
        u.Tests.patch_mro_import_rewriter_write_failure(monkeypatch)

        migrations, rewrites, errors = u.Tests.migrate_workspace_mro_imports(
            workspace_root=workspace_root,
            constants_path=constants_path,
            apply=True,
        )

        assert migrations == ()
        assert rewrites == ()
        assert errors
        assert (f'{"DEMO_VALUE"} = "{"demo"}"') in constants_path.read_text(
            encoding="utf-8"
        )
        assert (f"value = {'DEMO_VALUE'}") in consumer_path.read_text(encoding="utf-8")
