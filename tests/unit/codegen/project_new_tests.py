"""Functional tests for ``flext-infra codegen new`` (project scaffold).

The scaffold is proven FUNCTIONALLY through its generated public CLI:

* ``python -m flext_demo ping`` runs as a real subprocess against the freshly
  generated project with the generated ``src`` on ``PYTHONPATH``;
* the shared expected file layout is the ``expected_external.txt`` golden.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.17 / agent: codex): generated public CLI replaces
# the out-of-context Python fixture so the repository remains fully type-checkable.
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.constants import c

if TYPE_CHECKING:
    from tests.typings import t

_FIXTURES = Path(__file__).parents[2] / "fixtures" / "codegen_new"


def _golden(name: str) -> tuple[str, ...]:
    """Read a golden relpath fixture (one relative path per non-empty line)."""
    lines = (_FIXTURES / name).read_text(encoding="utf-8").splitlines()
    return tuple(
        sorted(
            line.strip()
            for line in lines
            if line.strip() and not line.lstrip().startswith("#")
        )
    )


def _relpaths(root: Path) -> tuple[str, ...]:
    """Sorted relative paths of every file under ``root``."""
    return tuple(
        sorted(
            str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
        )
    )


@pytest.fixture
def external_project(tmp_path: Path) -> Path:
    """Materialize the external scaffold and return its root."""
    service = FlextInfraCodegenProjectNew(
        name="flext-demo",
        kind=c.Infra.ProjectKind.EXTERNAL,
        output_root=tmp_path / "flext-demo",
        apply_changes=True,
    )
    outcome = service.execute()
    assert outcome.success
    return outcome.value.root


@pytest.fixture
def internal_project(tmp_path: Path) -> Path:
    """Materialize the internal (monorepo-member) scaffold and return its root."""
    service = FlextInfraCodegenProjectNew(
        name="flext-demo",
        kind=c.Infra.ProjectKind.INTERNAL,
        output_root=tmp_path / "flext-demo",
        apply_changes=True,
    )
    outcome = service.execute()
    assert outcome.success
    return outcome.value.root


def _run_cli(root: Path) -> subprocess.CompletedProcess[str]:
    """Run the generated package CLI through its public module entrypoint."""
    pythonpath = os.pathsep.join(
        part for part in (str(root / "src"), os.environ.get("PYTHONPATH", "")) if part
    )
    env = {**os.environ, "PYTHONPATH": pythonpath}
    return subprocess.run(
        [sys.executable, "-m", "flext_demo", "ping"],
        capture_output=True,
        text=True,
        cwd=root,
        env=env,
        timeout=60,
        check=False,
    )


class TestCodegenNewExternalLayout:
    def test_layout_matches_golden(self, external_project: Path) -> None:
        tm.that(_relpaths(external_project), eq=_golden("expected_external.txt"))


class TestCodegenNewInternalLayout:
    def test_layout_matches_golden(self, internal_project: Path) -> None:
        tm.that(_relpaths(internal_project), eq=_golden("expected_external.txt"))


class TestCodegenNewCliFunctional:
    def test_external_cli_runs_in_subprocess(
        self,
        external_project: Path,
    ) -> None:
        proc = _run_cli(external_project)
        tm.that(proc.returncode, eq=0)
        tm.that(bool(proc.stdout.strip()), eq=True)
        tm.that(proc.stderr.strip(), eq="")

    def test_internal_cli_runs_in_subprocess(
        self,
        internal_project: Path,
    ) -> None:
        proc = _run_cli(internal_project)
        tm.that(proc.returncode, eq=0)
        tm.that(bool(proc.stdout.strip()), eq=True)
        tm.that(proc.stderr.strip(), eq="")


class TestCodegenNewDryRun:
    def test_dry_run_reports_plan_without_writing(self, tmp_path: Path) -> None:
        root = tmp_path / "flext-demo"
        service = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            dry_run=True,
        )
        outcome = service.execute()
        tm.that(outcome.success, eq=True)
        report = outcome.value
        tm.that(len(report.files_created) > 0, eq=True)
        tm.that((report.root / "src" / "flext_demo").exists(), eq=False)


__all__: t.StrSequence = []
