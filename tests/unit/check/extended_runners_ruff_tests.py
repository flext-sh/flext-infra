"""Real gate behavior tests for Ruff and Pyright."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import (
    FlextInfraPyrightGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
    m,
)
from tests import t, u


class TestRealGateRunners:
    """Exercise real gate behavior through public gate APIs."""

    @staticmethod
    def make_ctx(root: Path) -> m.Infra.GateContext:
        return m.Infra.GateContext(
            workspace=root,
            reports_dir=root,
        )

    def test_ruff_lint_reports_real_issue(self, tmp_path: Path) -> None:
        project_dir = u.Infra.Tests.mk_project(tmp_path, "lint-project", with_src=True)
        (project_dir / "src" / "demo.py").write_text(
            "import os\n",
            encoding="utf-8",
        )

        result = FlextInfraRuffLintGate(tmp_path).check(
            project_dir,
            self.make_ctx(tmp_path),
        )

        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), gte=1)

    def test_ruff_lint_honors_public_ruff_args(self, tmp_path: Path) -> None:
        project_dir = u.Infra.Tests.mk_project(tmp_path, "lint-args", with_src=True)
        (project_dir / "src" / "demo.py").write_text(
            'value = "' + ("x" * 120) + '"\n',
            encoding="utf-8",
        )

        result = FlextInfraRuffLintGate(tmp_path).check(
            project_dir,
            m.Infra.GateContext(
                workspace=tmp_path,
                reports_dir=tmp_path,
                ruff_args=("--select", "E501"),
            ),
        )

        tm.that(not result.result.passed, eq=True)
        tm.that([issue.code for issue in result.issues], has=["E501"])

    def test_ruff_format_reports_real_reformat(self, tmp_path: Path) -> None:
        project_dir = u.Infra.Tests.mk_project(
            tmp_path, "format-project", with_src=True
        )
        (project_dir / "src" / "demo.py").write_text(
            "value=[1,2,3]\n",
            encoding="utf-8",
        )

        result = FlextInfraRuffFormatGate(tmp_path).check(
            project_dir,
            self.make_ctx(tmp_path),
        )

        tm.that(not result.result.passed, eq=True)

    def test_pyright_reports_real_type_error(self, tmp_path: Path) -> None:
        project_dir = u.Infra.Tests.mk_project(
            tmp_path, "pyright-project", with_src=True
        )
        (project_dir / "src" / "demo.py").write_text(
            "value: str = 1\n",
            encoding="utf-8",
        )

        result = FlextInfraPyrightGate(tmp_path).check(
            project_dir,
            self.make_ctx(tmp_path),
        )

        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), gte=1)


__all__: t.StrSequence = []
