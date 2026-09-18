"""Public error-reporting tests for workspace gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from tests import c, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestsFlextInfraGateErrorReporting:
    """Verify real gate issue reporting through the public ``check()`` contract."""

    def test_ruff_format_reports_each_unformatted_file_once(
        self, tmp_path: Path
    ) -> None:
        proj_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        unformatted = "value=[1,2,3]\n\n\n\n\nother=(4,5)\n"
        for name in ("one.py", "two.py"):
            (proj_dir / c.Infra.DEFAULT_SRC_DIR / name).write_text(
                unformatted, encoding="utf-8"
            )

        result = u.Tests.run_gate_check(FlextInfraRuffFormatGate, tmp_path, proj_dir)

        tm.that(result.result.passed, eq=False)
        tm.that(
            sorted(issue.file for issue in result.issues),
            eq=[f"{c.Infra.DEFAULT_SRC_DIR}/{name}" for name in ("one.py", "two.py")],
        )

    @pytest.mark.parametrize(
        ("readme", "config_text", "expected"),
        [
            ("# Project\n", '{"broken": [', [f"{c.Infra.RUMDL} exited with code"]),
            ("# Project\n\n[Missing](missing.md)\n", None, ["[MD057]", "missing.md"]),
        ],
    )
    def test_workspace_checker_emits_real_markdown_failure(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        readme: str,
        config_text: str | None,
        expected: t.StrSequence,
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "p1")
        (project_dir / "README.md").write_text(readme, encoding="utf-8")
        if config_text is not None:
            (project_dir / c.Infra.MARKDOWNLINT_CONFIG_FILENAME).write_text(
                config_text, encoding="utf-8"
            )
        u.Tests.initialize_git_repo(project_dir)

        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
            ["p1"], [c.Infra.MARKDOWN], reports_dir=tmp_path / "reports"
        )

        tm.ok(result)
        tm.that(result.value[0].passed, eq=False)
        captured = capsys.readouterr()
        tm.that(f"{captured.out}\n{captured.err}", has=list(expected))


__all__: t.StrSequence = ["TestsFlextInfraGateErrorReporting"]
