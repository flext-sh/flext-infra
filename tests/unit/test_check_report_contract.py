"""Public contract of the ``check`` verb: read-only gates and a readable report.

``make check`` renders ``check run`` without ``--apply`` so validation never
rewrites the tree; ``make fix`` keeps ``--apply``. Findings survive the run in
the SARIF report, which validates back into ``m.Infra.SarifReport`` and is read
through ``u.Infra.check_report_findings``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, main
from flext_infra.gates.pyright import FlextInfraPyrightGate
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestsFlextInfraCheckReportContract:
    """Prove the check verb leaves sources intact and its report round-trips."""

    @staticmethod
    def _project(tmp_path: Path) -> Path:
        project = u.Tests.mk_project(
            tmp_path,
            "p1",
            pyproject='[project]\nname = "p1"\nversion = "0.1.0"\n',
            with_src=True,
        )
        # One fixable lint finding (unused import) that only --apply rewrites.
        (project / "src" / "p1" / "module.py").write_text(
            '"""Fixture module."""\n\nimport os\n',
            encoding="utf-8",
        )
        return project

    @staticmethod
    def _sources(project: Path) -> t.StrMapping:
        return {
            str(path.relative_to(project)): path.read_text(encoding="utf-8")
            for path in sorted((project / "src").rglob("*.py"))
        }

    @staticmethod
    def _check_run(
        project: Path,
        reports: Path,
        *mode: str,
        gate: str | None = c.Infra.LINT,
        file: str | None = None,
    ) -> int:
        """Run the same ``check run`` argument vector the generated verbs render.

        Returns:
            The resulting ``int``.

        """
        return main([
            "check",
            "run",
            "--repository-root",
            str(project),
            *(("--gates", gate) if gate is not None else ()),
            "--projects",
            ".",
            "--reports-dir",
            str(reports),
            *(("--file", file) if file is not None else ()),
            *mode,
        ])

    @staticmethod
    def test_sarif_report_validates_its_own_emitted_json() -> None:
        """Test sarif report validates its own emitted json."""
        report = m.Infra.SarifReport.model_validate({
            "runs": (
                m.Infra.SarifRun.model_validate({
                    "tool_name": "flext-infra-check",
                    "information_uri": "https://example.invalid/tool",
                    "rules": (
                        m.Infra.SarifRule.model_validate({
                            "id": "unused-import",
                            "shortDescription": {"text": "Ruff Linter (lint) issue"},
                            "helpUri": "https://example.invalid/rule",
                        }),
                    ),
                    "results": (
                        m.Infra.SarifResult.model_validate({
                            "ruleId": "unused-import",
                            "level": "error",
                            "message": {"text": "`os` imported but unused"},
                            "locations": (
                                m.Infra.SarifLocation.model_validate({
                                    "uri": "src/p1/module.py",
                                    "start_line": 3,
                                    "start_column": 8,
                                    "end_line": 4,
                                    "end_column": 10,
                                }),
                            ),
                            "related_locations": (
                                m.Infra.SarifLocation.model_validate({
                                    "uri": "other-project/src/module.py",
                                    "start_line": 7,
                                    "start_column": 2,
                                    "end_line": 9,
                                    "end_column": 4,
                                }),
                            ),
                        }),
                    ),
                }),
            ),
        })

        emitted = report.model_dump_json()

        tm.that(emitted, has='"$schema":')
        tm.that(m.Infra.SarifReport.model_validate_json(emitted), eq=report)
        finding = report.runs[0].results[0]
        with pytest.raises(m.ValidationError, match="locations"):
            m.Infra.SarifResult.model_validate({
                "rule_id": finding.rule_id,
                "level": finding.level,
                "message": finding.message,
                "locations": list(finding.locations),
            })

    @staticmethod
    def test_public_check_preserves_native_diagnostic_levels_and_failure(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Real Pyright findings produce readable SARIF, not a validation crash."""
        project = u.Tests.mk_project(
            tmp_path,
            "diagnostic-levels",
            pyproject=(
                '[project]\nname = "diagnostic-levels"\nversion = "0.1.0"\n'
                '[tool.pyright]\ntypeCheckingMode = "strict"\n'
                'reportUnusedVariable = "warning"\n'
            ),
            with_src=True,
        )
        source = project / "src" / "diagnostics.py"
        source.write_text(
            "def diagnose() -> None:\n"
            "    unused = 1\n"
            '    value: int = "not an integer"\n'
            "    reveal_type(value)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = u.Cli.sha256_bytes(source.read_bytes())
        reports = tmp_path / "reports"
        native = FlextInfraPyrightGate(repository_root=project).check(
            project,
            m.Infra.GateContext.model_validate({
                "repository_root": project,
                "reports_dir": tmp_path / "native",
            }),
        )

        tm.that(
            TestsFlextInfraCheckReportContract._check_run(
                project,
                reports,
                gate="pyright",
            ),
            eq=1,
        )

        output = capsys.readouterr()
        tm.that(output.out + output.err, has="quality checks failed for")
        tm.that(output.out + output.err, lacks="ValidationError")
        tm.that(output.out + output.err, lacks="SerializationError")
        tm.that(u.Cli.sha256_bytes(source.read_bytes()), eq=before)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        report = m.Infra.SarifReport.model_validate_json(
            report_path.read_text(encoding=c.DEFAULT_ENCODING),
            strict=True,
        )
        summary = tm.not_none(report.properties)
        project_result = summary.results[0]
        execution = project_result.gates["pyright"]
        tm.fail(project_result.passed)
        tm.that(execution.outcome, eq=native.outcome)
        tm.that(execution.issues, eq=native.issues)
        tm.that(
            {issue.severity for issue in execution.issues},
            eq={"error", "warning", "information"},
        )
        findings = tm.ok(
            u.Infra.check_report_findings(project, reports_dir=report_path.parent),
        )
        tm.that(len(findings), eq=execution.finding_count)
        tm.that(project_result.total_findings, eq=len(findings))
        for issue, finding in zip(execution.issues, findings, strict=True):
            tm.that(finding.rule_id, eq=issue.code or "pyright")
            tm.that(finding.message, eq=issue.message)
            tm.that(
                finding.level,
                eq="note" if issue.severity == "information" else issue.severity,
            )
            tm.that(finding.locations[0].uri, eq=issue.file)
            tm.that(finding.locations[0].start_line, eq=issue.line)
            tm.that(finding.locations[0].start_column, eq=issue.column)
            tm.that(finding.related_locations, eq=issue.related_locations)
        tm.that(
            m.Infra.SarifReport.model_validate_json(
                report.model_dump_json(round_trip=True),
                strict=True,
            ),
            eq=report,
        )

    def test_check_without_apply_leaves_sources_and_reports_findings(
        self,
        tmp_path: Path,
    ) -> None:
        """Test check without apply leaves sources and reports findings."""
        project = self._project(tmp_path)
        reports = tmp_path / "reports"
        before = self._sources(project)

        tm.that(self._check_run(project, reports), eq=1)

        tm.that(self._sources(project), eq=before)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        report = m.Infra.SarifReport.model_validate_json(
            report_path.read_text(encoding=c.DEFAULT_ENCODING),
            strict=True,
        )
        summary = tm.not_none(report.properties)
        tm.that(tuple(summary.requested_gates), eq=(c.Infra.LINT,))
        tm.that(summary.selected_files, eq=())
        tm.that(len(summary.targets), eq=1)
        tm.that(summary.targets[0].name, eq=project.name)
        tm.that(summary.targets[0].path, eq=project.resolve())
        tm.that(len(summary.results), eq=1)
        tm.that(summary.results[0].project, eq=project.name)
        tm.that(tuple(summary.results[0].gates), eq=(c.Infra.LINT,))
        tm.that(
            m.Infra.SarifReport.model_validate_json(
                report.model_dump_json(round_trip=True),
                strict=True,
            ),
            eq=report,
        )
        findings = tm.ok(
            u.Infra.check_report_findings(project, reports_dir=report_path.parent),
        )
        tm.that(
            [
                location.uri
                for finding in findings
                for location in finding.locations
                if location.uri.endswith("module.py")
            ],
            empty=False,
        )

    def test_check_with_apply_is_the_mutating_fix_path(self, tmp_path: Path) -> None:
        """Test check with apply is the mutating fix path."""
        project = self._project(tmp_path)
        before = self._sources(project)

        tm.that(self._check_run(project, tmp_path / "reports", "--apply"), eq=0)

        tm.that(self._sources(project), ne=before)

    @staticmethod
    @pytest.mark.parametrize(
        "invalid",
        ["", "../outside.py", "/outside.py", "./file.py", "a/../file.py", "missing.py"],
    )
    def test_file_selection_refuses_before_report_effects(
        tmp_path: Path,
        invalid: str,
    ) -> None:
        """Invalid literal selection cannot execute gates or create reports."""
        project = TestsFlextInfraCheckReportContract._project(tmp_path)
        reports = tmp_path / "reports"
        tm.that(
            TestsFlextInfraCheckReportContract._check_run(
                project,
                reports,
                gate=c.Infra.FORMAT,
                file=invalid,
            ),
            ne=0,
        )
        tm.fail(reports.exists())

    @staticmethod
    @pytest.mark.parametrize("parent_link", [False, True])
    def test_file_selection_refuses_symlink_ambiguity(
        tmp_path: Path,
        *,
        parent_link: bool,
    ) -> None:
        """Even in-repository symlink aliases fail before a scanner can run."""
        project = TestsFlextInfraCheckReportContract._project(tmp_path)
        source_root = project / config.Infra.source_scan.roots[0]
        source_root.mkdir(exist_ok=True)
        actual = source_root / "literal.py"
        actual.write_text('"""Fixture."""\n', encoding="utf-8")
        link = project / "alias"
        link.symlink_to(
            source_root if parent_link else actual,
            target_is_directory=parent_link,
        )
        selection = link / actual.name if parent_link else link
        reports = tmp_path / "reports"
        tm.that(
            TestsFlextInfraCheckReportContract._check_run(
                project,
                reports,
                gate=c.Infra.FORMAT,
                file=str(selection.relative_to(project)),
            ),
            ne=0,
        )
        tm.fail(reports.exists())

    @staticmethod
    @pytest.mark.parametrize("broken", [False, True])
    def test_public_file_check_uses_literal_scope_and_native_verdict(
        tmp_path: Path,
        *,
        broken: bool,
    ) -> None:
        """A real configured formatter checks the selected file, not its sibling."""
        project = TestsFlextInfraCheckReportContract._project(tmp_path)
        source_root = project / config.Infra.source_scan.roots[0]
        source_root.mkdir(exist_ok=True)
        selected = source_root / 'literal " name.py'
        selected.write_text(
            "def :\n" if broken else '"""Fixture."""\n',
            encoding="utf-8",
        )
        sibling = source_root / "unselected.py"
        sibling.write_text("def :\n", encoding="utf-8")
        before = (selected.read_bytes(), sibling.read_bytes())
        reports = tmp_path / "reports"
        code = TestsFlextInfraCheckReportContract._check_run(
            project,
            reports,
            gate=c.Infra.FORMAT,
            file=str(selected.relative_to(project)),
        )
        tm.that(code, eq=1 if broken else 0)
        tm.that((selected.read_bytes(), sibling.read_bytes()), eq=before)

    @staticmethod
    @pytest.mark.parametrize("gate", [None, "unregistered-fixture-gate"])
    def test_missing_or_unknown_file_gate_selection_is_not_acceptance(
        tmp_path: Path,
        gate: str | None,
    ) -> None:
        """Absent or unregistered selection blocks without a project fallback."""
        project = TestsFlextInfraCheckReportContract._project(tmp_path)
        selected = project / "literal.py"
        selected.write_text('"""Fixture."""\n', encoding="utf-8")
        reports = tmp_path / "reports"
        tm.that(
            TestsFlextInfraCheckReportContract._check_run(
                project,
                reports,
                gate=gate,
                file=str(selected.relative_to(project)),
            ),
            ne=0,
        )
        tm.fail(reports.exists())

    def test_file_selection_uses_declared_member_context(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A workspace file uses its member's configuration and report identity."""
        root = u.Tests.mk_project(
            tmp_path,
            "workspace-root",
            pyproject=(
                '[project]\nname = "workspace-root"\nversion = "0.1.0"\n'
                '[tool.ruff.format]\nquote-style = "single"\n'
            ),
            with_src=True,
        )
        member = self._project(root)
        pyproject = member / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + '[tool.ruff.format]\nquote-style = "double"\n',
            encoding="utf-8",
        )
        (root / c.Infra.GITMODULES).write_text(
            f'[submodule "{member.name}"]\n'
            f"\tpath = {member.name}\n"
            "\turl = https://example.invalid/member.git\n",
            encoding="utf-8",
        )
        selected = member / "src" / member.name / "literal.py"
        selected.write_text('"""Fixture."""\n\nvalue = "member"\n', encoding="utf-8")
        before = selected.read_bytes()
        code = self._check_run(
            root,
            tmp_path / "reports",
            gate=c.Infra.FORMAT,
            file=str(selected.relative_to(root)),
        )
        output = capsys.readouterr().out
        tm.that(code, eq=0)
        tm.that(output, has=f"[1/1] {member.name} check")
        tm.that(output, lacks=f"[1/1] {root.name} check")
        tm.that(selected.read_bytes(), eq=before)

    @staticmethod
    @pytest.mark.parametrize(
        "mode",
        [
            ("--apply",),
            ("--ruff-args", "--exit-zero"),
            ("--pyright-args", "."),
            ("--projects", "other"),
        ],
    )
    def test_file_selection_cannot_override_scope(
        tmp_path: Path,
        mode: t.StrSequence,
    ) -> None:
        """Literal-file checks refuse mutation and scope or verdict overrides."""
        project = TestsFlextInfraCheckReportContract._project(tmp_path)
        selected = project / "literal.py"
        selected.write_text("import os\n", encoding="utf-8")
        before = selected.read_bytes()
        reports = tmp_path / "reports"
        tm.that(
            TestsFlextInfraCheckReportContract._check_run(
                project,
                reports,
                *mode,
                file=str(selected.relative_to(project)),
            ),
            ne=0,
        )
        tm.that(selected.read_bytes(), eq=before)
        tm.fail(reports.exists())
