"""Upg-owned requirement bounds written from the resolved lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.deps import FlextInfraCooldownAdmission
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsCooldownAdmission:
    """Only the bounds ``[tool.flext.upg]`` names follow the lock."""

    @staticmethod
    def test_record_bounds_follows_the_lock_once(tmp_path: Path) -> None:
        """Owned floor and pin take the locked version; authored lines stay."""
        u.Tests.initialize_git_repo(tmp_path)
        pyproject = tmp_path / c.PYPROJECT_FILENAME
        pyproject.write_text(
            '[project]\nname = "probe"\nversion = "0"\n'
            'dependencies = ["pikepdf>=10.18.0", "lxml>=6"]\n'
            '[dependency-groups]\ndev = ["types-reportlab==5.1.0.20261104"]\n'
            '[tool.flext.upg]\nfloors = ["pikepdf"]\npins = ["types-reportlab"]\n',
            encoding="utf-8",
        )
        registry = 'source = { registry = "https://pypi.org/simple" }\n'
        (tmp_path / c.Infra.UV_LOCK_FILENAME).write_text(
            "version = 1\n"
            '[[package]]\nname = "probe"\nversion = "0"\n'
            'source = { virtual = "." }\n'
            f'[[package]]\nname = "pikepdf"\nversion = "10.17.0"\n{registry}'
            f'[[package]]\nname = "lxml"\nversion = "6.1.3"\n{registry}'
            '[[package]]\nname = "types-reportlab"\nversion = "5.1.0.20261017"\n'
            f"{registry}",
            encoding="utf-8",
        )
        request = m.Infra.WorkspaceRequest(repository_root=tmp_path)
        tm.ok(FlextInfraCooldownAdmission.record_bounds(request))
        written = pyproject.read_text(encoding="utf-8")
        tm.that(written, has='"pikepdf>=10.17.0"')
        tm.that(written, has='"lxml>=6"')
        tm.that(written, has='"types-reportlab==5.1.0.20261017"')
        tm.ok(FlextInfraCooldownAdmission.record_bounds(request))
        tm.that(pyproject.read_text(encoding="utf-8"), eq=written)
