"""Tests for real workspace rewrites after MRO migration."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, t, u


def test_migrate_workspace_applies_consumer_rewrites(tmp_path: Path) -> None:
    workspace_root, constants_path, consumer_path = (
        u.Infra.Tests.build_mro_import_workspace(tmp_path)
    )

    migrations, rewrites, errors = u.Infra.Tests.migrate_workspace_mro_imports(
        workspace_root=workspace_root,
        constants_path=constants_path,
        apply=True,
    )

    assert errors == ()
    assert len(migrations) == 1
    assert migrations[0].moved_symbols == (c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME,)
    assert any(item.file.endswith("consumer.py") for item in rewrites)

    constants_text = constants_path.read_text(encoding="utf-8")
    consumer_text = consumer_path.read_text(encoding="utf-8")

    assert (
        f"class {c.Infra.Tests.Fixtures.Refactor.CONSTANTS_CLASS}:\n"
        f'    {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME} = "{c.Infra.Tests.Fixtures.Refactor.SYMBOL_VALUE}"'
    ) in constants_text
    assert (
        f"from demo_pkg.constants import {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}"
        not in consumer_text
    )
    assert (
        f"from demo_pkg.constants import {c.Infra.Tests.Fixtures.Refactor.FACADE_ALIAS}"
        in consumer_text
    )
    assert (
        f"value = {c.Infra.Tests.Fixtures.Refactor.FACADE_ALIAS}."
        f"{c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}"
    ) in consumer_text
    assert constants_path.with_suffix(".py.bak").exists()
    assert consumer_path.with_suffix(".py.bak").exists()


def test_migrate_workspace_dry_run_preserves_files(tmp_path: Path) -> None:
    workspace_root, constants_path, consumer_path = (
        u.Infra.Tests.build_mro_import_workspace(tmp_path)
    )
    original_constants = constants_path.read_text(encoding="utf-8")
    original_consumer = consumer_path.read_text(encoding="utf-8")

    migrations, rewrites, errors = u.Infra.Tests.migrate_workspace_mro_imports(
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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root, constants_path, consumer_path = (
        u.Infra.Tests.build_mro_import_workspace(tmp_path)
    )
    u.Infra.Tests.patch_mro_import_rewriter_write_failure(monkeypatch)

    migrations, rewrites, errors = u.Infra.Tests.migrate_workspace_mro_imports(
        workspace_root=workspace_root,
        constants_path=constants_path,
        apply=True,
    )

    assert migrations == ()
    assert rewrites == ()
    assert errors
    assert (
        f'{c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME} = "{c.Infra.Tests.Fixtures.Refactor.SYMBOL_VALUE}"'
    ) in constants_path.read_text(encoding="utf-8")
    assert (
        f"value = {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}"
    ) in consumer_path.read_text(encoding="utf-8")


__all__: t.StrSequence = []
