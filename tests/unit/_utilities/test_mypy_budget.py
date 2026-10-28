"""Regression coverage for bounded project Mypy policy and native receipts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import config, gates, m, u
from tests import c


class TestsFlextInfraMypyBudget:
    """Verify policy validation and the public checker execution contract."""

    @staticmethod
    @pytest.mark.parametrize(
        "budget",
        [c.ParserBooleanToken.ZERO, "-1", c.ParserBooleanToken.TRUE, "1.5", "'12'"],
    )
    def test_project_budget_rejects_invalid_values(tmp_path: Path, budget: str) -> None:
        """Malformed project budgets cannot launch an unbounded child."""
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "tooling.yaml").write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            f"        timeout_seconds: {budget}\n",
            encoding="utf-8",
        )
        with pytest.raises((TypeError, ValueError)):
            u.Infra.mypy_resource_limit_for_project(tmp_path)

    @staticmethod
    @pytest.mark.parametrize("field", ["timeout_seconds", "max_timeout_seconds"])
    @pytest.mark.parametrize("value", [0, -1, True, 1.5, "12"])
    def test_policy_requires_positive_integer_seconds(
        field: str,
        value: float | str,
    ) -> None:
        """Both canonical budgets reject coercion and non-positive seconds."""
        policy = config.Infra.tooling.tools.mypy
        payload = policy.model_dump(by_alias=True)
        payload[field] = value
        with pytest.raises(ValueError, match=r"greater than 0|valid integer"):
            type(policy).model_validate(payload)

    @staticmethod
    def test_policy_rejects_default_above_its_ceiling() -> None:
        """The typed SSOT rejects an inconsistent default and ceiling."""
        policy = config.Infra.tooling.tools.mypy
        payload = policy.model_dump(by_alias=True)
        payload["timeout_seconds"] = policy.max_timeout_seconds + 1
        with pytest.raises(ValueError, match="default timeout exceeds"):
            type(policy).model_validate(payload)

    @staticmethod
    def test_project_budget_is_published_with_native_completion(
        real_python_package: Path,
    ) -> None:
        """A real checker run records its project policy and native inventory."""
        project = real_python_package
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + "\n[tool.mypy]\n",
            encoding="utf-8",
        )
        reports = project / ".reports"
        reports.mkdir()
        context = m.Infra.GateContext(repository_root=project, reports_dir=reports)
        budget = config.Infra.tooling.tools.mypy.max_timeout_seconds
        (project / "config").mkdir(exist_ok=True)
        (project / "config" / "tooling.yaml").write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            f"        timeout_seconds: {budget}\n",
            encoding="utf-8",
        )
        source_root = project / config.Infra.source_scan.roots[0]
        source_root.mkdir(exist_ok=True)
        source = source_root / "budgeted.py"
        source.write_text("value: int = 1\n", encoding="utf-8")
        execution = gates.FlextInfraMypyGate(project).check_files(
            [source],
            project,
            context,
        )
        tm.ok(execution.result.passed)
        tm.that(execution.raw_output, has=f"timeout_seconds={budget}")
        tm.that(execution.raw_output, has="Build finished in ")
        tm.that(execution.raw_output, has=str(source))
