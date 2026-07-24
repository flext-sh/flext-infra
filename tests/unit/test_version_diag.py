"""Tests for version diagnostics."""

from pathlib import Path

from flext_tests import tm

import flext_infra as infra_pkg
from flext_infra import u


def test_version_diag() -> None:
    project_root = Path(__file__).resolve().parents[2]
    metadata_result = u.read_project_metadata(project_root)

    tm.ok(metadata_result)
    tm.that(infra_pkg.__version__, eq=metadata_result.value.project.version)
