"""Python source discovery owned by Git's checkout inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


class TestsFlextInfraUtilitiesProjectDiscovery:
    """Discovery decides candidates from one inventory at the checked root."""

    @staticmethod
    def test_python_discovery_reads_one_git_inventory_under_a_ceiling(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A ceiling-bounded checkout never probes Git below its root."""
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=tmp_path))
        (tmp_path / ".gitignore").write_text("/ignored/\n", encoding="utf-8")
        for name in ("owned", "ignored"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

        discovered = u.Infra.discover_python_dirs(
            tmp_path,
            workspace_excluded_top_dirs=frozenset(),
        )

        tm.that(discovered, eq=["owned"])
