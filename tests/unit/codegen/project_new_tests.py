"""Functional tests for ``flext-infra codegen new`` (project scaffold).

The scaffold is proven FUNCTIONALLY — no inline example code and no fake
harness:

* the example consumer program lives as a FIXTURE
  (``tests/fixtures/codegen_new/example_consumer.py``) and is executed as a real
  subprocess against the freshly generated project (isolated interpreter, the
  generated ``src`` on ``PYTHONPATH``), the way a downstream user would actually
  import it;
* the expected file layout is a golden FIXTURE
  (``expected_external.txt`` / ``expected_internal.txt``) compared as data.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.14 / agent: codegen): example code + golden layout
# moved to tests/fixtures/codegen_new (operator live order); test only
# orchestrates the real service and a real subprocess.
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
_CONSUMER = _FIXTURES / "example_consumer.py"


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


def _run_consumer(root: Path) -> subprocess.CompletedProcess[str]:
    """Run the example consumer fixture against ``root/src`` in a subprocess."""
    pythonpath = os.pathsep.join(
        part for part in (str(root / "src"), os.environ.get("PYTHONPATH", "")) if part
    )
    env = {**os.environ, "PYTHONPATH": pythonpath}
    return subprocess.run(
        [sys.executable, str(_CONSUMER)],
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
        tm.that(_relpaths(internal_project), eq=_golden("expected_internal.txt"))


class TestCodegenNewConsumerFunctional:
    def test_external_consumer_runs_in_subprocess(
        self,
        external_project: Path,
    ) -> None:
        proc = _run_consumer(external_project)
        tm.that(proc.returncode, eq=0)
        tm.that(proc.stdout.strip(), eq="OK")

    def test_internal_consumer_runs_in_subprocess(
        self,
        internal_project: Path,
    ) -> None:
        proc = _run_consumer(internal_project)
        tm.that(proc.returncode, eq=0)
        tm.that(proc.stdout.strip(), eq="OK")


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
