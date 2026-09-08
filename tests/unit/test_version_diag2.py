"""Tests for version diagnostics (extended)."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

import flext_infra as infra_pkg
from flext_infra import u


def test_version_full_import() -> None:
    project_root = Path(__file__).resolve().parents[2]
    metadata_result = u.Infra.read_project_metadata_result(project_root)

    tm.ok(metadata_result)
    tm.that(infra_pkg.__title__, eq=metadata_result.value.project.name)
