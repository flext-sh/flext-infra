"""Public error-reporting tests for workspace gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.__version__ import FlextInfraVersion
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path

from tests import t


class TestsFlextInfraGateErrorReporting:
    """Verify real gate issue reporting through the public ``check()`` contract."""

    @staticmethod
    def test_workspace_report_retains_all_executed_failures(
        tmp_path: Path,
    ) -> None:
        """Test workspace report retains all executed failures."""
        project_dir = u.Tests.mk_project(
            tmp_path, "p1", pyproject='[project]\nname = "p1"\n', with_src=True
        )
        (project_dir / "src" / "p1" / "value.py").write_text(
            "value=[1,2,3]\n",
            encoding="utf-8",
        )
        (project_dir / "README.md").write_text(
            "# Project\n\n[Missing](missing.md)\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)
        gates = [c.Infra.FORMAT, c.Infra.MARKDOWN]
        reports_dir = tmp_path / "reports"

        projects = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                ["p1"],
                gates,
                u.Tests.gate_context(tmp_path, reports_dir),
            ),
        )

        project = projects[0]
        tm.that(tuple(project.gates), eq=tuple(gates))
        tm.ok(all(not item.result.passed for item in project.gates.values()))
        tm.that(
            project.total_findings,
            eq=sum(len(item.issues) for item in project.gates.values()),
        )
        receipt = tm.not_none(project.gates[gates[0]].raw_receipt)
        report_path = receipt.parent.parent / c.Infra.CHECK_REPORT_MARKDOWN_FILENAME
        report = report_path.read_text(
            encoding="utf-8",
        )
        for gate in gates:
            tm.that(report, has=f"- {gate}: FAIL")
        sarif = m.Infra.SarifReport.model_validate_json(
            (receipt.parent.parent / c.Infra.CHECK_REPORT_SARIF_FILENAME).read_bytes(),
        )
        summary = tm.not_none(sarif.properties)
        retained = summary.results[0]
        tm.that(retained.total_findings, eq=project.total_findings)
        for gate in gates:
            original = project.gates[gate]
            published = retained.gates[gate]
            native = tm.not_none(published.raw_receipt)
            tm.that(published.issues, eq=original.issues)
            tm.that(published.outcome, eq=original.outcome)
            tm.that(published.raw_output, eq="")
            tm.that(native.read_text(encoding="utf-8"), eq=original.raw_output)

    @staticmethod
    def test_ruff_format_reports_each_unformatted_file_once(
        tmp_path: Path,
    ) -> None:
        """Test ruff format reports each unformatted file once."""
        proj_dir = u.Tests.mk_project(
            tmp_path, "p1", pyproject='[project]\nname = "p1"\n', with_src=True
        )
        unformatted = "value=[1,2,3]\n\n\n\n\nother=(4,5)\n"
        for name in ("one.py", "two.py"):
            (proj_dir / c.Infra.DEFAULT_SRC_DIR / name).write_text(
                unformatted,
                encoding="utf-8",
            )

        result = u.Tests.run_gate_check(FlextInfraRuffFormatGate, tmp_path, proj_dir)

        tm.fail(result.result.passed)
        tm.that(
            sorted(issue.file for issue in result.issues),
            eq=[f"{c.Infra.DEFAULT_SRC_DIR}/{name}" for name in ("one.py", "two.py")],
        )

    @staticmethod
    @pytest.mark.slow
    def test_workspace_checker_emits_ruff_stderr_without_findings(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A native formatter error retains its blocking diagnostic and receipt."""
        project_dir = u.Tests.mk_project(
            tmp_path,
            "p1",
            pyproject=(
                '[project]\nname = "p1"\n'
                '[tool.ruff]\nline-length = "invalid-line-length"\n'
            ),
            with_src=True,
        )
        (project_dir / "src" / "p1" / "value.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)

        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
            ["p1"],
            [c.Infra.FORMAT],
            u.Tests.gate_context(tmp_path, tmp_path / "reports"),
        )

        tm.ok(result)
        project = result.value[0]
        tm.fail(project.passed)
        execution = project.gates[c.Infra.FORMAT]
        tm.that(tuple(issue.code for issue in execution.issues), eq=("format-exec",))
        tm.that(len(execution.result.errors), eq=1)
        tm.that(execution.result.errors[0], has="invalid-line-length")
        tm.that(execution.raw_output, has="invalid-line-length")
        raw_receipt = tm.not_none(execution.raw_receipt)
        tm.that(
            raw_receipt.read_bytes().decode("utf-8"),
            eq=execution.raw_output,
        )
        captured = capsys.readouterr()
        tm.that(
            f"{captured.out}\n{captured.err}",
            has=[str(execution.raw_receipt), "invalid-line-length"],
        )

    @staticmethod
    @pytest.mark.slow
    def test_workspace_security_error_publishes_verbatim_receipt(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Native source excerpts stay in the receipt while issues remain public."""
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        source_dir = (
            project_dir / c.Infra.DEFAULT_SRC_DIR / project_dir.name.replace("-", "_")
        )
        source_marker = "native_receipt_source_marker"
        (source_dir / "finding.py").write_text(
            f'eval("{source_marker}")\n',
            encoding="utf-8",
        )
        invalid = source_dir / "invalid.py"
        invalid.write_text("def broken(:\n", encoding="utf-8")
        u.Tests.initialize_git_repo(project_dir)
        reports_dir = tmp_path / "reports with spaces"

        projects = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                [project_dir.name],
                [c.Infra.SECURITY],
                u.Tests.gate_context(tmp_path, reports_dir),
            ),
        )

        execution = projects[0].gates[c.Infra.SECURITY]
        tm.fail(execution.result.passed)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.ERROR)
        raw_receipt = tm.not_none(execution.raw_receipt)
        (invocation_directory,) = tuple(reports_dir.iterdir())
        tm.that(
            raw_receipt,
            eq=invocation_directory
            / tmp_path.name
            / project_dir.relative_to(tmp_path)
            / (f"{c.Infra.SECURITY}{config.Infra.tooling.raw_check_receipt_suffix}"),
        )
        receipt = raw_receipt.read_bytes().decode("utf-8")
        tm.that(receipt, eq=execution.raw_output, has=source_marker)
        tm.that(any(issue.code == "B307" for issue in execution.issues), eq=True)
        tm.that(
            any(
                issue.code == c.Infra.ToolOutcome.ERROR
                and issue.file == invalid.relative_to(project_dir).as_posix()
                for issue in execution.issues
            ),
            eq=True,
        )
        report_path = invocation_directory / c.Infra.CHECK_REPORT_MARKDOWN_FILENAME
        report = report_path.read_text(
            encoding="utf-8",
        )
        tm.that(
            report,
            has=raw_receipt.resolve().as_uri(),
            lacks=source_marker,
        )
        captured = capsys.readouterr()
        tm.that(
            f"{captured.out}\n{captured.err}",
            has=str(execution.raw_receipt),
            lacks=source_marker,
        )

    @staticmethod
    @pytest.mark.slow
    def test_workspace_preserves_unowned_receipt_destination(
        tmp_path: Path,
    ) -> None:
        """An unowned historical destination is never overwritten or reused."""
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        source_file = (
            project_dir
            / c.Infra.DEFAULT_SRC_DIR
            / project_dir.name.replace("-", "_")
            / "value.py"
        )
        source_file.write_text(
            "value = 1\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)
        reports_dir = tmp_path / "reports"
        blocked_receipt = (
            reports_dir
            / project_dir.name
            / (f"{c.Infra.SECURITY}{config.Infra.tooling.raw_check_receipt_suffix}")
        )
        blocked_receipt.mkdir(parents=True)

        projects = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                [project_dir.name],
                [c.Infra.SECURITY],
                u.Tests.gate_context(tmp_path, reports_dir),
            ),
        )
        receipt = tm.not_none(projects[0].gates[c.Infra.SECURITY].raw_receipt)
        tm.ok(receipt.is_file())
        tm.that(receipt, ne=blocked_receipt)
        tm.ok(blocked_receipt.is_dir())

    @staticmethod
    @pytest.mark.slow
    def test_workspace_checker_emits_mypy_plugin_traceback(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Mypy's real plugin loader failure survives structured-output parsing."""
        project_dir = u.Tests.mk_project(
            tmp_path,
            "p1",
            pyproject=(
                '[project]\nname = "p1"\n'
                '[tool.mypy]\nplugins = ["broken_plugin.py"]\nshow_traceback = true\n'
            ),
            with_src=True,
        )
        (project_dir / "src" / "p1" / "value.py").write_text(
            "value: int = 1\n",
            encoding="utf-8",
        )
        (project_dir / "broken_plugin.py").write_text(
            "def plugin(version: str) -> None:\n"
            '    raise RuntimeError("broken plugin entry point")\n',
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)

        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
            ["p1"],
            [c.Infra.MYPY],
            u.Tests.gate_context(tmp_path, tmp_path / "reports"),
        )

        tm.ok(result)
        project = result.value[0]
        tm.fail(project.passed)
        execution = project.gates[c.Infra.MYPY]
        tm.that(
            any(issue.code == c.Infra.ToolOutcome.ERROR for issue in execution.issues),
            eq=True,
        )
        captured = capsys.readouterr()
        tm.that(
            f"{captured.out}\n{captured.err}",
            has=[
                "Error calling the plugin(version) entry point",
                "Traceback (most recent call last)",
                "RuntimeError: broken plugin entry point",
            ],
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("readme", "config_text", "expected"),
        [
            ("# Project\n", "[broken\n", [f"{c.Infra.RUMDL} exited with code"]),
            ("# Project\n\n[Missing](missing.md)\n", "", ["[MD057]", "missing.md"]),
        ],
    )
    def test_workspace_checker_emits_real_markdown_failure(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        readme: str,
        config_text: str,
        expected: t.StrSequence,
    ) -> None:
        """Test workspace checker emits real markdown failure."""
        project_dir = u.Tests.mk_project(tmp_path, "p1", markdown_config=config_text)
        (project_dir / "README.md").write_text(readme, encoding="utf-8")
        u.Tests.initialize_git_repo(project_dir)

        result = FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
            ["p1"],
            [c.Infra.MARKDOWN],
            u.Tests.gate_context(tmp_path, tmp_path / "reports"),
        )

        tm.ok(result)
        tm.fail(result.value[0].passed)
        captured = capsys.readouterr()
        tm.that(f"{captured.out}\n{captured.err}", has=list(expected))
        receipt = tm.not_none(result.value[0].gates[c.Infra.MARKDOWN].raw_receipt)
        report = m.Infra.SarifReport.model_validate_json(
            (receipt.parent.parent / c.Infra.CHECK_REPORT_SARIF_FILENAME).read_text(
                encoding="utf-8",
            ),
        )
        tm.that(report.runs[0].information_uri, eq=FlextInfraVersion.__url__)
