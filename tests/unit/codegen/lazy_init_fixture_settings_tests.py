"""Tests for fixture/singleton ``settings`` collision in lazy-init generation.

A ``_fixtures`` module may expose a pytest fixture named ``settings``, but the
name is owned by the canonical ``_settings`` singleton. The generated root
``__init__.py`` must never re-export the fixture under that name: it collides
(F811) with the singleton re-export and shadows it in the lazy import map.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests.constants import c
from tests.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

_FIXTURE_SETTINGS_MODULE = (
    '"""Test fixtures."""\n\n'
    "from __future__ import annotations\n\n"
    "def settings() -> str:\n"
    '    """Fixture colliding with the canonical settings singleton."""\n'
    '    return "fixture"\n\n'
    "def reset_settings() -> None:\n"
    '    """Sibling fixture that must keep bubbling into the root."""\n'
)


def _write_fixture_settings_package(package_root: Path) -> None:
    fixtures_dir = package_root / "_fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
    (fixtures_dir / "settings.py").write_text(
        _FIXTURE_SETTINGS_MODULE,
        encoding=c.Cli.ENCODING_DEFAULT,
    )


class TestsFlextInfraLazyInitFixtureSettingsCollision:
    """The ``settings`` fixture never bubbles into the root lazy map."""

    def test_fixture_settings_export_is_excluded_from_root_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """The fixture name stays out while sibling fixtures keep flowing."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        _write_fixture_settings_package(package_root)

        result = u.Tests.run_lazy_init(workspace_root)

        unit_content = (package_root / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(result, eq=0)
        tm.that(unit_content, contains='"._fixtures.settings": (')
        tm.that(unit_content, contains='"reset_settings"')
        # NOTE (multi-agent): F811 guard — the fixture `settings` must not
        # appear anywhere in the root manifest (lazy map, TYPE_CHECKING, __all__);
        # the name is reserved for the canonical _settings singleton.
        tm.that(unit_content, lacks='"settings"')
        tm.that(unit_content, lacks="settings as settings")
        compile(unit_content, "__unit__.py", "exec")

    def test_fixture_settings_export_is_excluded_from_root_init(
        self,
        tmp_path: Path,
    ) -> None:
        """The thin root initializer never static-imports the fixture name."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        _write_fixture_settings_package(package_root)

        result = u.Tests.run_lazy_init(workspace_root)

        init_content = (package_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(result, eq=0)
        tm.that(init_content, contains="reset_settings as reset_settings")
        tm.that(init_content, lacks="settings as settings")
        compile(init_content, "__init__.py", "exec")
