"""Project-local managed artifacts cannot reintroduce Ruff exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraProjectRuffArtifacts:
    """The real project configuration loader rejects retired Ruff catalogs."""

    @staticmethod
    @pytest.mark.parametrize(
        "pattern", ["src/**", "tests/**", "scripts/**", "examples/**"]
    )
    def test_project_ruff_exemptions_are_rejected(tmp_path: Path, pattern: str) -> None:
        """Every first-party surface retains the same native rule policy."""
        root = tmp_path / "project"
        (root / "config").mkdir(parents=True)
        (root / "config" / "tooling.yaml").write_text(
            "ManagedArtifacts:\n  Ruff:\n    per_file_ignores:\n"
            f"      {pattern}: [ALL]\n",
            encoding="utf-8",
        )
        tm.fail(u.Infra.load_project_managed_artifacts(root), has="Ruff")
