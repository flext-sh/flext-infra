"""Real-checker regressions for every project-owned Python target.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

import pytest

from flext_infra import m
from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
from tests import c, tm

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.gates.base_gate import FlextInfraGate


class TestsFlextInfraOwnedPythonCoverage:
    """Native checks include all owned roots without importing entrypoints."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "relative_path", ["infra/probe.py", "automation/probe.py", "entry.py"]
    )
    @pytest.mark.parametrize(
        "gate_class",
        [FlextInfraRuffLintGate, FlextInfraMypyGate, FlextInfraPyreflyGate],
    )
    def test_nonstandard_python_targets_report_real_findings(
        real_python_package: Path,
        relative_path: str,
        gate_class: type[FlextInfraGate],
    ) -> None:
        """A clean conventional root cannot hide a defect in another owned target."""
        project = real_python_package
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + '\n[tool.mypy]\n[tool.pyrefly]\nproject-includes = ["src"]\n',
            encoding="utf-8",
        )
        reports = project / ".reports"
        reports.mkdir()
        source = project / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("value = missing_name\n", encoding="utf-8")

        result = gate_class(project).check(
            project,
            m.Infra.GateContext(repository_root=project, reports_dir=reports),
        )

        tm.fail(result.result.passed)
        tm.that(
            any(issue.file.endswith(relative_path) for issue in result.issues),
            truth=True,
        )
