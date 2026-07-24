"""Tests for real workspace rewrites after MRO migration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t

__all__: t.StrSequence = []


class TestsFlextInfraRefactorInfraRefactorMroImportRewriter:
    """Behavior contract for test_infra_refactor_mro_import_rewriter."""

    def test_migrate_workspace_applies_consumer_rewrites(self, tmp_path: Path) -> None:
        workspace_root, constants_path, consumer_path = (
            u.Tests.build_mro_import_workspace(tmp_path)
        )

        migrations, rewrites, errors = u.Tests.migrate_workspace_mro_imports(
            workspace_root=workspace_root, constants_path=constants_path, apply=True
        )

        tm.that(errors, eq=())
        tm.that(len(migrations), eq=1)
        tm.that(migrations[0].moved_symbols, eq=("DEMO_VALUE",))
        assert any(item.file.endswith("consumer.py") for item in rewrites)

        constants_text = constants_path.read_text(encoding="utf-8")
        consumer_text = consumer_path.read_text(encoding="utf-8")

        tm.that(
            constants_text,
            has=(f'class {"DemoConstants"}:\n    {"DEMO_VALUE"} = "{"demo"}"'),
        )
        tm.that(consumer_text, lacks=f"from demo_pkg.constants import {'DEMO_VALUE'}")
        tm.that(consumer_text, has=f"from demo_pkg.constants import {'c'}")
        tm.that(consumer_text, has=(f"value = {'c'}.{'DEMO_VALUE'}"))
        assert constants_path.with_suffix(".py.bak").exists()
        assert consumer_path.with_suffix(".py.bak").exists()

    def test_migrate_workspace_dry_run_preserves_files(self, tmp_path: Path) -> None:
        workspace_root, constants_path, consumer_path = (
            u.Tests.build_mro_import_workspace(tmp_path)
        )
        original_constants = constants_path.read_text(encoding="utf-8")
        original_consumer = consumer_path.read_text(encoding="utf-8")

        migrations, rewrites, errors = u.Tests.migrate_workspace_mro_imports(
            workspace_root=workspace_root, constants_path=constants_path, apply=False
        )

        tm.that(errors, eq=())
        tm.that(len(migrations), eq=1)
        assert any(item.file.endswith("consumer.py") for item in rewrites)
        tm.that(constants_path.read_text(encoding="utf-8"), eq=original_constants)
        tm.that(consumer_path.read_text(encoding="utf-8"), eq=original_consumer)
