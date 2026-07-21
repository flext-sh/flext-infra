"""Tests for private-fixture isolation in public lazy-init generation.

The generated public root must never re-export private ``_fixtures`` symbols.
Configuration and settings remain direct singleton exports from their canonical
foundation modules.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests import c
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraLazyInitFixtureSettingsCollision:
    """Private fixtures never widen the generated public root."""

    def test_root_excludes_private_fixtures_and_keeps_runtime_singletons(
        self, tmp_path: Path
    ) -> None:
        """The public root keeps direct singletons without private fixture exports."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        fixtures_dir = package_root / "_fixtures"
        fixtures_dir.mkdir()
        (fixtures_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (fixtures_dir / "settings.py").write_text(
            '"""Test fixtures."""\n\n'
            "def settings() -> str:\n"
            '    return "fixture"\n\n'
            "def reset_settings() -> None:\n"
            '    """Keep the non-colliding fixture public."""\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (package_root / "_config.py").write_text(
            "class _FlextSampleConfig:\n"
            '    """Private loader class."""\n\n'
            "config = _FlextSampleConfig()\n"
            '__all__ = ["config"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (package_root / "_settings.py").write_text(
            "class _FlextSampleSettings:\n"
            '    """Private loader class."""\n\n'
            "settings = _FlextSampleSettings()\n"
            '__all__ = ["settings"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        result = u.Tests.run_lazy_init(workspace_root)

        init_content = (package_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(result, eq=0)
        tm.that(init_content, contains='"._config": (')
        tm.that(init_content, contains='"._settings": (')
        # mro-wkii.17 (Codex): the inline root excludes private pytest edges.
        tm.that(init_content, lacks='"._fixtures.settings": (')
        tm.that(init_content, lacks='"reset_settings"')
        # mro-pulj (codex): generated local imports are compact and never use
        # redundant identity aliases.
        tm.that(init_content, contains="from ._config import config")
        tm.that(init_content, contains="from ._settings import settings")
        tm.that(init_content, lacks="config as config")
        tm.that(init_content, lacks="settings as settings")
        tm.that(init_content, lacks="_fixtures.settings")
        tm.that(init_content, lacks="reset_settings as reset_settings")
        tm.that(init_content, lacks="FlextSampleConfig")
        tm.that(init_content, lacks="FlextSampleSettings")
        compile(init_content, "__init__.py", "exec")
