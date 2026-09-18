"""Contract for the gitignored per-clone local config override file.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import FlextInfraConfig

if TYPE_CHECKING:
    import pytest


class TestsFlextInfraConfigLocalOverrides:
    """Prove the local override file merges last through the public surface."""

    @staticmethod
    def _copy_tracked_configs(target: Path) -> None:
        """Seed one config directory with the real tracked fleet config."""
        for tracked in FlextInfraConfig.ssot_config_dir().glob("*.yaml"):
            shutil.copy(tracked, target / tracked.name)

    def test_tracked_configs_keep_fleet_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without a local file the tracked scalar survives untouched."""
        self._copy_tracked_configs(tmp_path)
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            fresh = FlextInfraConfig.fetch_global()
            tm.that(fresh.Infra.codegen.loc_cap.max_lines, eq=1000)
        finally:
            FlextInfraConfig.reset_for_testing()

    def test_local_file_scalar_wins_despite_sorted_glob_position(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The local override wins scalars although its name sorts first.

        ``codegen-overrides.local.yaml`` sorts before the tracked files, so a
        plain glob would let the tracked config clobber it; the loader must
        anchor it last regardless of lexicographic position.
        """
        self._copy_tracked_configs(tmp_path)
        (tmp_path / "codegen-overrides.local.yaml").write_text(
            "Infra:\n  codegen:\n    loc_cap:\n      max_lines: 500\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            fresh = FlextInfraConfig.fetch_global()
            tm.that(fresh.Infra.codegen.loc_cap.max_lines, eq=500)
        finally:
            FlextInfraConfig.reset_for_testing()

    def test_local_file_dict_entries_add_beside_tracked_ones(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dict-typed registry gains the local entry and keeps tracked ones."""
        self._copy_tracked_configs(tmp_path)
        (tmp_path / "codegen-overrides.local.yaml").write_text(
            "Infra:\n"
            "  codegen:\n"
            "    layout:\n"
            "      project_overrides:\n"
            "        example-project:\n"
            "          ignore_globs:\n"
            "            - example\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            fresh = FlextInfraConfig.fetch_global()
            overrides = fresh.Infra.codegen.layout.project_overrides
            tm.that("example-project" in overrides, eq=True)
            tm.that("flext-cli" in overrides, eq=True)
        finally:
            FlextInfraConfig.reset_for_testing()
