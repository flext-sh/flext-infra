"""Public checker acceptance against real tools and native report schemas.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import FlextInfraCli, check, config, gates
from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraTypeGates:
    """The selected project's actual findings determine acceptance."""

    @staticmethod
    def test_omitted_ruff_policy_is_rejected() -> None:
        """A governed Make policy requires an explicit typed Ruff cache."""
        configured = config.Infra.codegen.make
        with u.Tests.raises(ValueError, match="ruff_cache"):
            m.Infra.MakeSpec.model_validate(
                configured.model_dump(
                    exclude={"ruff_cache"},
                    exclude_computed_fields=True,
                ),
            )

    @staticmethod
    @c.Tests.MARK.parametrize(
        "field",
        ["data_home_environment_variable", "user_home_environment_variable"],
    )
    def test_required_cache_environment_fields_do_not_inherit_defaults(
        field: str,
    ) -> None:
        """Testmon keeps its explicitly required YAML environment contract."""
        configured = config.Infra.codegen.make
        policy = configured.testmon_cache
        payload = policy.model_dump(
            exclude={field},
            exclude_computed_fields=True,
        )
        with u.Tests.raises(ValueError, match=field):
            type(policy).model_validate(payload)

    @u.Tests.fixture
    @staticmethod
    def checker_context(
        real_python_package: Path,
    ) -> p.Infra.GateContext:
        """Configure the existing real package for native checker execution.

        Returns:
            The resulting ``m.Infra.GateContext``.

        """
        pyproject = real_python_package / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + '\n[tool.pyrefly]\nproject-includes = ["src"]\n',
            encoding="utf-8",
        )
        reports = real_python_package / ".reports"
        reports.mkdir()
        # The type gates run each checker on the checkout's own managed runtime.
        u.Tests.provision_checkout(real_python_package)
        return m.Infra.GateContext(
            repository_root=real_python_package,
            reports_dir=reports,
        )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize(
        "gate",
        sorted(c.Infra.TYPE_CHECKER_GATES),
    )
    def test_public_literal_file_checker_preserves_native_findings_policy(
        checker_context: p.Infra.GateContext,
        gate: str,
    ) -> None:
        """Native findings survive while acceptance follows the typed SSOT policy."""
        project = checker_context.repository_root
        source_root = project / config.Infra.source_scan.roots[0]
        source_root.mkdir(exist_ok=True)
        selected = source_root / "literal_file.py"
        selected.write_text("value: int = 'incorrect'\n", encoding="utf-8")
        sibling = source_root / "unselected_file.py"
        sibling.write_text("def :\n", encoding="utf-8")
        reports = checker_context.reports_dir / "literal-file"
        code = FlextInfraCli.infra_main([
            "check",
            "run",
            "--repository-root",
            str(project),
            "--file",
            str(selected.relative_to(project)),
            "--gates",
            gate,
            "--reports-dir",
            str(reports),
        ])
        tm.that(code, eq=1)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        findings = tm.ok(
            u.Infra.check_report_findings(project, reports_dir=report_path.parent),
        )
        tm.that(findings, empty=False)
        tm.that(
            any(
                location.uri.endswith(str(selected.relative_to(project)))
                for finding in findings
                for location in finding.locations
            ),
            eq=True,
        )

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize(
        "gate_class",
        [
            gates.FlextInfraGatesPyrefly,
        ],
    )
    def test_real_check_and_repair(
        checker_context: p.Infra.GateContext,
        gate_class: type[gates.FlextInfraGates],
    ) -> None:
        """Test real check and repair."""
        project = checker_context.repository_root
        reports = checker_context.reports_dir
        ctx = m.Infra.GateContext(repository_root=project, reports_dir=reports)
        gate = gate_class(project)
        source = project / "src" / "test_pkg" / "contract.py"
        source.write_text('value: int = "incorrect"\n', encoding="utf-8")
        failed = gate.check(project, ctx)
        tm.that(failed.result.passed, eq=False)
        tm.that(failed.issues, truth=True)
        tm.that(failed.result.errors, truth=True)
        tm.that(
            any(issue.severity.lower() == "error" for issue in failed.issues),
            truth=True,
        )

        source.write_text("value: int = 1\n", encoding="utf-8")
        repaired = gate.check(project, ctx)
        tm.that(repaired.result.passed, truth=True, msg=repaired.raw_output)
        tm.that(repaired.issues, truth=False)

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize(
        ("gate_class", "config_text"),
        [
            (
                gates.FlextInfraGatesPyrefly,
                (
                    '[tool.pyrefly]\nproject-includes = ["src"]\n'
                    '[tool.pyrefly.errors]\nbad-assignment = "warn"\n'
                ),
            ),
        ],
    )
    def test_real_warning_is_red(
        real_python_package: Path,
        gate_class: type[gates.FlextInfraGates],
        config_text: str,
    ) -> None:
        """Test real warning is red."""
        project = real_python_package
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + "\n" + config_text,
            encoding="utf-8",
        )
        (project / "src" / "test_pkg" / "warning.py").write_text(
            'value: int = "incorrect"\n',
            encoding="utf-8",
        )
        reports = project / ".reports"
        reports.mkdir()
        result = gate_class(project).check(
            project,
            m.Infra.GateContext(repository_root=project, reports_dir=reports),
        )
        tm.that(result.result.passed, eq=False)
        tm.that(
            any(issue.severity in {"warn", "warning"} for issue in result.issues),
            truth=True,
        )

    @staticmethod
    @c.Tests.MARK.slow
    def test_failed_pyrefly_cannot_reuse_previous_report(
        checker_context: p.Infra.GateContext,
    ) -> None:
        """Test failed pyrefly cannot reuse previous report."""
        project = checker_context.repository_root
        pyproject = project / c.PYPROJECT_FILENAME
        reports = checker_context.reports_dir
        gate = gates.FlextInfraGatesPyrefly(project)
        first = gate.check(project, checker_context)
        tm.that(first.result.passed, truth=True, msg=first.raw_output)
        native_reports = tuple(reports.glob("*-pyrefly.json"))
        tm.that(len(native_reports) == 1, truth=True)
        tm.that(
            m.Infra.PyreflyReport.model_validate_json(
                native_reports[0].read_text(encoding="utf-8"), strict=True
            ).errors,
            truth=False,
        )
        pyproject.write_text("[tool.pyrefly\n", encoding="utf-8")
        failed = gate.check(project, checker_context)
        tm.that(failed.result.passed, eq=False)
        tm.that(failed.raw_output, truth=True)
        # The gate's declared report path is replaced per run: the passing
        # run's report is removed before the failing run, never reused.
        tm.that(native_reports[0].exists(), truth=False)

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.parametrize(
        "gate_class",
        [
            gates.FlextInfraGatesPyrefly,
        ],
    )
    def test_explicit_files_keep_selected_scope(
        checker_context: p.Infra.GateContext,
        gate_class: type[gates.FlextInfraGates],
    ) -> None:
        """Test explicit files keep selected scope."""
        project = checker_context.repository_root
        package = project / "src" / "test_pkg"
        unselected = package / "unselected.py"
        unselected.write_text('value: int = "incorrect"\n', encoding="utf-8")
        gate = gate_class(project)
        result = gate.check_files([package / "identity.py"], project, checker_context)
        tm.that(result.result.passed, truth=True, msg=result.raw_output)
        tm.that(result.issues, truth=False)

        selected_error = gate.check_files([unselected], project, checker_context)
        tm.that(selected_error.result.passed, eq=False, msg=str(selected_error))
        tm.that(
            any(
                issue.file.endswith(unselected.name) for issue in selected_error.issues
            ),
            truth=True,
        )

        full_project = gate.check(project, checker_context)
        tm.that(full_project.result.passed, eq=False, msg=str(full_project))
        tm.that(
            any(issue.file.endswith(unselected.name) for issue in full_project.issues),
            truth=True,
        )

    @staticmethod
    @c.Tests.MARK.parametrize(
        "gate_class",
        [
            gates.FlextInfraGatesPyrefly,
        ],
    )
    def test_empty_source_is_not_passed(
        tmp_path: Path,
        gate_class: type[gates.FlextInfraGates],
    ) -> None:
        """A checker invoked without inputs never reads as a clean pass."""
        result = gate_class(tmp_path).check(
            tmp_path,
            m.Infra.GateContext(repository_root=tmp_path, reports_dir=tmp_path),
        )
        tm.that(result.result.passed, eq=False)
        # An empty source must never read as a clean pass: the skipped state
        # stays visible in the execution errors for every gate posture.
        tm.that(result.result.errors, truth=True)

    @staticmethod
    @c.Tests.MARK.parametrize(
        "gate_class",
        [gates.FlextInfraGatesPyrefly],
    )
    def test_python_analysis_gates_follow_detected_content(
        tmp_path: Path,
        real_python_package: Path,
        gate_class: type[gates.FlextInfraGates],
    ) -> None:
        """Detected Python content, not a pass receipt, selects the type gates."""
        tm.fail(
            gate_class(tmp_path).selected_for(tmp_path, u.Tests.gate_context(tmp_path))
        )
        tm.that(
            gate_class(real_python_package).selected_for(
                real_python_package, u.Tests.gate_context(real_python_package)
            ),
            eq=True,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("payload", ["", " ", "not JSON", "{}", "[]", "null"])
    @c.Tests.MARK.parametrize(
        "report_model",
        [m.Infra.PyreflyReport],
    )
    def test_invalid_native_report(
        report_model: type[m.Infra.PyreflyReport],
        payload: str,
    ) -> None:
        """Test invalid native report."""
        with u.Tests.raises(c.ValidationError):
            report_model.model_validate_json(payload, strict=True)

    @staticmethod
    def test_pyrefly_empty_native_report() -> None:
        """Test pyrefly empty native report."""
        report = m.Infra.PyreflyReport.model_validate_json('{"errors":[]}', strict=True)
        tm.that(report.errors, truth=False)

    @staticmethod
    def test_checker_does_not_run_type_gates_on_content_only_project(
        real_python_package: Path,
    ) -> None:
        """A project without Python targets gets no type-gate row at all."""
        for module in (real_python_package / "src").rglob("*.py"):
            module.unlink()
        reports = real_python_package / ".reports"

        results = tm.ok(
            check.FlextInfraWorkspaceChecker(
                repository_root=real_python_package.parent,
            ).run_projects(
                [real_python_package.name],
                [gates.FlextInfraGatesPyrefly.gate_id],
                u.Tests.gate_context(real_python_package.parent, reports),
            ),
        )

        tm.that(results[0].gates, empty=True)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_MARKDOWN_FILENAME}")
        markdown = report_path.read_text(
            encoding="utf-8",
        )
        tm.that(markdown, lacks=f"- {gates.FlextInfraGatesPyrefly.gate_id}:")
